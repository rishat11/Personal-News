from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.digest.rank import DigestConfig, rank_events_for_user
from src.digest.summarize import extractive_summary
from src.storage.schema import Article, Digest, DigestItem, Event, EventArticle, Source


@dataclass(frozen=True)
class DigestItemView:
    event_id: int
    title: str
    summary_text: str
    primary_url: str


async def get_or_build_daily_digest(
    session: AsyncSession, *, user_id: int, date: dt.date | None = None, config: DigestConfig | None = None
) -> list[DigestItemView]:
    date = date or dt.datetime.now(dt.UTC).date()
    existing = await session.scalar(select(Digest).where(Digest.user_id == user_id, Digest.date == date))
    if existing is not None:
        return await _load_digest_items(session, existing.id)

    items = await build_daily_digest(session, user_id=user_id, date=date, config=config)
    return items


async def build_daily_digest(
    session: AsyncSession, *, user_id: int, date: dt.date, config: DigestConfig | None = None
) -> list[DigestItemView]:
    config = config or DigestConfig()
    event_ids = await rank_events_for_user(session, user_id=user_id, config=config)

    digest = Digest(user_id=user_id, date=date)
    session.add(digest)
    await session.flush()

    views: list[DigestItemView] = []
    rank = 1
    for ev_id in event_ids[: config.max_items]:
        primary = await _load_event_primary(session, ev_id)
        if primary is None:
            continue
        title, url, content_text, summary = primary
        summary_text = extractive_summary(content_text, summary)
        session.add(
            DigestItem(
                digest_id=digest.id,
                event_id=ev_id,
                rank=rank,
                summary_text=summary_text,
                primary_url=url,
            )
        )
        views.append(DigestItemView(event_id=ev_id, title=title, summary_text=summary_text, primary_url=url))
        rank += 1

    return views


async def _load_digest_items(session: AsyncSession, digest_id: int) -> list[DigestItemView]:
    rows = await session.execute(
        select(DigestItem.event_id, DigestItem.summary_text, DigestItem.primary_url, Event.title)
        .join(Event, Event.id == DigestItem.event_id)
        .where(DigestItem.digest_id == digest_id)
        .order_by(DigestItem.rank.asc())
    )
    out: list[DigestItemView] = []
    for ev_id, summary_text, primary_url, title in rows.all():
        out.append(
            DigestItemView(
                event_id=int(ev_id),
                title=str(title),
                summary_text=str(summary_text),
                primary_url=str(primary_url),
            )
        )
    return out


async def _load_event_primary(
    session: AsyncSession, event_id: int
) -> tuple[str, str, Optional[str], Optional[str]] | None:
    row = await session.execute(
        select(Event.title, Article.url_canonical, Article.content_text, Article.summary)
        .join(EventArticle, EventArticle.event_id == Event.id)
        .join(Article, Article.id == EventArticle.article_id)
        .join(Source, Source.id == Article.source_id)
        .where(Event.id == event_id, Source.enabled_by_default.is_(True))
        .order_by(EventArticle.is_primary.desc(), Article.published_at.desc().nullslast(), Article.id.desc())
        .limit(1)
    )
    r = row.first()
    if r is None:
        return None
    return str(r[0]), str(r[1]), (r[2] if r[2] is None else str(r[2])), (r[3] if r[3] is None else str(r[3]))

