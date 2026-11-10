"""Runs one Werewolf game: announcements, night/day loop, win detection.

The session talks to players only through a *prompter* (see :class:`Prompter`),
which the Discord layer implements with buttons and select menus. That keeps
the whole game flow testable without a Discord connection.
"""

from __future__ import annotations

import asyncio
import logging
import random
from collections import Counter
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Protocol, Sequence

import discord

from .engine import (
    Death,
    Game,
    Role,
    RolesError,
    Winner,
    WitchAction,
    build_roles,
    count_votes,
    leaders,
)
from .i18n import tr

log = logging.getLogger(__name__)

Options = Sequence[tuple[int, str]]  # (player id, display name)

# A game where nobody ever dies (everyone AFK) would loop forever: stop it.
MAX_IDLE_ROUNDS = 3


class Prompter(Protocol):
    """How the session asks players for decisions."""

    async def pick(
        self,
        member: Any,
        *,
        prompt: str,
        options: Options,
        count: int = 1,
        timeout: float,
    ) -> Optional[list[int]]:
        """Ask one player (by DM) to choose ``count`` players. None on timeout."""

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
        """Collect one vote per voter (``voter id -> target id``)."""

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
        """Ask the witch what to do tonight."""


@dataclass
class Timings:
    night: float = 60.0  # per night action (seer, wolves, witch, hunter...)
    discussion: float = 120.0  # talk before the day vote
    vote: float = 60.0  # voting window (day vote and mayor election)


@dataclass
class GameOptions:
    werewolves: Optional[int] = None  # None = automatic (README table)
    seer: bool = True
    witch: bool = True
    cupid: bool = True
    hunter: bool = True
    create_lair: bool = True  # private channel for the werewolves


