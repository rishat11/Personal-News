from __future__ import annotations

from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_url: str
    log_level: str = "INFO"
    proxy_url: str | None = None


def load_settings() -> Settings:
    # Optional dotenv support for local runs; production can use real env vars.
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv()
    except Exception:
        pass

    bot_token = (getenv("BOT_TOKEN") or "").strip()
    database_url = (getenv("DATABASE_URL") or "").strip()
    log_level = (getenv("LOG_LEVEL") or "INFO").strip().upper()
    proxy_url = (getenv("PROXY_URL") or "").strip() or None

    return Settings(bot_token=bot_token, database_url=database_url, log_level=log_level, proxy_url=proxy_url)
