from __future__ import annotations

from src.digest.service import DigestItemView
from src.feed.service import FeedItem


def render_feed_item(item: FeedItem) -> str:
    reason = f"\n_{item.reason}_" if item.reason else ""
    return f"*{item.title}*\n{item.primary_url}{reason}"


def render_digest(items: list[DigestItemView]) -> str:
    lines: list[str] = []
    for idx, it in enumerate(items, start=1):
        lines.append(f"{idx}. *{it.title}*\n{it.summary_text}\n{it.primary_url}")
    return "\n\n".join(lines)