class GameSession:
    def __init__(
        self,
        *,
        channel: Any,
        members: Mapping[int, Any],
        prompter: Prompter,
        lang: str = "en",
        options: Optional[GameOptions] = None,
        timings: Optional[Timings] = None,
        rng: Optional[random.Random] = None,
    ) -> None:
        self.channel = channel
        self.members = dict(members)
        self.prompter = prompter
        self.lang = lang
        self.options = options or GameOptions()
        self.timings = timings or Timings()
        self.rng = rng or random.Random()
        self.game: Optional[Game] = None
        self.lair: Any = None
        self.winner: Optional[Winner] = None

    # -- small helpers ---------------------------------------------------
    def t(self, key: str, **kwargs: object) -> str:
        return tr(self.lang, key, **kwargs)

    async def _say(self, key: str, **kwargs: object) -> None:
        await self.channel.send(self.t(key, **kwargs))

    async def _dm(self, pid: int, text: str) -> bool:
        try:
            await self.members[pid].send(text)
            return True
        except (discord.Forbidden, discord.HTTPException):
            log.warning("Could not DM player %s", pid)
            return False

    def _role_name(self, role: Role) -> str:
        return self.t(f"role_{role.value}")

    def _name(self, pid: int) -> str:
        assert self.game is not None
        return self.game.players[pid].name

    def _options(self, exclude: Sequence[int] = ()) -> list[tuple[int, str]]:
        assert self.game is not None
        return [(p.id, p.name) for p in self.game.alive() if p.id not in exclude]

    # -- public entry point ----------------------------------------------
    async def run(self) -> Optional[Winner]:
        """Play a whole game. Returns the winner, or None if it never started."""
        try:
            if not await self._start():
                return None
            assert self.game is not None
            idle_rounds = 0
            while True:
                alive_before = len(self.game.alive())
                deaths = await self._night()
                await self._dawn(deaths)
                if self._check_end():
                    break
                await self._ensure_mayor()
                await self._day_vote()
                if self._check_end():
                    break
                idle_rounds = idle_rounds + 1 if len(self.game.alive()) == alive_before else 0
                if idle_rounds >= MAX_IDLE_ROUNDS:
                    await self._say("game_idle", rounds=MAX_IDLE_ROUNDS)
                    break
            await self._finish()
            return self.winner
        finally:
            await self._cleanup()

    # -- setup -------------------------------------------------------------
    async def _start(self) -> bool:
        try:
            roles = build_roles(
                len(self.members),
                werewolves=self.options.werewolves,
                seer=self.options.seer,
                witch=self.options.witch,
                cupid=self.options.cupid,
                hunter=self.options.hunter,
            )
        except RolesError as exc:
            await self._say(f"err_roles_{exc.args[0]}")
            return False

        names = {pid: m.display_name for pid, m in self.members.items()}
        self.game = Game(names, roles, rng=self.rng)
        players = list(self.game.players.values())

        sent = await asyncio.gather(*(self._send_role(p.id) for p in players))
        failed = [p.name for p, ok in zip(players, sent) if not ok]
        if failed:
            await self._say("dm_failed", names=", ".join(failed))
            return False

        await self._create_lair()

        counts = Counter(roles)
        summary = ", ".join(
            f"{n}× {self._role_name(role)}" if n > 1 else self._role_name(role)
            for role, n in counts.items()
        )
        await self._say(
            "game_started",
            count=len(players),
            names=", ".join(p.name for p in players),
            roles=summary,
        )
        return True

    async def _send_role(self, pid: int) -> bool:
        assert self.game is not None
        player = self.game.players[pid]
        text = self.t(
            "role_dm",
            role=self._role_name(player.role),
            desc=self.t(f"desc_{player.role.value}"),
        )
        if player.role is Role.WEREWOLF:
            mates = [
                w.name for w in self.game.with_role(Role.WEREWOLF) if w.id != pid
            ]
            if mates:
                text += "\n" + self.t("role_dm_wolves", names=", ".join(mates))
        return await self._dm(pid, text)

    async def _create_lair(self) -> None:
        guild = getattr(self.channel, "guild", None)
        if not self.options.create_lair or guild is None or self.game is None:
            return
        overwrites: dict[Any, discord.PermissionOverwrite] = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True
            ),
        }
        for wolf in self.game.with_role(Role.WEREWOLF):
            overwrites[self.members[wolf.id]] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True
            )
        try:
            self.lair = await guild.create_text_channel(
                "werewolves-lair",
                overwrites=overwrites,
                category=getattr(self.channel, "category", None),
                reason="Werewolf game",
            )
        except (discord.Forbidden, discord.HTTPException):
            log.info("No permission to create the werewolves' lair")
            await self._say("lair_missing")
            return
        await self.lair.send(self.t("lair_welcome"))

    async def _cleanup(self) -> None:
        if self.lair is not None:
            try:
                await self.lair.delete(reason="Werewolf game over")
            except (discord.Forbidden, discord.HTTPException):
                log.warning("Could not delete the werewolves' lair")
            self.lair = None

    # -- night -------------------------------------------------------------
    async def _night(self) -> list[Death]:
        assert self.game is not None
        g = self.game
        g.night += 1
        await self._say("night_falls", n=g.night)
        _, _, victim = await asyncio.gather(
            self._cupid(), self._seer(), self._wolves()
        )
        action = await self._witch(victim)
        return g.resolve_night(victim, action)

    async def _cupid(self) -> None:
        assert self.game is not None
        g = self.game
        cupids = g.with_role(Role.CUPID)
        if g.night != 1 or not cupids:
            return
        cupid = cupids[0]
        await self._say("cupid_wakes")
        picked = await self.prompter.pick(
            self.members[cupid.id],
            prompt=self.t("prompt_cupid"),
            options=self._options(),
            count=2,
            timeout=self.timings.night,
        )
        alive = set(g.alive_ids())
        if not picked or len(set(picked)) != 2 or not set(picked) <= alive:
            await self._say("cupid_skipped")
            return
        a, b = picked
        g.set_lovers(a, b)
        await self._dm(a, self.t("lovers_dm", name=self._name(b)))
        await self._dm(b, self.t("lovers_dm", name=self._name(a)))

    async def _seer(self) -> None:
        assert self.game is not None
        g = self.game
        seers = g.with_role(Role.SEER)
        if not seers:
            return
        seer = seers[0]
        await self._say("seer_wakes")
        options = self._options(exclude=[seer.id])
        picked = await self.prompter.pick(
            self.members[seer.id],
            prompt=self.t("prompt_seer"),
            options=options,
            count=1,
            timeout=self.timings.night,
        )
        if not picked or picked[0] not in {pid for pid, _ in options}:
            return
        target = picked[0]
        await self._dm(
            seer.id,
            self.t(
                "seer_result",
                name=self._name(target),
                role=self._role_name(g.reveal(target)),
            ),
        )

    async def _wolves(self) -> Optional[int]:
        assert self.game is not None
        g = self.game
        wolves = g.with_role(Role.WEREWOLF)
        options = [(p.id, p.name) for p in g.alive() if p.role is not Role.WEREWOLF]
        if not wolves or not options:
            return None
        await self._say("wolves_wake")
        destinations = (
            [self.lair] if self.lair is not None else [self.members[w.id] for w in wolves]
        )
        votes = await self.prompter.group_vote(
            destinations=destinations,
            voters=[w.id for w in wolves],
            prompt=self.t("prompt_wolves"),
            options=options,
            allow_self=True,
            timeout=self.timings.night,
        )
        valid_targets = {pid for pid, _ in options}
        wolf_ids = {w.id for w in wolves}
        votes = {v: t for v, t in votes.items() if v in wolf_ids and t in valid_targets}
        top = leaders(count_votes(votes))
        if not top:
            return None
        return self.rng.choice(sorted(top))

    async def _witch(self, victim: Optional[int]) -> WitchAction:
        assert self.game is not None
        g = self.game
        witches = g.with_role(Role.WITCH)
        if not witches:
            return WitchAction()
        witch = witches[0]
        can_heal = g.heal_available and victim is not None
        can_poison = g.poison_available
        if not (can_heal or can_poison):
            return WitchAction()

        await self._say("witch_wakes")
        prompt = (
            self.t("prompt_witch_victim", name=self._name(victim))
            if victim is not None
            else self.t("prompt_witch_none")
        )
        options = self._options(exclude=[witch.id])
        action = await self.prompter.witch(
            self.members[witch.id],
            prompt=prompt,
            can_heal=can_heal,
            can_poison=can_poison,
            options=options,
            timeout=self.timings.night,
        )
        # Never trust the UI blindly: drop anything the rules don't allow.
        save = action.save and can_heal
        poison = action.poison
        if poison is not None and (
            not can_poison or poison not in {pid for pid, _ in options}
        ):
            poison = None
        if save and poison is not None and g.witch_one_potion_per_night:
            poison = None
        return WitchAction(save=save, poison=poison)

    # -- day ---------------------------------------------------------------
    async def _dawn(self, deaths: list[Death]) -> None:
        await self._say("day_breaks")
        if not deaths:
            await self._say("no_deaths")
            return
        await self._say("deaths_header")
        await self._process_deaths(deaths)

    async def _process_deaths(self, deaths: list[Death]) -> None:
        """Announce deaths; a dead hunter gets to shoot, which can chain."""
        queue = list(deaths)
        while queue:
            death = queue.pop(0)
            await self._say(
                "death_line", name=death.name, role=self._role_name(death.role)
            )
            if death.role is Role.HUNTER:
                queue.extend(await self._hunter_shot(death))

    async def _hunter_shot(self, hunter: Death) -> list[Death]:
        assert self.game is not None
        g = self.game
        options = self._options()
        if not options:
            return []
        picked = await self.prompter.pick(
            self.members[hunter.player_id],
            prompt=self.t("prompt_hunter"),
            options=options,
            count=1,
            timeout=self.timings.night,
        )
        if not picked or picked[0] not in {pid for pid, _ in options}:
            await self._say("hunter_no_shot", hunter=hunter.name)
            return []
        target = picked[0]
        await self._say("hunter_shoots", hunter=hunter.name, target=self._name(target))
        return g.kill(target, "hunter")

    async def _ensure_mayor(self) -> None:
        assert self.game is not None
        g = self.game
        if g.mayor is not None or len(g.alive()) < 2:
            return
        seconds = int(self.timings.vote)
        await self._say("mayor_died" if g.mayor_died else "mayor_election", seconds=seconds)
        options = self._options()
        votes = await self.prompter.group_vote(
            destinations=[self.channel],
            voters=g.alive_ids(),
            prompt=self.t("prompt_mayor"),
            options=options,
            allow_self=True,
            timeout=self.timings.vote,
        )
        valid = {pid for pid, _ in options}
        votes = {v: t for v, t in votes.items() if v in valid and t in valid}
        top = leaders(count_votes(votes))
        if top:
            mayor = self.rng.choice(sorted(top))
        else:
            mayor = self.rng.choice(sorted(valid))
            await self._say("mayor_random", name=self._name(mayor))
        g.mayor = mayor
        g.mayor_died = False
        await self._say("mayor_elected", name=self._name(mayor))

    async def _day_vote(self) -> None:
        assert self.game is not None
        g = self.game
        await self._say("discussion", seconds=int(self.timings.discussion))
        await asyncio.sleep(self.timings.discussion)
        await self._say("vote_open", seconds=int(self.timings.vote))
        votes = await self.prompter.group_vote(
            destinations=[self.channel],
            voters=g.alive_ids(),
            prompt=self.t("prompt_lynch"),
            options=self._options(),
            allow_self=False,
            timeout=self.timings.vote,
        )
        votes = {
            v: t
            for v, t in votes.items()
            if v in g.players and t in g.players and v != t
        }
        counts = g.lynch_counts(votes)
        top = leaders(counts)
        if not top:
            await self._say("no_votes")
            return
        results = ", ".join(
            f"{self._name(pid)}: {n}"
            for pid, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        )
        await self._say("vote_result", results=results)

        target = await self._break_tie(top)
        if target is None:
            return
        await self._say("lynched", name=self._name(target))
        await self._process_deaths(g.kill(target, "vote"))

    async def _break_tie(self, top: list[int]) -> Optional[int]:
        assert self.game is not None
        g = self.game
        if len(top) == 1:
            return top[0]
        if g.mayor is None:
            await self._say("tie_nobody")
            return None
        picked = await self.prompter.pick(
            self.members[g.mayor],
            prompt=self.t("prompt_tiebreak"),
            options=[(pid, self._name(pid)) for pid in top],
            count=1,
            timeout=self.timings.vote,
        )
        if picked and picked[0] in top:
            return picked[0]
        await self._say("tie_random")
        return self.rng.choice(sorted(top))

    # -- end ---------------------------------------------------------------
    def _check_end(self) -> bool:
        assert self.game is not None
        self.winner = self.game.check_winner()
        return self.winner is not None

    async def _finish(self) -> None:
        assert self.game is not None
        if self.winner is not None:
            await self._say(f"winner_{self.winner.value}")
        roles = ", ".join(
            f"{p.name} ({self._role_name(p.role)})"
            for p in self.game.players.values()
        )
        await self._say("final_roles", roles=roles)
