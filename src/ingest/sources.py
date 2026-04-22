from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceSpec:
    name: str
    feed_url: str
    site_url: str | None
    enabled_by_default: bool = True


def default_sources() -> list[SourceSpec]:
    # Small MVP catalog; can be expanded later or moved to DB/admin tooling.
    return [
        SourceSpec(
            name="Hacker News",
            feed_url="https://hnrss.org/frontpage",
            site_url="https://news.ycombinator.com/",
            enabled_by_default=True,
        ),
        SourceSpec(
            name="BBC World",
            feed_url="http://feeds.bbci.co.uk/news/world/rss.xml",
            site_url="https://www.bbc.com/news/world",
            enabled_by_default=False,
        ),
    ]

