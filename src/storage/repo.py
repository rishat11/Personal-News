from __future__ import annotations

import datetime as dt
from typing import Optional, Sequence

from sqlalchemy import Select, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.schema import (
    Article,
    Event,
    EventArticle,
    FeedEntry,
    Interest,
    PreferenceSignal,
    Source,
    User,
    UserInterest,
    UserSourceOverride,
)


class Repo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_user_by_telegram_id(self, telegram_user_id: int) -> User:
        user = await self.session.scalar(select(User).where(User.telegram_user_id == telegram_user_id))
        if user is not None:
            return user
        user = User(telegram_user_id=telegram_user_id)
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_user(self, telegram_user_id: int) -> Optional[User]:
        return await self.session.scalar(select(User).where(User.telegram_user_id == telegram_user_id))

    async def list_interests(self, user_id: int) -> list[str]:
        rows = await self.session.execute(
            select(Interest.name)
            .join(UserInterest, UserInterest.interest_id == Interest.id)
            .where(UserInterest.user_id == user_id)
            .order_by(Interest.name)
        )
        return [r[0] for r in rows.all()]

    async def add_interest(self, user_id: int, interest_name_norm: str) -> None:
        interest = await self.session.scalar(select(Interest).where(Interest.name == interest_name_norm))
        if interest is None:
            interest = Interest(name=interest_name_norm)
            self.session.add(interest)
            await self.session.flush()

        exists = await self.session.scalar(
            select(UserInterest).where(UserInterest.user_id == user_id, UserInterest.interest_id == interest.id)
        )
        if exists is None:
            self.session.add(UserInterest(user_id=user_id, interest_id=interest.id, weight=1.0))

    async def remove_interest(self, user_id: int, interest_name_norm: str) -> None:
        interest_id = await self.session.scalar(select(Interest.id).where(Interest.name == interest_name_norm))
        if interest_id is None:
            return
        await self.session.execute(
            delete(UserInterest).where(UserInterest.user_id == user_id, UserInterest.interest_id == interest_id)
        )

    async def list_sources_with_overrides(self, user_id: int) -> list[tuple[Source, Optional[str]]]:
        rows = await self.session.execute(
            select(Source, UserSourceOverride.status)
            .outerjoin(
                UserSourceOverride,
                (UserSourceOverride.source_id == Source.id) & (UserSourceOverride.user_id == user_id),
            )
            .order_by(Source.name)
        )
        return [(r[0], r[1]) for r in rows.all()]

    async def set_source_override(self, user_id: int, source_id: int, status: str) -> None:
        override = await self.session.scalar(
            select(UserSourceOverride).where(
                UserSourceOverride.user_id == user_id, UserSourceOverride.source_id == source_id
            )
        )
        if override is None:
            self.session.add(UserSourceOverride(user_id=user_id, source_id=source_id, status=status))
        else:
            override.status = status

    async def upsert_source(self, *, name: str, feed_url: str, site_url: Optional[str], enabled_by_default: bool) -> Source:
        source = await self.session.scalar(select(Source).where(Source.feed_url == feed_url))
        if source is None:
            source = Source(name=name, feed_url=feed_url, site_url=site_url, enabled_by_default=enabled_by_default)
            self.session.add(source)
            await self.session.flush()
            return source
        source.name = name
        source.site_url = site_url
        source.enabled_by_default = enabled_by_default
        return source

    async def insert_article(
        self,
        *,
        source_id: int,
        url: str,
        url_canonical: str,
        title: str,
        summary: Optional[str],
        content_text: Optional[str],
        published_at: Optional[dt.datetime],
        fetched_at: dt.datetime,
        language: Optional[str],
        hash_title_norm: Optional[str],
    ) -> Article:
        existing = await self.session.scalar(select(Article).where(Article.url_canonical == url_canonical))
        if existing is not None:
            return existing

        article = Article(
            source_id=source_id,
            url=url,
            url_canonical=url_canonical,
            title=title,
            summary=summary,
            content_text=content_text,
            published_at=published_at,
            fetched_at=fetched_at,
            language=language,
            hash_title_norm=hash_title_norm,
        )
        self.session.add(article)
        await self.session.flush()
        return article

    async def get_recent_articles_for_dedupe(self, since: dt.datetime) -> Sequence[Article]:
        rows = await self.session.execute(select(Article).where(Article.fetched_at >= since))
        return rows.scalars().all()

    async def get_or_create_event(self, *, key: str, title: str) -> Event:
        event = await self.session.scalar(select(Event).where(Event.key == key))
        if event is not None:
            return event
        event = Event(key=key, title=title)
        self.session.add(event)
        await self.session.flush()
        return event

    async def link_event_article(self, *, event_id: int, article_id: int, is_primary: bool) -> None:
        exists = await self.session.scalar(
            select(EventArticle).where(EventArticle.event_id == event_id, EventArticle.article_id == article_id)
        )
        if exists is None:
            self.session.add(EventArticle(event_id=event_id, article_id=article_id, is_primary=is_primary))

    async def upsert_feed_entry(self, *, user_id: int, event_id: int, score: float, reason: Optional[str]) -> FeedEntry:
        entry = await self.session.scalar(select(FeedEntry).where(FeedEntry.user_id == user_id, FeedEntry.event_id == event_id))
        if entry is None:
            entry = FeedEntry(user_id=user_id, event_id=event_id, score=score, reason=reason)
            self.session.add(entry)
            await self.session.flush()
            return entry
        entry.score = score
        entry.reason = reason
        return entry

    async def list_top_feed_entries(self, *, user_id: int, limit: int) -> list[FeedEntry]:
        rows = await self.session.execute(
            select(FeedEntry).where(FeedEntry.user_id == user_id).order_by(FeedEntry.score.desc()).limit(limit)
        )
        return list(rows.scalars().all())

    async def add_preference_signal(
        self, *, user_id: int, signal_type: str, event_id: int | None = None, article_id: int | None = None
    ) -> PreferenceSignal:
        ps = PreferenceSignal(user_id=user_id, type=signal_type, event_id=event_id, article_id=article_id)
        self.session.add(ps)
        await self.session.flush()
        return ps

