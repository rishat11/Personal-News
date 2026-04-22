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
            name="Лента.ру — новости",
            feed_url="https://lenta.ru/rss/news",
            site_url="https://lenta.ru/",
            enabled_by_default=True,
        ),
        SourceSpec(
            name="Коммерсантъ — главное",
            feed_url="https://www.kommersant.ru/RSS/main.xml",
            site_url="https://www.kommersant.ru/",
            enabled_by_default=True,
        ),
        SourceSpec(
            name="Газета.Ru — первая полоса",
            feed_url="https://www.gazeta.ru/export/rss/first.xml",
            site_url="https://www.gazeta.ru/",
            enabled_by_default=True,
        ),
        SourceSpec(
            name="МК — все материалы",
            feed_url="https://www.mk.ru/rss/index.xml",
            site_url="https://www.mk.ru/",
            enabled_by_default=True,
        ),
        SourceSpec(
            name="Российская газета",
            feed_url="https://rg.ru/xml/index.xml",
            site_url="https://rg.ru/",
            enabled_by_default=True,
        ),
        SourceSpec(
            name="Hacker News",
            feed_url="https://hnrss.org/frontpage",
            site_url="https://news.ycombinator.com/",
            enabled_by_default=False,
        ),
        SourceSpec(
            name="BBC World",
            feed_url="http://feeds.bbci.co.uk/news/world/rss.xml",
            site_url="https://www.bbc.com/news/world",
            enabled_by_default=False,
        ),
    ]

