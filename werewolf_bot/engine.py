"""Pure game rules for Werewolf.

Nothing in this module knows about Discord, so every rule can be unit tested.
The Discord layer (``session.py`` / ``ui.py``) only asks players for decisions
and feeds them into a :class:`Game`.
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional

MIN_PLAYERS = 8
MAX_PLAYERS = 18


class Role(str, Enum):
    WEREWOLF = "werewolf"
    VILLAGER = "villager"
    SEER = "seer"
    WITCH = "witch"
    HUNTER = "hunter"
    CUPID = "cupid"


class Winner(str, Enum):
    VILLAGE = "village"
    WEREWOLVES = "werewolves"
    LOVERS = "lovers"
    NOBODY = "nobody"


class RolesError(ValueError):
    """Raised for an impossible role setup. ``args[0]`` is a stable code."""


@dataclass
class Player:
    id: int
    name: str
    role: Role = Role.VILLAGER
    alive: bool = True
    lover: Optional[int] = None


@dataclass(frozen=True)
class Death:
    player_id: int
    name: str
    role: Role
    cause: str  # "werewolves" | "poison" | "vote" | "hunter" | "love"


@dataclass(frozen=True)
class WitchAction:
    save: bool = False
    poison: Optional[int] = None


def default_werewolf_count(num_players: int) -> int:
    """Werewolf count from the README table: 2 for 8-11 players, 3 for 12-18."""
    return 2 if num_players <= 11 else 3


def build_roles(
    num_players: int,
    *,
    werewolves: Optional[int] = None,
    seer: bool = True,
    witch: bool = True,
    cupid: bool = True,
    hunter: bool = True,
) -> list[Role]:
    """Return one role per player (unshuffled). Villagers fill the remainder."""
    wolves = default_werewolf_count(num_players) if werewolves is None else werewolves
    special = [
        role
        for role, enabled in (
            (Role.SEER, seer),
            (Role.WITCH, witch),
            (Role.CUPID, cupid),
            (Role.HUNTER, hunter),
        )
        if enabled
    ]
    if wolves < 1:
        raise RolesError("too_few_wolves")
    if wolves * 2 >= num_players:
        raise RolesError("too_many_wolves")
    if wolves + len(special) > num_players:
        raise RolesError("too_many_special")
    villagers = num_players - wolves - len(special)
    return [Role.WEREWOLF] * wolves + special + [Role.VILLAGER] * villagers


def count_votes(
    votes: Mapping[int, int], weights: Optional[Mapping[int, int]] = None
) -> dict[int, int]:
    """Tally ``voter -> target`` votes; ``weights`` lets a voter count more."""
    counts: Counter[int] = Counter()
    for voter, target in votes.items():
        counts[target] += (weights or {}).get(voter, 1)
    return dict(counts)


def leaders(counts: Mapping[int, int]) -> list[int]:
    """All targets sharing the top count (empty when nobody got a vote)."""
    if not counts:
        return []
    top = max(counts.values())
    return [target for target, n in counts.items() if n == top]


class Game:
    def __init__(
        self,
        players: Mapping[int, str],
        roles: list[Role],
        *,
        rng: Optional[random.Random] = None,
        witch_one_potion_per_night: bool = True,
    ) -> None:
        if len(players) != len(roles):
            raise ValueError("need exactly one role per player")
        self.rng = rng or random.Random()
        self.witch_one_potion_per_night = witch_one_potion_per_night
        shuffled = list(roles)
        self.rng.shuffle(shuffled)
        self.players: dict[int, Player] = {
            pid: Player(pid, name, role)
            for (pid, name), role in zip(players.items(), shuffled)
        }
        self.mayor: Optional[int] = None
        self.mayor_died = False
        self.heal_available = True
        self.poison_available = True
        self.night = 0

    # -- lookups ---------------------------------------------------------
    def alive(self) -> list[Player]:
        return [p for p in self.players.values() if p.alive]

    def alive_ids(self) -> list[int]:
        return [p.id for p in self.alive()]

    def with_role(self, role: Role, *, alive_only: bool = True) -> list[Player]:
        return [
            p
            for p in self.players.values()
            if p.role is role and (p.alive or not alive_only)
        ]

    # -- actions ---------------------------------------------------------
    def set_lovers(self, a: int, b: int) -> None:
        if a == b:
            raise ValueError("lovers must be two different players")
        self.players[a].lover = b
        self.players[b].lover = a

    def reveal(self, pid: int) -> Role:
        return self.players[pid].role

    def kill(self, pid: int, cause: str) -> list[Death]:
        """Kill a player; a lover dies of grief right after. Returns all deaths."""
        player = self.players[pid]
        if not player.alive:
            return []
        player.alive = False
        if self.mayor == pid:
            self.mayor = None
            self.mayor_died = True
        deaths = [Death(player.id, player.name, player.role, cause)]
        if player.lover is not None:
            deaths += self.kill(player.lover, "love")
        return deaths

    def resolve_night(
        self, victim: Optional[int], action: WitchAction = WitchAction()
    ) -> list[Death]:
        """Apply the werewolves' victim and the witch's potions."""
        if action.save:
            if victim is None or not self.heal_available:
                raise ValueError("the healing potion cannot be used now")
            if action.poison is not None and self.witch_one_potion_per_night:
                raise ValueError("only one potion per night")
        if action.poison is not None:
            if not self.poison_available:
                raise ValueError("the poison potion is already used")
            if not self.players[action.poison].alive:
                raise ValueError("cannot poison a dead player")

        deaths: list[Death] = []
        if action.save:
            self.heal_available = False
        elif victim is not None:
            deaths += self.kill(victim, "werewolves")
        if action.poison is not None:
            self.poison_available = False
            deaths += self.kill(action.poison, "poison")
        return deaths

    # -- voting ----------------------------------------------------------
    def vote_weight(self, voter: int) -> int:
        """The mayor's vote counts double."""
        return 2 if voter == self.mayor else 1

    def lynch_counts(self, votes: Mapping[int, int]) -> dict[int, int]:
        """Tally day votes, ignoring dead voters and dead targets."""
        valid = {
            voter: target
            for voter, target in votes.items()
            if self.players[voter].alive and self.players[target].alive
        }
        weights = {voter: self.vote_weight(voter) for voter in valid}
        return count_votes(valid, weights)

    # -- end of game -----------------------------------------------------
    def check_winner(self) -> Optional[Winner]:
        alive = self.alive()
        if not alive:
            return Winner.NOBODY
        wolves = [p for p in alive if p.role is Role.WEREWOLF]
        others = [p for p in alive if p.role is not Role.WEREWOLF]
        if len(alive) == 2:
            a, b = alive
            mixed = (a.role is Role.WEREWOLF) != (b.role is Role.WEREWOLF)
            if a.lover == b.id and mixed:
                return Winner.LOVERS
        if not wolves:
            return Winner.VILLAGE
        if not others:
            return Winner.WEREWOLVES
        return None
