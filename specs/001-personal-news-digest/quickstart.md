# Quickstart (Phase 1): Personal news digest Telegram bot

## Prerequisites
- Python 3.12+
- Telegram Bot Token

## Environment
Create `.env` (example keys):

- `BOT_TOKEN` — Telegram bot token
- `DATABASE_URL` — e.g. `sqlite:///./app.db`
- `LOG_LEVEL` — e.g. `INFO`

## Run (local)
Suggested commands (to be implemented in the codebase):

- Install deps (either `pip` + `requirements.txt` or `poetry`/`uv` once chosen)
- Run bot: `python -m src.main`

## Smoke checklist
- `/start` shows onboarding and quick interest selection (FR-008)
- “Лента” shows items relevant to interests; no excluded sources appear (FR-002/FR-005)
- “Дайджест дня” returns 5–12 items with summaries and links (FR-003/FR-004, SC-002)

