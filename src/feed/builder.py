from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.rules import interest_score, normalize_title, recency_boost
from src.storage.repo import Repo
from src.storage.schema import (
    Article,
    Event,
    EventArticle,
    FeedEntry,
    Interest,
    PreferenceSignal,
    Source,
    UserInterest,
    UserSourceOverride,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FeedConfig:
    window_hours: int = 72
    limit: int = 30


async def build_feed_for_user(session: AsyncSession, *, user_id: int, config: FeedConfig | None = None) -> None:
    config = config or FeedConfig()
    repo = Repo(session)

    interests = await repo.list_interests(user_id)
    excluded_source_ids = await _excluded_sources(session, user_id)

    now = dt.datetime.now(dt.UTC)
    since = now - dt.timedelta(hours=config.window_hours)

    candidates = await _candidate_events(session, since)
    if not candidates:
        return

    muted_event_ids = await _muted_events(session, user_id)

    for ev_id, ev_title, published_at, primary_url, primary_source_id in candidates:
        if ev_id in muted_event_ids:
            continue
        if primary_source_id in excluded_source_ids:
            continue

        title_norm = normalize_title(ev_title)
        i_score, reason = interest_score(title_norm, [normalize_title(i) for i in interests])

        base = recency_boost(published_at, now=now)
        score = base + i_score

        # General feed for empty interests: keep only recency.
        if interests:
            if i_score <= 0:
                continue

        await repo.upsert_feed_entry(user_id=user_id, event_id=ev_id, score=score, reason=reason)


async def _excluded_sources(session: AsyncSession, user_id: int) -> set[int]:
    rows = await session.execute(
        select(UserSourceOverride.source_id).where(
            UserSourceOverride.user_id == user_id, UserSourceOverride.status == "excluded"
        )
    )
    return {r[0] for r in rows.all()}


async def _muted_events(session: AsyncSession, user_id: int) -> set[int]:
    rows = await session.execute(
        select(PreferenceSignal.event_id)
        .where(PreferenceSignal.user_id == user_id, PreferenceSignal.type == "not_interesting")
        .where(PreferenceSignal.event_id.is_not(None))
    )
    return {r[0] for r in rows.all() if r[0] is not None}


async def _candidate_events(session: AsyncSession, since: dt.datetime) -> list[tuple[int, str, Optional[dt.datetime], str, int]]:
    # Pick primary article for event if exists else any.
    stmt = (
        select(
            Event.id,
            Event.title,
            func.max(Article.published_at).label("published_at"),
            Article.url_canonical,
            Article.source_id,
        )
        .join(EventArticle, EventArticle.event_id == Event.id)
        .join(Article, Article.id == EventArticle.article_id)
        .join(Source, Source.id == Article.source_id)
        .where(Article.fetched_at >= since, Source.enabled_by_default.is_(True))
        .order_by(func.max(Article.published_at).desc().nullslast(), Event.id.desc())
        .group_by(Event.id, Event.title, Article.url_canonical, Article.source_id)
        .limit(200)
    )
    rows = await session.execute(stmt)
    return [(int(r[0]), str(r[1]), r[2], str(r[3]), int(r[4])) for r in rows.all()]

