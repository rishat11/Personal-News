from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.rules import normalize_title, recency_boost
from src.storage.schema import Article, Event, EventArticle, FeedEntry


@dataclass(frozen=True)
class DigestConfig:
    window_hours: int = 24
    min_items: int = 5
    max_items: int = 12


async def rank_events_for_user(session: AsyncSession, *, user_id: int, config: DigestConfig | None = None) -> list[int]:
    config = config or DigestConfig()
    now = dt.datetime.now(dt.UTC)
    since = now - dt.timedelta(hours=config.window_hours)

    # Prefer using already materialized feed when available.
    rows = await session.execute(
        select(FeedEntry.event_id).where(FeedEntry.user_id == user_id).order_by(FeedEntry.score.desc()).limit(100)
    )
    event_ids = [int(r[0]) for r in rows.all()]
    if event_ids:
        return event_ids[: config.max_items]

    # Fallback: recency-based selection from recent articles.
    stmt = (
        select(Event.id)
        .join(EventArticle, EventArticle.event_id == Event.id)
        .join(Article, Article.id == EventArticle.article_id)
        .where(Article.fetched_at >= since)
        .group_by(Event.id)
        .order_by(func.max(Article.published_at).desc().nullslast(), func.max(Article.fetched_at).desc())
        .limit(config.max_items)
    )
    rows2 = await session.execute(stmt)
    return [int(r[0]) for r in rows2.all()]

