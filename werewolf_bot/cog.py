"""Slash commands: /werewolf start | stop | rules."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Mapping, Optional

import discord
from discord import app_commands
from discord.ext import commands

from .config import Config
from .engine import RolesError, build_roles
from .i18n import tr
from .session import GameOptions, GameSession
from .ui import DiscordPrompter, LobbyView

log = logging.getLogger(__name__)


@dataclass
class ActiveGame:
    host_id: int
    task: Optional["asyncio.Task[None]"] = None


def interaction_language(interaction: discord.Interaction, default: str) -> str:
    """Use French for French-speaking users, otherwise the configured default."""
    return "fr" if str(interaction.locale).startswith("fr") else default


class WerewolfCog(commands.GroupCog, group_name="werewolf", group_description="Play Werewolf"):
    def __init__(self, bot: commands.Bot, config: Config) -> None:
        super().__init__()
        self.bot = bot
        self.config = config
        self.games: dict[int, ActiveGame] = {}  # one game per server

    async def cog_unload(self) -> None:
        for game in self.games.values():
            if game.task:
                game.task.cancel()

    # -- /werewolf start -------------------------------------------------------
    @app_commands.command(name="start", description="Open a lobby for a new Werewolf game")
    @app_commands.guild_only()
    @app_commands.describe(
        werewolves="Number of werewolves (default: automatic from player count)",
        seer="Include the seer",
        witch="Include the witch",
        cupid="Include cupid",
        hunter="Include the hunter",
        language="Language of the game",
    )
    @app_commands.choices(
        language=[
            app_commands.Choice(name="English", value="en"),
            app_commands.Choice(name="Français", value="fr"),
        ]
    )
    async def start(
        self,
        interaction: discord.Interaction,
        werewolves: Optional[app_commands.Range[int, 1, 5]] = None,
        seer: bool = True,
        witch: bool = True,
        cupid: bool = True,
        hunter: bool = True,
        language: Optional[app_commands.Choice[str]] = None,
    ) -> None:
        lang = language.value if language else self.config.default_language
        guild_id = interaction.guild_id
        if guild_id is None or interaction.channel is None:
            await interaction.response.send_message(tr(lang, "err_guild_only"), ephemeral=True)
            return
        if guild_id in self.games:
            await interaction.response.send_message(tr(lang, "err_active"), ephemeral=True)
            return
        if not interaction.app_permissions.send_messages:
            await interaction.response.send_message(tr(lang, "err_channel"), ephemeral=True)
            return

        options = GameOptions(
            werewolves=werewolves,
            seer=seer,
            witch=witch,
            cupid=cupid,
            hunter=hunter,
            create_lair=self.config.create_lair,
        )
        # Reject impossible role setups now, not after everyone has joined.
        try:
            build_roles(
                self.config.max_players,
                werewolves=options.werewolves,
                seer=seer, witch=witch, cupid=cupid, hunter=hunter,
            )
        except RolesError as exc:
            await interaction.response.send_message(
                tr(lang, f"err_roles_{exc.args[0]}"), ephemeral=True
            )
            return

        def render(members: Mapping[int, Any]) -> str:
            return self._render_lobby(lang, interaction.user.display_name, options, members)

        lobby = LobbyView(
            interaction.user,
            lang=lang,
            render=render,
            min_players=self.config.min_players,
            max_players=self.config.max_players,
        )
        entry = ActiveGame(host_id=interaction.user.id)
        self.games[guild_id] = entry
        await interaction.response.send_message(render(lobby.members), view=lobby)
        lobby.message = await interaction.original_response()
        entry.task = asyncio.create_task(
            self._play(guild_id, interaction.channel, lobby, entry, lang, options)
        )

    def _render_lobby(
        self, lang: str, host: str, options: GameOptions, members: Mapping[int, Any]
    ) -> str:
        wolves = (
            tr(lang, "lobby_wolves_auto", n="2–3")
            if options.werewolves is None
            else tr(lang, "lobby_wolves", n=options.werewolves)
        )
        specials = [
            tr(lang, f"role_{name}")
            for name, enabled in (
                ("seer", options.seer), ("witch", options.witch),
                ("cupid", options.cupid), ("hunter", options.hunter),
            )
            if enabled
        ]
        return tr(
            lang,
            "lobby",
            host=host,
            roles=", ".join([wolves, *specials]),
            count=len(members),
            max=self.config.max_players,
            min=self.config.min_players,
            players=", ".join(m.display_name for m in members.values()) or tr(lang, "lobby_none"),
        )

    async def _play(
        self,
        guild_id: int,
        channel: Any,
        lobby: LobbyView,
        entry: ActiveGame,
        lang: str,
        options: GameOptions,
    ) -> None:
        try:
            await lobby.wait()
            if not lobby.started:
                return
            session = GameSession(
                channel=channel,
                members=lobby.members,
                prompter=DiscordPrompter(lang),
                lang=lang,
                options=options,
                timings=self.config.timings,
            )
            await session.run()
        except asyncio.CancelledError:
            lobby.stop()
            await self._notify(channel, tr(lang, "game_stopped"))
        except Exception:
            log.exception("Werewolf game crashed in guild %s", guild_id)
            await self._notify(channel, tr(lang, "game_error"))
        finally:
            if self.games.get(guild_id) is entry:
                del self.games[guild_id]

    @staticmethod
    async def _notify(channel: Any, text: str) -> None:
        try:
            await channel.send(text)
        except discord.HTTPException:
            pass

    # -- /werewolf stop --------------------------------------------------------
    @app_commands.command(name="stop", description="Stop the game of this server")
    @app_commands.guild_only()
    async def stop(self, interaction: discord.Interaction) -> None:
        lang = interaction_language(interaction, self.config.default_language)
        entry = self.games.get(interaction.guild_id or 0)
        if entry is None:
            await interaction.response.send_message(tr(lang, "err_none"), ephemeral=True)
            return
        member = interaction.user
        is_admin = isinstance(member, discord.Member) and member.guild_permissions.manage_guild
        if member.id != entry.host_id and not is_admin:
            await interaction.response.send_message(tr(lang, "err_not_allowed"), ephemeral=True)
            return
        if entry.task:
            entry.task.cancel()
        await interaction.response.send_message(tr(lang, "stopped"), ephemeral=True)

    # -- /werewolf rules -------------------------------------------------------
    @app_commands.command(name="rules", description="Explain the rules")
    async def rules(self, interaction: discord.Interaction) -> None:
        lang = interaction_language(interaction, self.config.default_language)
        await interaction.response.send_message(tr(lang, "rules"), ephemeral=True)
