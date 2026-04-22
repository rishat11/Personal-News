from __future__ import annotations

import re
from typing import Optional


_SPACE_RE = re.compile(r"\s+")


def extractive_summary(text: Optional[str], fallback: Optional[str], *, max_chars: int = 350) -> str:
    """
    Deterministic, extractive summary for MVP.
    - Prefer content_text; fallback to RSS summary; fallback to empty string.
    """
    base = (text or "").strip()
    if not base:
        base = (fallback or "").strip()
    base = _SPACE_RE.sub(" ", base).strip()
    if not base:
        return "Краткого описания пока нет."
    if len(base) <= max_chars:
        return base
    cut = base[: max_chars - 1].rstrip()
    return f"{cut}…"

