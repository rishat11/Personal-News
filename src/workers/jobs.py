from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from src.ingest.orchestrator import ingest_once


logger = logging.getLogger(__name__)


async def run_ingest_cycle(session_factory: async_sessionmaker[AsyncSession]) -> None:
    try:
        async with session_factory() as session:
            async with session.begin():
                touched = await ingest_once(session)
        logger.info("Ingest cycle complete; touched_events=%s", len(touched))
    except Exception:
        logger.exception("Ingest cycle failed")

