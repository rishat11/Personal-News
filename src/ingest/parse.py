from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Optional

import feedparser
from bs4 import BeautifulSoup

from src.domain.rules import canonicalize_url, hash_title_norm, normalize_title


@dataclass(frozen=True)
class ParsedEntry:
    title: str
    url: str
    url_canonical: str
    summary: Optional[str]
    published_at: Optional[dt.datetime]
    fetched_at: dt.datetime
    title_norm: str
    hash_title: str


def _parse_published(entry) -> Optional[dt.datetime]:  # type: ignore[no-untyped-def]
    if getattr(entry, "published_parsed", None):
        return dt.datetime(*entry.published_parsed[:6], tzinfo=dt.UTC)
    if getattr(entry, "updated_parsed", None):
        return dt.datetime(*entry.updated_parsed[:6], tzinfo=dt.UTC)
    return None


def parse_feed(feed_text: str, fetched_at: Optional[dt.datetime] = None) -> list[ParsedEntry]:
    fetched_at = fetched_at or dt.datetime.now(dt.UTC)
    parsed = feedparser.parse(feed_text)

    out: list[ParsedEntry] = []
    for e in parsed.entries:
        url = (getattr(e, "link", "") or "").strip()
        title = (getattr(e, "title", "") or "").strip()
        if not url or not title:
            continue

        summary_raw = (getattr(e, "summary", None) or getattr(e, "description", None))
        summary = None
        if isinstance(summary_raw, str) and summary_raw.strip():
            # Strip HTML tags but keep readable text.
            soup = BeautifulSoup(summary_raw, "html.parser")
            summary = soup.get_text(" ", strip=True)[:2000] or None

        url_can = canonicalize_url(url)
        title_norm = normalize_title(title)
        out.append(
            ParsedEntry(
                title=title,
                url=url,
                url_canonical=url_can,
                summary=summary,
                published_at=_parse_published(e),
                fetched_at=fetched_at,
                title_norm=title_norm,
                hash_title=hash_title_norm(title_norm),
            )
        )
    return out

