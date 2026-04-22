from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from sqlalchemy.ext.asyncio import AsyncEngine

from src.common.logging import configure_logging
from src.common.settings import load_settings
from src.ingest.orchestrator import ensure_sources
from src.storage.db import create_engine, create_session_factory
from src.storage.schema import Base
from src.workers.jobs import run_ingest_cycle
from src.workers.scheduler import create_scheduler


logger = logging.getLogger(__name__)

async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)

    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is missing. Create .env (see .env.example).")
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is missing. Create .env (see .env.example).")

    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    await init_db(engine)

    if settings.proxy_url and settings.proxy_url.startswith(("socks5://", "socks4://")):
        from aiohttp_socks import ProxyConnector

        connector = ProxyConnector.from_url(settings.proxy_url)
        bot_session = AiohttpSession(connector=connector)
    else:
        bot_session = AiohttpSession(proxy=settings.proxy_url) if settings.proxy_url else AiohttpSession()
    bot = Bot(token=settings.bot_token, session=bot_session)
    dp = Dispatcher()
    # aiogram Bot is not a dict; keep shared deps as attributes.
    bot.session_factory = session_factory  # type: ignore[attr-defined]

    # Seed sources catalog once at startup.
    from src.storage.db import session_scope

    async with session_scope(session_factory) as session:
        await ensure_sources(session)

    from src.bot.handlers import callbacks_router, commands_router

    dp.include_router(commands_router)
    dp.include_router(callbacks_router)

    scheduler = create_scheduler()
    scheduler.add_job(run_ingest_cycle, "interval", minutes=20, args=[session_factory], id="ingest_cycle")
    scheduler.start()

    logger.info("Bot starting up")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
