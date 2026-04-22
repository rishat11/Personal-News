from __future__ import annotations

import logging
import re

from aiogram import Router
from aiogram.types import Message

from src.feed.builder import build_feed_for_user
from src.storage.db import session_scope
from src.storage.repo import Repo


logger = logging.getLogger(__name__)

router = Router()

_SPLIT_RE = re.compile(r"[,;\n]+")


def _parse_interest_tokens(text: str) -> list[str]:
    parts = _SPLIT_RE.split(text)
    out: list[str] = []
    for p in parts:
        t = p.strip().lower()
        if not t or len(t) > 64:
            continue
        out.append(t)
    return out


@router.message()
async def on_plain_text_interests(message: Message) -> None:
    """
    Add interests from free-form text (comma/newline separated).
    Commands and non-text updates are ignored by other handlers first; this is a fallback.
    """
    if message.from_user is None:
        return
    if not message.text:
        return
    raw = message.text.strip()
    if not raw or raw.startswith("/"):
        return

    tokens = _parse_interest_tokens(raw)
    if not tokens:
        return

    s = getattr(message.bot, "session_factory", None)
    if s is None:
        await message.answer("Сервис не инициализирован.")
        return

    async with session_scope(s) as session:  # type: ignore[arg-type]
        repo = Repo(session)
        user = await repo.upsert_user_by_telegram_id(message.from_user.id)
        for t in tokens:
            await repo.add_interest(user_id=user.id, interest_name_norm=t)
        await build_feed_for_user(session, user_id=user.id)

    if len(tokens) == 1:
        await message.answer(f"Добавил интерес: {tokens[0]}\nОткрой /feed или /digest.")
    else:
        await message.answer(f"Добавил интересы: {', '.join(tokens)}\nОткрой /feed или /digest.")
