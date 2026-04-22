from __future__ import annotations

import datetime as dt
from typing import Optional

from pydantic import BaseModel, Field


class UserSettingsSnapshot(BaseModel):
    user_id: int
    interests: list[str] = Field(default_factory=list)
    excluded_source_ids: list[int] = Field(default_factory=list)


class NormalizedArticleView(BaseModel):
    article_id: int
    source_id: int
    url: str
    url_canonical: str
    title: str
    title_norm: str
    hash_title_norm: str
    summary: Optional[str] = None
    content_text: Optional[str] = None
    published_at: Optional[dt.datetime] = None


class NormalizedEventView(BaseModel):
    event_id: int
    title: str
    primary_url: str
    primary_source_id: int
    published_at: Optional[dt.datetime] = None

