"""Drive GameSession with scripted / random players (no Discord needed)."""

import asyncio
import random

import discord
import pytest

from werewolf_bot.engine import Role, Winner, WitchAction
from werewolf_bot.i18n import tr
from werewolf_bot.session import (
    MAX_IDLE_ROUNDS,
    GameOptions,
    GameSession,
    Timings,
)

W, V, S, WI, H, C = (
    Role.WEREWOLF,
    Role.VILLAGER,
    Role.SEER,
    Role.WITCH,
    Role.HUNTER,
    Role.CUPID,
)
# Player ids are 1..8: P1,P2 wolves; P3 seer; P4 witch; P5 cupid; P6 hunter; P7,P8 villagers
ROLES8 = [W, W, S, WI, C, H, V, V]


def en(key, **kw):
    return tr("en", key, **kw)


# -- fakes -------------------------------------------------------------------
class FakeMember:
    def __init__(self, pid, fail_dm=False):
        self.id = pid
        self.display_name = f"P{pid}"
        self.fail_dm = fail_dm
        self.sent = []

    async def send(self, text, **kwargs):
        if self.fail_dm:
            raise discord.Forbidden()
        self.sent.append(text)


class FakeChannel:
    guild = None
    category = None

    def __init__(self):
        self.sent = []
        self.deleted = False

    async def send(self, text, **kwargs):
        self.sent.append(text)

    async def delete(self, **kwargs):
        self.deleted = True

    def said(self, text):
        return any(text in m for m in self.sent)


class FakeGuild:
    default_role = object()
    me = object()

    def __init__(self, fail=False):
        self.fail = fail
        self.lair = FakeChannel()
        self.created_with = None

    async def create_text_channel(self, name, **kwargs):
        if self.fail:
            raise discord.Forbidden()
        self.created_with = kwargs
        return self.lair


class FakePrompter:
    """Scripted decisions; override any policy through keyword arguments."""

    def __init__(self, **policies):
        self.session = None
        self.votes = []  # (kind, destinations)
        self.policy = {
            "cupid": lambda opts: [opts[0][0], opts[1][0]],
            "seer": lambda opts: [opts[0][0]],
            "hunter": lambda opts: [opts[0][0]],
            "tiebreak": lambda opts: [opts[0][0]],
            "wolves": lambda voter, opts: opts[0][0],
            "mayor": lambda voter, opts: opts[0][0],
            "lynch": lambda voter, opts: opts[0][0],
            "witch": lambda **kw: WitchAction(),
        }
        self.policy.update(policies)

    async def pick(self, member, *, prompt, options, count=1, timeout):
        kind = {
            en("prompt_cupid"): "cupid",
            en("prompt_seer"): "seer",
            en("prompt_hunter"): "hunter",
            en("prompt_tiebreak"): "tiebreak",
        }[prompt]
        return self.policy[kind](options)

    async def group_vote(
        self, *, destinations, voters, prompt, options, allow_self, timeout
    ):
        kind = {
            en("prompt_wolves"): "wolves",
            en("prompt_mayor"): "mayor",
            en("prompt_lynch"): "lynch",
        }[prompt]
        self.votes.append((kind, list(destinations)))
        out = {}
        for voter in voters:
            opts = [o for o in options if allow_self or o[0] != voter]
            choice = self.policy[kind](voter, opts)
            if choice is not None:
                out[voter] = choice
        return out

    async def witch(self, member, *, prompt, can_heal, can_poison, options, timeout):
        return self.policy["witch"](
            prompt=prompt, can_heal=can_heal, can_poison=can_poison, options=options
        )


def make_session(n=8, prompter=None, members=None, channel=None, seed=3, **kwargs):
    members = members or {i: FakeMember(i) for i in range(1, n + 1)}
    channel = channel or FakeChannel()
    prompter = prompter or FakePrompter()
    session = GameSession(
        channel=channel,
        members=members,
        prompter=prompter,
        timings=Timings(0, 0, 0),
        rng=random.Random(seed),
        **kwargs,
    )
    prompter.session = session
    return session, channel, prompter, members


async def started(roles=None, **kwargs):
    session, channel, prompter, members = make_session(**kwargs)
    assert await session._start()
    if roles:
        for pid, role in zip(session.game.players, roles):
            session.game.players[pid].role = role
    return session, channel, prompter, members


def run(coro):
    return asyncio.run(asyncio.wait_for(coro, 10))


# -- setup -------------------------------------------------------------------
def test_everyone_gets_a_role_dm_and_wolves_know_each_other():
    async def go():
        session, channel, _, members = await started()
        for member in members.values():
            assert any("**" in m for m in member.sent)
        wolves = session.game.with_role(W)
        assert len(wolves) == 2
        for wolf in wolves:
            other = next(w for w in wolves if w.id != wolf.id)
            dms = " ".join(members[wolf.id].sent)
            assert other.name in dms
        assert channel.said("8")

    run(go())


