from __future__ import annotations

import datetime as dt
import hashlib
import re
from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from rapidfuzz.fuzz import ratio as fuzz_ratio


_SPACE_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[\t\r\n]+")

_DROP_QUERY_PREFIXES = (
    "utm_",
    "yclid",
    "gclid",
    "fbclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "ref_src",
    "spm",
)


def canonicalize_url(url: str) -> str:
    """
    Remove common tracking parameters; normalize scheme/host; strip fragments.
    Deterministic and test-friendly.
    """
    p = urlparse(url.strip())
    scheme = (p.scheme or "https").lower()
    netloc = p.netloc.lower()
    path = p.path or "/"

    kept = []
    for k, v in parse_qsl(p.query, keep_blank_values=True):
        kl = k.lower()
        if any(kl == x or kl.startswith(x) for x in _DROP_QUERY_PREFIXES):
            continue
        kept.append((k, v))
    query = urlencode(kept, doseq=True)

    return urlunparse((scheme, netloc, path, "", query, ""))


def normalize_title(title: str) -> str:
    t = title.strip().lower()
    t = _PUNCT_RE.sub(" ", t)
    t = re.sub(r"[“”\"'`]+", "", t)
    t = re.sub(r"[^\w\s\-]+", " ", t, flags=re.UNICODE)
    t = _SPACE_RE.sub(" ", t).strip()
    return t


def hash_title_norm(title_norm: str) -> str:
    return hashlib.sha256(title_norm.encode("utf-8")).hexdigest()[:32]


def is_near_duplicate(title_a_norm: str, title_b_norm: str, threshold: float = 0.9) -> bool:
    if not title_a_norm or not title_b_norm:
        return False
    score = fuzz_ratio(title_a_norm, title_b_norm) / 100.0
    return score >= threshold


def derive_event_key(title_norm: str, published_at: Optional[dt.datetime]) -> str:
    """
    Bucket by day (UTC) to reduce unbounded clustering.
    """
    day = "unknown"
    if published_at is not None:
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=dt.UTC)
        day = published_at.astimezone(dt.UTC).date().isoformat()
    return f"{hash_title_norm(title_norm)}:{day}"


@dataclass(frozen=True)
class ScoredItem:
    event_id: int
    score: float
    reason: Optional[str]


def recency_boost(published_at: Optional[dt.datetime], now: Optional[dt.datetime] = None) -> float:
    if published_at is None:
        return 0.0
    if now is None:
        now = dt.datetime.now(dt.UTC)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=dt.UTC)
    age_h = max(0.0, (now - published_at).total_seconds() / 3600.0)
    # 0..~1.5 over 48h
    return max(0.0, 1.5 - (age_h / 32.0))


def interest_score(event_title_norm: str, interests_norm: Iterable[str]) -> tuple[float, Optional[str]]:
    """
    MVP heuristic: exact substring match against normalized interests.
    """
    best: Optional[str] = None
    for i in interests_norm:
        if not i:
            continue
        if i in event_title_norm:
            best = i
            break
    if best is None:
        return 0.0, None
    return 2.0, f"interest:{best}"

