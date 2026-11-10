import random

import pytest

from werewolf_bot.engine import (
    Game,
    Role,
    RolesError,
    Winner,
    WitchAction,
    build_roles,
    count_votes,
    default_werewolf_count,
    leaders,
)


def make_game(roles, seed=1, **kwargs):
    players = {i + 1: f"P{i + 1}" for i in range(len(roles))}
    game = Game(players, list(roles), rng=random.Random(seed), **kwargs)
    # Make roles deterministic: player i gets roles[i].
    for pid, role in zip(players, roles):
        game.players[pid].role = role
    return game


W, V, S, WI, H, C = (
    Role.WEREWOLF,
    Role.VILLAGER,
    Role.SEER,
    Role.WITCH,
    Role.HUNTER,
    Role.CUPID,
)


# -- composition -------------------------------------------------------------
@pytest.mark.parametrize(
    "players,wolves", [(8, 2), (11, 2), (12, 3), (18, 3)]
)
def test_default_werewolf_count_matches_readme_table(players, wolves):
    assert default_werewolf_count(players) == wolves


def test_build_roles_fills_with_villagers():
    roles = build_roles(10)
    assert len(roles) == 10
    assert roles.count(W) == 2
    assert all(roles.count(r) == 1 for r in (S, WI, C, H))
    assert roles.count(V) == 4


def test_build_roles_can_disable_specials_and_set_wolves():
    roles = build_roles(9, werewolves=3, seer=False, cupid=False)
    assert roles.count(W) == 3
    assert S not in roles and C not in roles
    assert roles.count(WI) == 1 and roles.count(H) == 1


@pytest.mark.parametrize(
    "players,kwargs,code",
    [
        (8, {"werewolves": 0}, "too_few_wolves"),
        (8, {"werewolves": 4}, "too_many_wolves"),
        (5, {"werewolves": 2}, "too_many_special"),  # 2 wolves + 4 specials > 5
    ],
)
def test_build_roles_rejects_impossible_setups(players, kwargs, code):
    with pytest.raises(RolesError) as exc:
        build_roles(players, **kwargs)
    assert exc.value.args[0] == code


def test_game_needs_one_role_per_player():
    with pytest.raises(ValueError):
        Game({1: "a", 2: "b"}, [W])


def test_roles_are_shuffled_but_complete():
    roles = build_roles(12)
    game = Game({i: f"P{i}" for i in range(12)}, roles, rng=random.Random(7))
    assert sorted(p.role.value for p in game.players.values()) == sorted(
        r.value for r in roles
    )


# -- deaths ------------------------------------------------------------------
def test_kill_returns_death_and_is_idempotent():
    g = make_game([W, V, V])
    deaths = g.kill(2, "vote")
    assert [d.player_id for d in deaths] == [2]
    assert deaths[0].role is V and deaths[0].cause == "vote"
    assert g.kill(2, "vote") == []


def test_lover_dies_of_grief_once():
    g = make_game([W, V, V, V])
    g.set_lovers(2, 3)
    deaths = g.kill(2, "werewolves")
    assert [(d.player_id, d.cause) for d in deaths] == [(2, "werewolves"), (3, "love")]
    assert g.kill(3, "vote") == []


def test_lovers_must_differ():
    g = make_game([W, V, V])
    with pytest.raises(ValueError):
        g.set_lovers(1, 1)


def test_mayor_death_is_flagged():
    g = make_game([W, V, V])
    g.mayor = 2
    g.kill(2, "vote")
    assert g.mayor is None and g.mayor_died


# -- night -------------------------------------------------------------------
def test_night_victim_dies():
    g = make_game([W, V, V, WI])
    deaths = g.resolve_night(2)
    assert [d.player_id for d in deaths] == [2]
    assert not g.players[2].alive


def test_witch_save_prevents_death_and_uses_potion():
    g = make_game([W, V, V, WI])
    assert g.resolve_night(2, WitchAction(save=True)) == []
    assert g.players[2].alive and not g.heal_available
    with pytest.raises(ValueError):
        g.resolve_night(3, WitchAction(save=True))