def test_game_cancelled_when_a_dm_fails():
    async def go():
        members = {i: FakeMember(i, fail_dm=(i == 4)) for i in range(1, 9)}
        session, channel, _, _ = make_session(members=members)
        assert await session.run() is None
        assert channel.said("P4")
        assert not channel.said(en("night_falls", n=1))

    run(go())


def test_impossible_role_setup_is_reported():
    async def go():
        session, channel, _, _ = make_session(
            options=GameOptions(werewolves=5)
        )
        assert await session.run() is None
        assert channel.said(en("err_roles_too_many_wolves"))

    run(go())


# -- night -------------------------------------------------------------------
def test_cupid_binds_lovers_seer_peeks_witch_saves():
    async def go():
        prompter = FakePrompter(
            cupid=lambda opts: [7, 8],
            seer=lambda opts: [1],
            wolves=lambda voter, opts: 7,
            witch=lambda **kw: WitchAction(save=kw["can_heal"]),
        )
        session, channel, _, members = await started(ROLES8, prompter=prompter)
        deaths = await session._night()
        g = session.game
        assert deaths == []
        assert not g.heal_available and g.players[7].alive
        assert g.players[7].lover == 8 and g.players[8].lover == 7
        assert any("P8" in m for m in members[7].sent)
        assert any(en("role_werewolf") in m for m in members[3].sent)
        assert channel.said(en("night_falls", n=1))

    run(go())


def test_wolves_kill_and_lover_follows():
    async def go():
        prompter = FakePrompter(
            cupid=lambda opts: [7, 8], wolves=lambda voter, opts: 7
        )
        session, channel, _, _ = await started(ROLES8, prompter=prompter)
        deaths = await session._night()
        await session._dawn(deaths)
        assert {d.player_id for d in deaths} == {7, 8}
        assert channel.said(en("death_line", name="P7", role=en("role_villager")))
        assert channel.said(en("death_line", name="P8", role=en("role_villager")))

    run(go())


def test_wolf_votes_majority_wins():
    async def go():
        # Wolf 1 votes P7, wolf 2 votes P8; tie broken by the seeded rng.
        prompter = FakePrompter(wolves=lambda voter, opts: 7 if voter == 1 else 8)
        session, _, _, _ = await started(ROLES8, prompter=prompter)
        victim = await session._wolves()
        assert victim in (7, 8)

    run(go())


def test_witch_poison_kills_and_potion_is_spent():
    async def go():
        prompter = FakePrompter(
            wolves=lambda voter, opts: 7,
            witch=lambda **kw: WitchAction(poison=8),
        )
        session, _, _, _ = await started(ROLES8, prompter=prompter)
        deaths = await session._night()
        assert {d.player_id for d in deaths} == {7, 8}
        assert not session.game.poison_available

    run(go())


def test_invalid_witch_answers_are_ignored():
    async def go():
        # Tries to save AND poison herself with potions that are unavailable.
        prompter = FakePrompter(
            wolves=lambda voter, opts: 7,
            witch=lambda **kw: WitchAction(save=True, poison=4),
        )
        session, _, _, _ = await started(ROLES8, prompter=prompter)
        action = await session._witch(7)
        assert action == WitchAction(save=True)  # poison dropped: one potion/night
        session.game.heal_available = False
        action = await session._witch(7)
        assert action == WitchAction(poison=None)  # P4 (witch) is not a valid target

    run(go())


def test_witch_is_skipped_without_potions():
    async def go():
        calls = []
        prompter = FakePrompter(witch=lambda **kw: calls.append(kw) or WitchAction())
        session, channel, _, _ = await started(ROLES8, prompter=prompter)
        session.game.heal_available = False
        session.game.poison_available = False
        assert await session._witch(7) == WitchAction()
        assert calls == [] and not channel.said(en("witch_wakes"))

    run(go())


def test_cupid_timeout_means_no_lovers():
    async def go():
        prompter = FakePrompter(cupid=lambda opts: None)
        session, channel, _, _ = await started(ROLES8, prompter=prompter)
        await session._night()
        assert all(p.lover is None for p in session.game.players.values())
        assert channel.said(en("cupid_skipped"))

    run(go())


# -- day ---------------------------------------------------------------------
def test_hunter_shoots_when_killed_and_chain_continues():
    async def go():
        prompter = FakePrompter(
            wolves=lambda voter, opts: 6,  # kill the hunter
            hunter=lambda opts: [1],  # hunter shoots wolf P1
        )
        session, channel, _, _ = await started(ROLES8, prompter=prompter)
        await session._dawn(await session._night())
        g = session.game
        assert not g.players[6].alive and not g.players[1].alive
        assert channel.said(en("hunter_shoots", hunter="P6", target="P1"))

    run(go())


