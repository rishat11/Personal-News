from __future__ import annotations

import datetime as dt
import logging
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.rules import derive_event_key, is_near_duplicate, normalize_title
from src.ingest.fetch import Fetcher
from src.ingest.parse import parse_feed
from src.ingest.sources import SourceSpec, default_sources
from src.storage.repo import Repo
from src.storage.schema import Article, EventArticle, Source


logger = logging.getLogger(__name__)


async def ensure_sources(session: AsyncSession, specs: Iterable[SourceSpec] | None = None) -> None:
    repo = Repo(session)
    for s in (specs or default_sources()):
        await repo.upsert_source(name=s.name, feed_url=s.feed_url, site_url=s.site_url, enabled_by_default=s.enabled_by_default)


async def ingest_once(session: AsyncSession) -> list[int]:
    """
    Fetch enabled sources, store new articles, and link them into events.
    Returns a list of event_ids that were touched.
    """
    repo = Repo(session)

    rows = await session.execute(select(Source).where(Source.enabled_by_default.is_(True)))
    sources = list(rows.scalars().all())
    if not sources:
        logger.info("No enabled sources configured")
        return []

    touched_events: set[int] = set()
    now = dt.datetime.now(dt.UTC)

    async with Fetcher() as fetcher:
        for s in sources:
            try:
                feed_text = await fetcher.get_text(s.feed_url)
                entries = parse_feed(feed_text, fetched_at=now)
                for e in entries:
                    article = await repo.insert_article(
                        source_id=s.id,
                        url=e.url,
                        url_canonical=e.url_canonical,
                        title=e.title,
                        summary=e.summary,
                        content_text=None,
                        published_at=e.published_at,
                        fetched_at=e.fetched_at,
                        language=None,
                        hash_title_norm=e.hash_title,
                    )
                    event_id = await _link_article_to_event(session, article)
                    if event_id is not None:
                        touched_events.add(event_id)
            except Exception:
                logger.exception("Source ingest failed: %s", s.feed_url)
                continue

    return sorted(touched_events)


async def _link_article_to_event(session: AsyncSession, article: Article) -> int | None:
    """
    MVP clustering: try to find near-duplicate event title within 48h window.
    """
    repo = Repo(session)

    title_norm = normalize_title(article.title)
    key = derive_event_key(title_norm, article.published_at)

    # First, deterministic key match
    event = await repo.get_or_create_event(key=key, title=article.title)

    # Decide primary article: first link wins for MVP.
    existing = await session.scalar(
        select(EventArticle).where(EventArticle.event_id == event.id, EventArticle.is_primary.is_(True))
    )
    is_primary = existing is None
    await repo.link_event_article(event_id=event.id, article_id=article.id, is_primary=is_primary)
    return event.id

