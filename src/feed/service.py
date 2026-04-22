from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.schema import Article, Event, EventArticle, FeedEntry


@dataclass(frozen=True)
class FeedItem:
    event_id: int
    title: str
    score: float
    reason: Optional[str]
    primary_url: str
    source_id: int


async def list_feed(session: AsyncSession, *, user_id: int, limit: int = 10) -> list[FeedItem]:
    rows = await session.execute(
        select(FeedEntry).where(FeedEntry.user_id == user_id).order_by(FeedEntry.score.desc()).limit(limit)
    )
    entries = list(rows.scalars().all())
    if not entries:
        return []

    out: list[FeedItem] = []
    for e in entries:
        item = await _load_event_primary(session, e.event_id)
        if item is None:
            continue
        out.append(
            FeedItem(
                event_id=e.event_id,
                title=item[0],
                score=e.score,
                reason=e.reason,
                primary_url=item[1],
                source_id=item[2],
            )
        )
    return out


async def _load_event_primary(session: AsyncSession, event_id: int) -> tuple[str, str, int] | None:
    # Prefer primary article if present.
    row = await session.execute(
        select(Event.title, Article.url_canonical, Article.source_id)
        .join(EventArticle, EventArticle.event_id == Event.id)
        .join(Article, Article.id == EventArticle.article_id)
        .where(Event.id == event_id)
        .order_by(EventArticle.is_primary.desc(), Article.published_at.desc().nullslast(), Article.id.desc())
        .limit(1)
    )
    r = row.first()
    if r is None:
        return None
    return str(r[0]), str(r[1]), int(r[2])