def test_hunter_killing_a_lover_triggers_grief_death():
    async def go():
        prompter = FakePrompter(
            cupid=lambda opts: [1, 2],
            wolves=lambda voter, opts: 6,
            hunter=lambda opts: [1],  # shoots P1, whose lover is P2
        )
        session, _, _, _ = await started(ROLES8, prompter=prompter)
        await session._dawn(await session._night())
        g = session.game
        assert not g.players[1].alive and not g.players[2].alive

    run(go())


def test_hunter_timeout_means_no_shot():
    async def go():
        prompter = FakePrompter(wolves=lambda voter, opts: 6, hunter=lambda opts: None)
        session, channel, _, _ = await started(ROLES8, prompter=prompter)
        await session._dawn(await session._night())
        assert session.game.players[1].alive
        assert channel.said(en("hunter_no_shot", hunter="P6"))

    run(go())


def test_mayor_election_picks_the_most_voted_player():
    async def go():
        prompter = FakePrompter(mayor=lambda voter, opts: 3)
        session, channel, _, _ = await started(ROLES8, prompter=prompter)
        await session._ensure_mayor()
        assert session.game.mayor == 3
        assert channel.said(en("mayor_elected", name="P3"))
        # The mayor's own vote then counts double in the day vote.
        counts = session.game.lynch_counts({3: 7, 1: 8, 2: 8, 4: 7})
        assert counts == {7: 3, 8: 2}

    run(go())


def test_mayor_election_without_votes_is_random():
    async def go():
        prompter = FakePrompter(mayor=lambda voter, opts: None)
        session, channel, _, _ = await started(ROLES8, prompter=prompter)
        await session._ensure_mayor()
        assert session.game.mayor is not None

    run(go())


def test_dead_mayor_is_replaced():
    async def go():
        prompter = FakePrompter(mayor=lambda voter, opts: 5)
        session, channel, _, _ = await started(ROLES8, prompter=prompter)
        session.game.mayor = 3
        session.game.kill(3, "vote")
        await session._ensure_mayor()
        assert session.game.mayor == 5
        assert channel.said(en("mayor_died", seconds=0))

    run(go())


def test_day_vote_lynches_most_voted_player():
    async def go():
        prompter = FakePrompter(lynch=lambda voter, opts: 7 if voter != 7 else 8)
        session, channel, _, _ = await started(ROLES8, prompter=prompter)
        session.game.mayor = 5
        await session._day_vote()
        assert not session.game.players[7].alive
        assert channel.said(en("lynched", name="P7"))

    run(go())


def test_nobody_cannot_vote_for_themselves():
    async def go():
        # Policy tries to vote for self; the fake enforces allow_self=False.
        seen = []

        def policy(voter, opts):
            seen.append((voter, [o[0] for o in opts]))
            return opts[0][0]

        prompter = FakePrompter(lynch=policy)
        session, _, _, _ = await started(ROLES8, prompter=prompter)
        session.game.mayor = 5
        await session._day_vote()
        assert all(voter not in ids for voter, ids in seen)

    run(go())


TIED_VOTES = {3: 1, 4: 1, 5: 2, 6: 2}  # P1 and P2 both get two votes


def test_tie_is_broken_by_the_mayor():
    async def go():
        prompter = FakePrompter(
            lynch=lambda voter, opts: TIED_VOTES.get(voter),
            tiebreak=lambda opts: [2],
        )
        session, channel, _, _ = await started(ROLES8, prompter=prompter)
        session.game.mayor = 7  # abstains, only breaks the tie
        await session._day_vote()
        assert not session.game.players[2].alive
        assert session.game.players[1].alive

    run(go())


def test_tie_is_random_when_the_mayor_does_not_answer():
    async def go():
        prompter = FakePrompter(
            lynch=lambda voter, opts: TIED_VOTES.get(voter),
            tiebreak=lambda opts: None,
        )
        session, channel, _, _ = await started(ROLES8, prompter=prompter)
        session.game.mayor = 7
        await session._day_vote()
        dead = [p.id for p in session.game.players.values() if not p.alive]
        assert len(dead) == 1 and dead[0] in (1, 2)
        assert channel.said(en("tie_random"))

    run(go())


def test_tie_without_mayor_means_nobody_dies():
    async def go():
        session, channel, _, _ = await started(ROLES8)
        session.game.mayor = None
        assert await session._break_tie([1, 2]) is None
        assert channel.said(en("tie_nobody"))

    run(go())


def test_no_votes_means_no_lynch():
    async def go():
        prompter = FakePrompter(lynch=lambda voter, opts: None)
        session, channel, _, _ = await started(ROLES8, prompter=prompter)
        await session._day_vote()
        assert len(session.game.alive()) == 8
        assert channel.said(en("no_votes"))

    run(go())


