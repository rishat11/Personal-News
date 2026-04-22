from __future__ import annotations

import datetime as dt
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.keyboards.inline import interests_manage_kb, quick_interests_kb
from src.bot.messages.render import render_digest, render_feed_item
from src.digest.service import get_or_build_daily_digest
from src.feed.builder import build_feed_for_user
from src.feed.service import list_feed
from src.storage.db import session_scope
from src.storage.repo import Repo


logger = logging.getLogger(__name__)

router = Router()

QUICK_INTERESTS = ["технологии", "экономика", "политика", "спорт", "наука"]


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    if message.from_user is None:
        return
    await message.answer(
        "Привет! Я собираю персональную ленту новостей и дневной дайджест.\n"
        "Источники — русскоязычные СМИ. Начнём с выбора интересов, затем открой /feed.",
        reply_markup=quick_interests_kb(QUICK_INTERESTS),
    )


@router.message(Command("interests"))
async def cmd_interests(message: Message) -> None:
    if message.from_user is None:
        return
    s = getattr(message.bot, "session_factory", None)
    if s is None:
        await message.answer("Сервис не инициализирован.")
        return

    async with session_scope(s) as session:  # type: ignore[arg-type]
        repo = Repo(session)
        user = await repo.upsert_user_by_telegram_id(message.from_user.id)
        interests = await repo.list_interests(user.id)

    if not interests:
        await message.answer("У вас пока нет интересов. Выберите:", reply_markup=quick_interests_kb(QUICK_INTERESTS))
        return
    await message.answer("Ваши интересы (нажмите, чтобы убрать):", reply_markup=interests_manage_kb(interests))


@router.message(Command("feed"))
async def cmd_feed(message: Message) -> None:
    if message.from_user is None:
        return
    s = getattr(message.bot, "session_factory", None)
    if s is None:
        await message.answer("Сервис не инициализирован.")
        return

    async with session_scope(s) as session:  # type: ignore[arg-type]
        repo = Repo(session)
        user = await repo.upsert_user_by_telegram_id(message.from_user.id)
        await build_feed_for_user(session, user_id=user.id)
        items = await list_feed(session, user_id=user.id, limit=10)

    if not items:
        await message.answer(
            "Пока нет подходящих новостей.\n"
            "Попробуйте добавить интересы через /interests или вернитесь позже."
        )
        return

    for it in items:
        await message.answer(render_feed_item(it), parse_mode="Markdown")


@router.message(Command("digest"))
async def cmd_digest(message: Message) -> None:
    if message.from_user is None:
        return
    s = getattr(message.bot, "session_factory", None)
    if s is None:
        await message.answer("Сервис не инициализирован.")
        return

    async with session_scope(s) as session:  # type: ignore[arg-type]
        repo = Repo(session)
        user = await repo.upsert_user_by_telegram_id(message.from_user.id)
        items = await get_or_build_daily_digest(session, user_id=user.id, date=dt.datetime.now(dt.UTC).date())

    if not items:
        await message.answer(
            "Сегодня пока нет значимых новостей по вашим интересам.\n"
            "Попробуйте расширить интересы или вернитесь позже."
        )
        return

    await message.answer(render_digest(items), parse_mode="Markdown")

