"""Discord UI: the buttons and select menus used to collect decisions.

Everything here is built on discord.py 2.x components, so the bot needs no
privileged intent (players answer by clicking, not by typing).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Mapping, Optional, Sequence

import discord

from .engine import WitchAction
from .i18n import tr

log = logging.getLogger(__name__)

Options = Sequence[tuple[int, str]]
GRACE = 5.0  # views outlive the question a little, then get cleaned up


async def _safe_send(destination: Any, content: str, view: discord.ui.View):
    try:
        return await destination.send(content, view=view)
    except (discord.Forbidden, discord.HTTPException):
        log.warning("Could not send a prompt to %r", destination)
        return None


async def _safe_clear(message: Any) -> None:
    """Remove the components of a finished prompt."""
    try:
        await message.edit(view=None)
    except discord.HTTPException:
        pass


class _Collector:
    """Shared answers for one question asked to one or more players."""

    def __init__(self, voters: Sequence[int]) -> None:
        self.voters = set(voters)
        self.choices: dict[int, list[int]] = {}
        self.done = asyncio.Event()

    def record(self, voter: int, chosen: list[int]) -> None:
        self.choices[voter] = chosen  # voters may change their mind
        if self.voters <= self.choices.keys():
            self.done.set()


class _SelectView(discord.ui.View):
    def __init__(
        self,
        collector: _Collector,
        options: Options,
        *,
        lang: str,
        count: int,
        allow_self: bool,
        timeout: float,
    ) -> None:
        super().__init__(timeout=timeout + GRACE)
        self.collector = collector
        self.lang = lang
        self.allow_self = allow_self
        self.names = dict(options)
        self.select = discord.ui.Select(
            placeholder=tr(lang, "ui_placeholder_two" if count == 2 else "ui_placeholder_one"),
            min_values=count,
            max_values=count,
            options=[
                discord.SelectOption(label=name[:100], value=str(pid))
                for pid, name in options
            ],
        )
        self.select.callback = self._on_select
        self.add_item(self.select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id in self.collector.voters:
            return True
        await interaction.response.send_message(
            tr(self.lang, "ui_not_allowed"), ephemeral=True
        )
        return False

    async def _on_select(self, interaction: discord.Interaction) -> None:
        chosen = [int(value) for value in self.select.values]
        if not self.allow_self and interaction.user.id in chosen:
            await interaction.response.send_message(
                tr(self.lang, "ui_no_self"), ephemeral=True
            )
            return
        self.collector.record(interaction.user.id, chosen)
        names = ", ".join(self.names[pid] for pid in chosen)
        await interaction.response.send_message(
            tr(self.lang, "ui_registered", names=names), ephemeral=True
        )


class _WitchView(discord.ui.View):
    def __init__(
        self,
        witch_id: int,
        options: Options,
        *,
        lang: str,
        can_heal: bool,
        can_poison: bool,
        timeout: float,
    ) -> None:
        super().__init__(timeout=timeout + GRACE)
        self.witch_id = witch_id
        self.lang = lang
        self.options = options
        self.action: Optional[WitchAction] = None
        self.done = asyncio.Event()

        heal = discord.ui.Button(
            label=tr(lang, "ui_heal"), style=discord.ButtonStyle.success, disabled=not can_heal
        )
        poison = discord.ui.Button(
            label=tr(lang, "ui_poison"), style=discord.ButtonStyle.danger, disabled=not can_poison
        )
        skip = discord.ui.Button(
            label=tr(lang, "ui_pass"), style=discord.ButtonStyle.secondary
        )
        heal.callback = self._heal
        poison.callback = self._poison
        skip.callback = self._skip
        for button in (heal, poison, skip):
            self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.witch_id:
            return True
        await interaction.response.send_message(
            tr(self.lang, "ui_not_allowed"), ephemeral=True
        )
        return False

    async def _finish(self, interaction: discord.Interaction, action: WitchAction) -> None:
        self.action = action
        await interaction.response.edit_message(
            content=tr(self.lang, "ui_witch_done"), view=None
        )
        self.done.set()

    async def _heal(self, interaction: discord.Interaction) -> None:
        await self._finish(interaction, WitchAction(save=True))

    async def _skip(self, interaction: discord.Interaction) -> None:
        await self._finish(interaction, WitchAction())

    async def _poison(self, interaction: discord.Interaction) -> None:
        select = discord.ui.Select(
            placeholder=tr(self.lang, "ui_placeholder_one"),
            options=[
                discord.SelectOption(label=name[:100], value=str(pid))
                for pid, name in self.options
            ],
        )

        async def chosen(select_interaction: discord.Interaction) -> None:
            await self._finish(
                select_interaction, WitchAction(poison=int(select.values[0]))
            )

        select.callback = chosen
        self.clear_items()
        self.add_item(select)
        await interaction.response.edit_message(
            content=tr(self.lang, "prompt_witch_poison"), view=self
        )


class DiscordPrompter:
    """Implements ``session.Prompter`` with Discord components."""

    def __init__(self, lang: str = "en") -> None:
        self.lang = lang

    async def _ask(
        self,
        destinations: Sequence[Any],
        content: str,
        voters: Sequence[int],
        options: Options,
        *,
        count: int,
        allow_self: bool,
        timeout: float,
    ) -> dict[int, list[int]]:
        collector = _Collector(voters)
        sent: list[tuple[Any, discord.ui.View]] = []
        try:
            for destination in destinations:
                view = _SelectView(
                    collector,
                    options,
                    lang=self.lang,
                    count=count,
                    allow_self=allow_self,
                    timeout=timeout,
                )
                message = await _safe_send(destination, content, view)
                if message is not None:
                    sent.append((message, view))
            if sent:
                try:
                    await asyncio.wait_for(collector.done.wait(), timeout)
                except asyncio.TimeoutError:
                    pass
        finally:
            for message, view in sent:
                view.stop()
                await _safe_clear(message)
        return dict(collector.choices)

    async def pick(
        self,
        member: Any,
        *,
        prompt: str,
        options: Options,
        count: int = 1,
        timeout: float,
    ) -> Optional[list[int]]:
        choices = await self._ask(
            [member], prompt, [member.id], options,
            count=count, allow_self=True, timeout=timeout,
        )
        return choices.get(member.id)

    async def group_vote(
        self,
        *,
        destinations: Sequence[Any],
        voters: Sequence[int],
        prompt: str,
        options: Options,
        allow_self: bool,
        timeout: float,
    ) -> dict[int, int]:
        choices = await self._ask(
            destinations, prompt, voters, options,
            count=1, allow_self=allow_self, timeout=timeout,
        )
        return {voter: chosen[0] for voter, chosen in choices.items()}

    async def witch(
        self,
        member: Any,
        *,
        prompt: str,
        can_heal: bool,
        can_poison: bool,
        options: Options,
        timeout: float,
    ) -> WitchAction:
        view = _WitchView(
            member.id, options,
            lang=self.lang, can_heal=can_heal, can_poison=can_poison, timeout=timeout,
        )
        message = await _safe_send(member, prompt, view)
        if message is None:
            return WitchAction()
        try:
            await asyncio.wait_for(view.done.wait(), timeout)
        except asyncio.TimeoutError:
            pass
        finally:
            view.stop()
            await _safe_clear(message)
        return view.action or WitchAction()


class LobbyView(discord.ui.View):
    """Join / Leave / Begin / Cancel buttons for a game that is being set up."""

    def __init__(
        self,
        host: discord.abc.User,
        *,
        lang: str,
        render: Callable[[Mapping[int, Any]], str],
        min_players: int,
        max_players: int,
        timeout: float = 900.0,
    ) -> None:
        super().__init__(timeout=timeout)
        self.host = host
        self.lang = lang
        self.render = render
        self.min_players = min_players
        self.max_players = max_players
        self.members: dict[int, Any] = {host.id: host}
        self.started = False
        self.message: Optional[discord.Message] = None

        for key, style, callback in (
            ("ui_join", discord.ButtonStyle.success, self._join),
            ("ui_leave", discord.ButtonStyle.secondary, self._leave),
            ("ui_begin", discord.ButtonStyle.primary, self._begin),
            ("ui_cancel", discord.ButtonStyle.danger, self._cancel),
        ):
            button = discord.ui.Button(label=tr(lang, key), style=style)
            button.callback = callback
            self.add_item(button)

    def _t(self, key: str, **kwargs: object) -> str:
        return tr(self.lang, key, **kwargs)

    async def _refresh(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(content=self.render(self.members))

    async def _join(self, interaction: discord.Interaction) -> None:
        user = interaction.user
        if user.id in self.members:
            await interaction.response.send_message(self._t("ui_already_in"), ephemeral=True)
        elif len(self.members) >= self.max_players:
            await interaction.response.send_message(self._t("ui_full"), ephemeral=True)
        else:
            self.members[user.id] = user
            await self._refresh(interaction)

    async def _leave(self, interaction: discord.Interaction) -> None:
        user = interaction.user
        if user.id == self.host.id:
            await interaction.response.send_message(self._t("ui_host_cannot_leave"), ephemeral=True)
        elif user.id not in self.members:
            await interaction.response.send_message(self._t("ui_not_in"), ephemeral=True)
        else:
            del self.members[user.id]
            await self._refresh(interaction)

    async def _begin(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.host.id:
            await interaction.response.send_message(self._t("ui_host_only"), ephemeral=True)
        elif len(self.members) < self.min_players:
            await interaction.response.send_message(
                self._t("lobby_min", min=self.min_players), ephemeral=True
            )
        else:
            self.started = True
            await interaction.response.edit_message(
                content=self.render(self.members), view=None
            )
            self.stop()

    async def _cancel(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.host.id:
            await interaction.response.send_message(self._t("ui_host_only"), ephemeral=True)
            return
        await interaction.response.edit_message(
            content=self._t("lobby_cancelled"), view=None
        )
        self.stop()

    async def on_timeout(self) -> None:
        if self.message is not None and not self.started:
            try:
                await self.message.edit(content=self._t("lobby_expired"), view=None)
            except discord.HTTPException:
                pass
