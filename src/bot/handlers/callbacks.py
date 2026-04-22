from __future__ import annotations

import logging

from aiogram import Router
from aiogram.types import CallbackQuery

from src.feed.builder import build_feed_for_user
from src.storage.db import session_scope
from src.storage.repo import Repo


logger = logging.getLogger(__name__)

router = Router()


@router.callback_query()
async def on_callback(q: CallbackQuery) -> None:
    if q.from_user is None or q.data is None:
        return
    s = getattr(q.bot, "session_factory", None)
    if s is None:
        await q.answer("Сервис не инициализирован.", show_alert=True)
        return

    try:
        prefix, raw = q.data.split(":", 1)
    except ValueError:
        await q.answer("Некорректные данные кнопки.", show_alert=True)
        return

    async with session_scope(s) as session:  # type: ignore[arg-type]
        repo = Repo(session)
        user = await repo.upsert_user_by_telegram_id(q.from_user.id)

        if prefix == "ni":
            await repo.add_preference_signal(user_id=user.id, signal_type="not_interesting", event_id=int(raw))
            await build_feed_for_user(session, user_id=user.id)
            await q.answer("Ок, учту.", show_alert=False)
            return
        if prefix == "xs":
            await repo.set_source_override(user_id=user.id, source_id=int(raw), status="excluded")
            await build_feed_for_user(session, user_id=user.id)
            await q.answer("Источник исключён.", show_alert=False)
            return
        if prefix == "ai":
            await repo.add_interest(user_id=user.id, interest_name_norm=raw.strip().lower())
            await build_feed_for_user(session, user_id=user.id)
            await q.answer("Добавил интерес.", show_alert=False)
            return
        if prefix == "ri":
            await repo.remove_interest(user_id=user.id, interest_name_norm=raw.strip().lower())
            await build_feed_for_user(session, user_id=user.id)
            await q.answer("Убрал интерес.", show_alert=False)
            return

    await q.answer("Неизвестная кнопка.", show_alert=True)