# -- lair --------------------------------------------------------------------
def test_wolves_vote_in_private_lair_and_it_is_deleted():
    async def go():
        guild = FakeGuild()
        channel = FakeChannel()
        channel.guild = guild
        session, _, prompter, _ = await started(ROLES8, channel=channel)
        assert session.lair is guild.lair
        await session._wolves()
        kind, destinations = prompter.votes[-1]
        assert kind == "wolves" and destinations == [guild.lair]
        assert guild.lair.said(en("lair_welcome"))
        await session._cleanup()
        assert guild.lair.deleted

    run(go())


def test_wolves_fall_back_to_dms_without_permission():
    async def go():
        guild = FakeGuild(fail=True)
        channel = FakeChannel()
        channel.guild = guild
        session, _, prompter, members = await started(ROLES8, channel=channel)
        assert session.lair is None and channel.said(en("lair_missing"))
        await session._wolves()
        kind, destinations = prompter.votes[-1]
        assert {m.id for m in destinations} == {w.id for w in session.game.with_role(W)}

    run(go())


# -- whole games -------------------------------------------------------------
def test_full_game_with_a_smart_village_ends():
    async def go():
        holder = {}

        def lynch(voter, opts):
            g = holder["s"].game
            wolf_ids = {p.id for p in g.with_role(W)}
            wolf_opts = [o[0] for o in opts if o[0] in wolf_ids]
            if g.players[voter].role is W:
                return next(o[0] for o in opts if o[0] not in wolf_ids)
            return wolf_opts[0] if wolf_opts else opts[0][0]

        def wolves(voter, opts):
            return opts[0][0]

        prompter = FakePrompter(lynch=lynch, wolves=wolves)
        session, channel, _, _ = make_session(prompter=prompter)
        holder["s"] = session
        winner = await session.run()
        assert winner is not None
        assert session.game.check_winner() is winner
        assert channel.said(en(f"winner_{winner.value}"))
        assert channel.said(en("final_roles", roles="")[:6])

    run(go())


def test_idle_game_is_abandoned():
    async def go():
        prompter = FakePrompter(
            wolves=lambda voter, opts: None,
            lynch=lambda voter, opts: None,
            cupid=lambda opts: None,
            seer=lambda opts: None,
        )
        session, channel, _, _ = make_session(prompter=prompter)
        assert await session.run() is None
        assert channel.said(en("game_idle", rounds=MAX_IDLE_ROUNDS))
        assert session.game.night == MAX_IDLE_ROUNDS

    run(go())


class RandomPrompter(FakePrompter):
    def __init__(self, rng, timeout_rate=0.15):
        def maybe(value):
            return None if rng.random() < timeout_rate else value

        def ids(opts):
            return [o[0] for o in opts]

        super().__init__(
            cupid=lambda opts: maybe(rng.sample(ids(opts), 2)),
            seer=lambda opts: maybe([rng.choice(ids(opts))]),
            hunter=lambda opts: maybe([rng.choice(ids(opts))]),
            tiebreak=lambda opts: maybe([rng.choice(ids(opts))]),
            wolves=lambda voter, opts: maybe(rng.choice(ids(opts))),
            mayor=lambda voter, opts: maybe(rng.choice(ids(opts))),
            lynch=lambda voter, opts: maybe(rng.choice(ids(opts))),
            witch=lambda **kw: maybe(
                rng.choice(
                    [
                        WitchAction(),
                        WitchAction(save=kw["can_heal"]),
                        WitchAction(poison=rng.choice([o[0] for o in kw["options"]])),
                    ]
                )
            )
            or WitchAction(),
        )


@pytest.mark.parametrize("seed", range(150))
def test_random_games_always_terminate_consistently(seed):
    async def go():
        rng = random.Random(seed)
        n = rng.randint(8, 18)
        options = GameOptions(
            werewolves=rng.choice([None, 1, 2, 3]),
            seer=rng.random() < 0.7,
            witch=rng.random() < 0.7,
            cupid=rng.random() < 0.7,
            hunter=rng.random() < 0.7,
        )
        session, channel, _, _ = make_session(
            n=n, prompter=RandomPrompter(rng), seed=seed, options=options
        )
        winner = await session.run()
        g = session.game
        assert g is not None
        if winner is not None:
            assert g.check_winner() is winner
            assert channel.said(en(f"winner_{winner.value}"))
        else:  # abandoned as idle
            assert channel.said(en("game_idle", rounds=MAX_IDLE_ROUNDS))
        # Invariants: lovers are mutual; at most one mayor, and alive if set.
        for p in g.players.values():
            if p.lover is not None:
                assert g.players[p.lover].lover == p.id
        if g.mayor is not None:
            assert g.players[g.mayor].alive

    run(go())
