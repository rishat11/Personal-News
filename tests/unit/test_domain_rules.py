import datetime as dt

from src.domain.rules import canonicalize_url, derive_event_key, hash_title_norm, is_near_duplicate, normalize_title


def test_canonicalize_url_drops_utm_and_fragment() -> None:
    u = "https://example.com/a?utm_source=x&x=1#frag"
    assert canonicalize_url(u) == "https://example.com/a?x=1"


def test_normalize_title_basic() -> None:
    assert normalize_title("  Hello, WORLD!!  ") == "hello world"


def test_hash_title_norm_length() -> None:
    h = hash_title_norm("hello world")
    assert len(h) == 32


def test_near_duplicate_threshold() -> None:
    assert is_near_duplicate("hello world", "hello world", threshold=0.9) is True
    assert is_near_duplicate("hello world", "completely different", threshold=0.9) is False


def test_event_key_buckets_by_day() -> None:
    k = derive_event_key("hello world", dt.datetime(2026, 1, 1, tzinfo=dt.UTC))
    assert k.endswith(":2026-01-01")

