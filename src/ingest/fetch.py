from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass(frozen=True)
class FetchConfig:
    timeout_s: float = 15.0
    retries: int = 2
    concurrency: int = 8
    user_agent: str = "personal-news-digest-mvp/0.1"


class Fetcher:
    def __init__(self, config: FetchConfig | None = None) -> None:
        self.config = config or FetchConfig()
        self._sem = asyncio.Semaphore(self.config.concurrency)
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "Fetcher":
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout_s),
            headers={"User-Agent": self.config.user_agent},
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        if self._client is not None:
            await self._client.aclose()
        self._client = None

    async def get_text(self, url: str) -> str:
        if self._client is None:
            raise RuntimeError("Fetcher must be used as an async context manager.")

        async with self._sem:
            last_exc: Exception | None = None
            for _ in range(self.config.retries + 1):
                try:
                    r = await self._client.get(url)
                    r.raise_for_status()
                    return r.text
                except Exception as e:  # pragma: no cover (exercised via integration tests)
                    last_exc = e
                    await asyncio.sleep(0.2)
            assert last_exc is not None
            raise last_exc

