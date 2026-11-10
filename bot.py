"""Entry point: ``python bot.py``."""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from werewolf_bot.cog import WerewolfCog
from werewolf_bot.config import Config

log = logging.getLogger("werewolf")


class WerewolfBot(commands.Bot):
    def __init__(self, config: Config) -> None:
        # Slash commands + buttons need no privileged intent. The prefix is only
        # there because commands.Bot requires one; nothing listens to it.
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=discord.Intents.default(),
        )
        self.config = config

    async def setup_hook(self) -> None:
        await self.add_cog(WerewolfCog(self, self.config))
        if self.config.guild_id:  # instant sync to one server (handy while developing)
            guild = discord.Object(id=self.config.guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:  # global sync can take up to an hour to show up everywhere
            await self.tree.sync()

    async def on_ready(self) -> None:
        log.info("Logged in as %s (id %s)", self.user, getattr(self.user, "id", "?"))


def main() -> None:
    config = Config.from_env()
    WerewolfBot(config).run(config.token)


if __name__ == "__main__":
    main()
