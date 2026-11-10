"""Settings, read from environment variables (or a local ``.env`` file)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from .engine import MAX_PLAYERS, MIN_PLAYERS
from .i18n import LANGUAGES
from .session import Timings


def _bool(value: Optional[str], default: bool) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    token: str
    guild_id: Optional[int] = None  # sync slash commands to one server instantly
    default_language: str = "en"
    min_players: int = MIN_PLAYERS
    max_players: int = MAX_PLAYERS
    create_lair: bool = True
    timings: Timings = Timings()

    @classmethod
    def from_env(cls) -> "Config":
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:  # python-dotenv is optional
            pass

        token = os.environ.get("DISCORD_TOKEN", "").strip()
        if not token:
            raise SystemExit(
                "DISCORD_TOKEN is not set. Copy .env.example to .env and fill it in."
            )
        language = os.environ.get("DEFAULT_LANGUAGE", "en").strip().lower()
        if language not in LANGUAGES:
            raise SystemExit(f"DEFAULT_LANGUAGE must be one of {', '.join(LANGUAGES)}")
        guild = os.environ.get("DISCORD_GUILD_ID", "").strip()
        return cls(
            token=token,
            guild_id=int(guild) if guild else None,
            default_language=language,
            min_players=max(4, int(os.environ.get("WEREWOLF_MIN_PLAYERS", MIN_PLAYERS))),
            create_lair=_bool(os.environ.get("WEREWOLF_CREATE_LAIR"), True),
            timings=Timings(
                night=float(os.environ.get("WEREWOLF_NIGHT_SECONDS", 60)),
                discussion=float(os.environ.get("WEREWOLF_DISCUSSION_SECONDS", 120)),
                vote=float(os.environ.get("WEREWOLF_VOTE_SECONDS", 60)),
            ),
        )
