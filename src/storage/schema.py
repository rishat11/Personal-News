from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC))

    interests: Mapped[list["UserInterest"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    source_overrides: Mapped[list["UserSourceOverride"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Interest(Base):
    __tablename__ = "interests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC))

    users: Mapped[list["UserInterest"]] = relationship(back_populates="interest", cascade="all, delete-orphan")


class UserInterest(Base):
    __tablename__ = "user_interests"
    __table_args__ = (UniqueConstraint("user_id", "interest_id", name="uq_user_interest"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    interest_id: Mapped[int] = mapped_column(ForeignKey("interests.id", ondelete="CASCADE"), primary_key=True)
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=1.0)

    user: Mapped["User"] = relationship(back_populates="interests")
    interest: Mapped["Interest"] = relationship(back_populates="users")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    feed_url: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    site_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    enabled_by_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    articles: Mapped[list["Article"]] = relationship(back_populates="source")
    overrides: Mapped[list["UserSourceOverride"]] = relationship(back_populates="source", cascade="all, delete-orphan")


class UserSourceOverride(Base):
    __tablename__ = "user_source_overrides"
    __table_args__ = (UniqueConstraint("user_id", "source_id", name="uq_user_source_override"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)  # included|excluded

    user: Mapped["User"] = relationship(back_populates="source_overrides")
    source: Mapped["Source"] = relationship(back_populates="overrides")


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (
        UniqueConstraint("url_canonical", name="uq_article_url_canonical"),
        Index("ix_articles_published_at", "published_at"),
        Index("ix_articles_fetched_at", "fetched_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    url_canonical: Mapped[str] = mapped_column(String(2000), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC))
    language: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    hash_title_norm: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    source: Mapped["Source"] = relationship(back_populates="articles")
    event_links: Mapped[list["EventArticle"]] = relationship(back_populates="article", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("key", name="uq_event_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC))
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC))

    articles: Mapped[list["EventArticle"]] = relationship(back_populates="event", cascade="all, delete-orphan")


class EventArticle(Base):
    __tablename__ = "event_articles"
    __table_args__ = (UniqueConstraint("event_id", "article_id", name="uq_event_article"),)

    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    event: Mapped["Event"] = relationship(back_populates="articles")
    article: Mapped["Article"] = relationship(back_populates="event_links")


class PreferenceSignal(Base):
    __tablename__ = "preference_signals"
    __table_args__ = (
        Index("ix_pref_user_created", "user_id", "created_at"),
        Index("ix_pref_event_created", "event_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id: Mapped[Optional[int]] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=True)
    article_id: Mapped[Optional[int]] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), nullable=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # not_interesting|mute_source|mute_interest
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC))


class FeedEntry(Base):
    __tablename__ = "feed_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_feed_user_event"),
        Index("ix_feed_user_score", "user_id", "score"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC))


class Digest(Base):
    __tablename__ = "digests"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_digest_user_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC))

    items: Mapped[list["DigestItem"]] = relationship(back_populates="digest", cascade="all, delete-orphan")


class DigestItem(Base):
    __tablename__ = "digest_items"
    __table_args__ = (UniqueConstraint("digest_id", "rank", name="uq_digest_rank"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    digest_id: Mapped[int] = mapped_column(ForeignKey("digests.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    primary_url: Mapped[str] = mapped_column(String(2000), nullable=False)

    digest: Mapped["Digest"] = relationship(back_populates="items")

