# Tasks (Phase 2): Personal news digest Telegram bot

**Branch**: `[001-personal-news-digest]` | **Date**: 2026-04-22  
**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/telegram-bot.md`, `quickstart.md`

## Guiding principles (MVP)
- Deterministic behavior in tests (no live network, no LLM dependency by default).
- Store and display **Events** (not raw Articles) to satisfy FR-006 (no duplicates).
- Keep bot UX explicit for empty states (FR-008, FR-009).

## Phase A — Repo scaffolding & dependencies
- [X] Create Python project skeleton per `plan.md`:
  - `src/bot/{handlers,keyboards,middlewares,messages}/`
  - `src/domain/`, `src/ingest/`, `src/digest/`, `src/storage/`, `src/workers/`
  - `tests/{unit,integration,contract}/`
- [X] Add dependency management (choose one and implement):
  - Option 1: `requirements.txt` (+ `requirements-dev.txt`)
  - Option 2: `pyproject.toml` (Poetry/uv)
- [X] Add `.env.example` with `BOT_TOKEN`, `DATABASE_URL`, `LOG_LEVEL`.
- [X] Add `src/main.py` entrypoint to start bot + scheduler.
- [X] Add basic logging configuration (JSON or readable text) and consistent log levels.

## Phase B — Storage layer (SQLAlchemy + SQLite)
- [X] Implement `src/storage/db.py`:
  - engine creation from `DATABASE_URL`
  - async vs sync decision (document in code via types; keep consistent across repo)
  - session factory + context manager helper
- [X] Implement `src/storage/schema.py` SQLAlchemy models for entities in `data-model.md`:
  - `User`, `Interest`, `UserInterest`
  - `Source`, `UserSourceOverride`
  - `Article`, `Event`, `EventArticle`
  - `PreferenceSignal`
  - `FeedEntry`
  - `Digest`, `DigestItem`
- [X] Add indexes/constraints needed for MVP:
  - unique: `User.telegram_user_id`
  - unique (or unique-ish): `Article.url_canonical`
  - time-based indexes for `Article.published_at`, `Article.fetched_at`
  - join indexes for `EventArticle`, `UserInterest`, `UserSourceOverride`
- [X] Implement `src/storage/repo.py` with repositories/queries:
  - upsert/get `User` by telegram id
  - get/set interests (add/remove/list)
  - list sources + per-user overrides (include/exclude)
  - insert articles, create/find events, link event↔article
  - record `PreferenceSignal`
  - materialize user `FeedEntry` (insert/update score, list feed)
  - store/load daily digest and items
- [X] Add migrations strategy:
  - MVP: `create_all()` on startup for local dev
  - Optional: add Alembic baseline if schema expected to evolve immediately

## Phase C — Domain rules (personalization, dedupe, ranking)
- [X] Implement Pydantic domain models in `src/domain/models.py` for:
  - user settings snapshot (interests, excluded sources)
  - normalized article/event view used by feed/digest rendering
- [X] Implement normalization utilities in `src/domain/rules.py`:
  - canonicalize URL (remove UTM/tracking params)
  - normalize title (lowercase, punctuation trimming, whitespace)
- [X] Implement MVP dedup strategy (from `research.md`):
  - compute `hash_title_norm`
  - near-duplicate detection using RapidFuzz title similarity \(\ge 0.9\)
  - time window (e.g. 48h) to limit candidate search
  - event key derivation and rules for primary article selection
- [X] Implement scoring/ranking primitives used by feed/digest:
  - interest match scoring (simple keyword/category mapping for MVP)
  - penalties: excluded sources, “not interesting” signals
  - recency boost based on `published_at`
  - produce `score` + optional short `reason` string for `FeedEntry`

## Phase D — Ingest pipeline (RSS + article text extraction)
- [X] Implement `src/ingest/sources.py`:
  - MVP source catalog with a small set of RSS/Atom feeds
  - `enabled_by_default` flags per `data-model.md`
- [X] Implement `src/ingest/fetch.py`:
  - HTTP client with timeouts, retries, user-agent
  - rate-limiting/batching strategy (simple concurrency cap)
- [X] Implement `src/ingest/parse.py`:
  - parse RSS/Atom entries (feedparser)
  - extract `title`, `url`, `summary`, `published_at`
  - canonicalize URL, set `fetched_at`
  - optionally fetch HTML and extract `content_text` (BeautifulSoup + readability-lxml)
- [X] Implement ingest orchestration:
  - for each enabled source: fetch feed, parse entries, store new Articles
  - run dedupe linking Articles into Events
  - update per-user FeedEntries for affected events (or mark dirty for rebuild)
- [X] Add resilience:
  - per-source failure isolation (one feed down shouldn’t break whole cycle)
  - clear logs and metrics counters (even if just log-based)

## Phase E — Feed materialization (per-user)
- [X] Define “general feed” behavior for users with no interests (FR-008):
  - show top events by recency/importance from default-enabled sources
- [X] Implement feed builder:
  - compute candidate events from recent window (e.g. 24–72h)
  - filter by user interests (if configured)
  - apply exclusions (sources) (FR-005)
  - apply preference signals (FR-007)
  - save/update `FeedEntry` rows (score, reason)
- [X] Implement feed retrieval:
  - list top N feed events for `/feed`
  - ensure one event appears once (FR-006)

## Phase F — Digest generation (daily)
- [X] Implement `src/digest/summarize.py` (default: extractive, deterministic):
  - build short summary from `content_text` or `summary`
  - enforce length and readability constraints (2–4 lines target in Telegram)
  - fallback when text unavailable
- [X] Implement `src/digest/rank.py`:
  - rank events for a user for a given date window
  - select 5–12 events (SC-002), fewer if not enough (FR-009)
- [X] Implement digest builder:
  - compute date in user timezone (if set; else server default)
  - store `Digest` + `DigestItem` (event_id, rank, summary_text, primary_url)
- [X] Implement digest retrieval:
  - return cached digest if already built for that day
  - rebuild policy (e.g. allow refresh command to rebuild once/day)

## Phase G — Telegram bot UX (aiogram)
- [X] Implement command routing in `src/bot/handlers/` per `contracts/telegram-bot.md`:
  - `/start` onboarding:
    - if no interests: show quick picks
    - else: show main menu
  - `/feed` show feed items with action buttons
  - `/digest` show digest items with summaries + links
  - `/interests` manage interests (add/remove)
  - `/sources` manage source include/exclude
- [X] Implement keyboards in `src/bot/keyboards/`:
  - callback data formats: `ni:{event_id}`, `xs:{source_id}`, `ai:{interest}`, `ri:{interest}`
- [X] Implement callback handlers:
  - “Не интересно” → create `PreferenceSignal(not_interesting, event_id=...)`, refresh feed
  - “Исключить источник” → set `UserSourceOverride(excluded)`, refresh feed
  - add/remove interest → update `UserInterest`, refresh feed
- [X] Implement message rendering helpers in `src/bot/messages/`:
  - feed item: one event card, no duplicates (FR-006), with buttons
  - digest item: compact, scannable, link included (FR-004)
- [X] Add empty-state messaging:
  - no interests → quick pick + general feed (FR-008)
  - no content → explain + suggest actions (FR-009)

## Phase H — Background workers (APScheduler)
- [X] Implement `src/workers/scheduler.py`:
  - periodic ingest job (every 10–30 minutes)
  - optional digest precompute job (daily per timezone bucket or on-demand only for MVP)
- [X] Implement `src/workers/jobs.py`:
  - `run_ingest_cycle()`
  - `rebuild_feeds_for_changed_events()` (or simpler “rebuild all active users” for MVP scale)
  - `build_daily_digest_for_user()` (if precompute enabled)
- [X] Ensure clean shutdown and error isolation:
  - scheduler stops on bot shutdown
  - jobs log exceptions and continue next tick

## Phase I — Tests (pytest + pytest-asyncio)
- [X] Unit tests:
  - URL canonicalization
  - title normalization
  - dedupe clustering (same event across sources)
  - ranking selection count (5–12) and empty behavior (FR-009)
  - extractive summary determinism
- [ ] Integration tests (SQLite in-memory):
  - ingest → store Articles → Events → feed materialization (no duplicates)
  - exclusions (sources) remove items from feed (FR-005)
  - “not interesting” signal affects subsequent feed (FR-007)
- [X] Contract tests for bot interface (`tests/contract/`):
  - callback parsing for `ni/xs/ai/ri`
  - message formatting: feed and digest include links (FR-004)
- [ ] Add HTTP/network isolation:
  - mock `httpx` responses for RSS + HTML pages
  - deterministic fixtures for feeds and articles

## Phase J — Operational readiness
- [X] Update repository-level README (or feature README) with:
  - how to create `.env`
  - how to run `python -m src.main`
  - how to run tests
- [ ] Add basic Docker support (optional for MVP but recommended):
  - `Dockerfile`
  - minimal `docker-compose.yml` for local run
- [X] Add runtime safeguards:
  - Telegram token validation on startup
  - DB connectivity check
  - configurable timeouts and concurrency settings

## Phase K — Acceptance scenario verification (from `spec.md`)
- [ ] US1 (P1) Personal feed:
  - configure interests → `/feed` shows relevant items, sorted by score/recency
  - changing interests updates feed accordingly
- [ ] US2 (P2) Daily digest:
  - configured interests → `/digest` returns 5–12 items with summaries and links
  - no significant news → appropriate empty response + suggestions
- [ ] US3 (P3) Controls:
  - exclude source → source items never appear afterward (SC-004)
  - “not interesting” reduces similar items frequency in subsequent feed views