def test_witch_poison_kills_and_is_single_use():
    g = make_game([W, V, V, WI])
    deaths = g.resolve_night(None, WitchAction(poison=3))
    assert [d.player_id for d in deaths] == [3] and deaths[0].cause == "poison"
    assert not g.poison_available
    with pytest.raises(ValueError):
        g.resolve_night(None, WitchAction(poison=2))


def test_poisoning_the_victim_kills_only_once():
    g = make_game([W, V, V, WI])
    deaths = g.resolve_night(2, WitchAction(poison=2))
    assert [d.player_id for d in deaths] == [2]


def test_one_potion_per_night_rule():
    g = make_game([W, V, V, WI])
    with pytest.raises(ValueError):
        g.resolve_night(2, WitchAction(save=True, poison=3))
    g2 = make_game([W, V, V, WI], witch_one_potion_per_night=False)
    deaths = g2.resolve_night(2, WitchAction(save=True, poison=3))
    assert [d.player_id for d in deaths] == [3]


def test_cannot_poison_dead_player():
    g = make_game([W, V, V, WI])
    g.kill(3, "vote")
    with pytest.raises(ValueError):
        g.resolve_night(None, WitchAction(poison=3))


def test_poison_kill_can_trigger_lover_chain():
    g = make_game([W, V, V, WI])
    g.set_lovers(2, 3)
    deaths = g.resolve_night(None, WitchAction(poison=2))
    assert {d.player_id for d in deaths} == {2, 3}


# -- votes -------------------------------------------------------------------
def test_count_votes_and_leaders():
    counts = count_votes({1: 3, 2: 3, 3: 4})
    assert counts == {3: 2, 4: 1}
    assert leaders(counts) == [3]
    assert sorted(leaders({3: 2, 4: 2, 5: 1})) == [3, 4]
    assert leaders({}) == []


def test_mayor_vote_counts_double():
    g = make_game([W, V, V, V])
    g.mayor = 2
    counts = g.lynch_counts({1: 3, 2: 4, 3: 4, 4: 3})
    assert counts == {3: 2, 4: 3}


def test_lynch_counts_ignore_dead_voters_and_targets():
    g = make_game([W, V, V, V])
    g.kill(4, "vote")
    counts = g.lynch_counts({4: 2, 1: 4, 2: 3})
    assert counts == {3: 1}


# -- winners -----------------------------------------------------------------
def test_village_wins_when_no_wolves():
    g = make_game([W, V, V])
    g.kill(1, "vote")
    assert g.check_winner() is Winner.VILLAGE


def test_wolves_win_when_only_wolves_remain():
    g = make_game([W, V, V])
    g.kill(2, "werewolves")
    assert g.check_winner() is None
    g.kill(3, "werewolves")
    assert g.check_winner() is Winner.WEREWOLVES


def test_wolves_outnumbering_villagers_is_not_a_win_yet():
    # Strict rule: werewolves win only once *no* non-wolf is left alive.
    assert make_game([W, W, V]).check_winner() is None


def test_game_continues_otherwise():
    assert make_game([W, W, V, V, V]).check_winner() is None


def test_mixed_lovers_win_together():
    g = make_game([W, V, V, V])
    g.set_lovers(1, 2)
    g.kill(3, "werewolves")
    assert g.check_winner() is None
    g.kill(4, "werewolves")
    assert g.check_winner() is Winner.LOVERS


def test_same_camp_lovers_do_not_win_alone():
    g = make_game([W, V, V, V])
    g.set_lovers(2, 3)
    g.kill(1, "vote")
    assert g.check_winner() is Winner.VILLAGE


def test_nobody_wins_when_everyone_dies():
    g = make_game([W, V])
    g.set_lovers(1, 2)
    g.kill(1, "vote")
    assert g.check_winner() is Winner.NOBODY


def test_seer_reveals_role():
    g = make_game([W, S, V])
    assert g.reveal(1) is W
