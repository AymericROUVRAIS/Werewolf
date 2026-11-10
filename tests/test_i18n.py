import re
import string
from pathlib import Path

from werewolf_bot.engine import Role, Winner
from werewolf_bot.i18n import STRINGS, tr

SRC = Path(__file__).resolve().parent.parent / "werewolf_bot"


def placeholders(text):
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def test_languages_have_the_same_keys():
    assert set(STRINGS["en"]) == set(STRINGS["fr"])


def test_languages_use_the_same_placeholders():
    for key, text in STRINGS["en"].items():
        assert placeholders(text) == placeholders(STRINGS["fr"][key]), key


def test_every_key_used_in_code_exists():
    used = set()
    for path in SRC.glob("*.py"):
        text = path.read_text()
        used |= set(re.findall(r'(?:_say|\.t|tr)\((?:self\.lang, |lang, )?"([a-z_]+)"', text))
        used |= set(re.findall(r'\("(ui_[a-z_]+)"', text))
        used |= set(re.findall(r'"(err_[a-z_]+|lobby_[a-z_]+)"', text))
    missing = {k for k in used if k not in STRINGS["en"]}
    assert not missing, missing


def test_dynamic_keys_exist_for_every_role_and_winner():
    for role in Role:
        for prefix in ("role_", "desc_"):
            assert f"{prefix}{role.value}" in STRINGS["en"]
    for winner in Winner:
        assert f"winner_{winner.value}" in STRINGS["en"]
    for code in ("too_few_wolves", "too_many_wolves", "too_many_special"):
        assert f"err_roles_{code}" in STRINGS["en"]


def test_fallback_to_english_then_key():
    assert tr("xx", "no_deaths") == STRINGS["en"]["no_deaths"]
    assert tr("en", "does_not_exist") == "does_not_exist"
