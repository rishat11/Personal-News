# Implementation Plan: Personal news digest Telegram bot

**Branch**: `[001-personal-news-digest]` | **Date**: 2026-04-22 | **Spec**: `specs/001-personal-news-digest/spec.md`  
**Input**: Feature specification from `specs/001-personal-news-digest/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Telegram-бот агрегирует новости из выбранных источников/по темам, строит персональную ленту и по запросу формирует дневной дайджест (5–12 пунктов) с краткими пересказами и ссылками на первоисточники. Персонализация опирается на интересы пользователя, исключения источников/тем и сигналы “не интересно”; дубликаты материалов объединяются в “события”.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: `aiogram` (Telegram bot), `httpx` (HTTP), `feedparser` (RSS/Atom), `beautifulsoup4` + `readability-lxml` (извлечение текста статьи), `sqlalchemy` (SQLite), `apscheduler` (фоновые джобы), `pydantic` (валидация)  
**Storage**: SQLite (локально) через SQLAlchemy; миграции — `alembic` (если потребуется)  
**Testing**: `pytest` + `pytest-asyncio`, фикстуры на SQLite-in-memory, контракты команд/кнопок  
**Target Platform**: Linux server (Docker-friendly), локальный запуск на Windows  
**Project Type**: Telegram bot service + background workers (ingest, dedupe, digest build)  
**Performance Goals**: p95 ответа бота на команду \(< 1s\) при наличии кеша; сбор фидов батчами, обновление ленты — каждые 10–30 минут, дайджест — формирование \(< 20s\) на пользователя при холодном кеше  
**Constraints**: лимиты Telegram API; внешние источники могут быть недоступны/тормозить; нельзя полагаться на “идеальную” структуру HTML; хранение PII минимальное (telegram user id, настройки)  
**Scale/Scope**: MVP до 1k пользователей, десятки источников, до ~10k материалов/день суммарно

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Code Quality**: читаемые модули, стабильные интерфейсы (команды бота, callback-данные), явные ошибки (источник недоступен, пустая выдача).
- **Testing Standards**: тесты на дедупликацию, фильтрацию по интересам/исключениям, генерацию дайджеста (детерминированно, без реальных внешних сервисов).
- **UX Consistency**: одинаковые форматы сообщений, явные состояния (нет интересов / нет новостей / ошибка источников), корректные тексты.
- **Performance**: без unbounded-сканов; индексы по ключам (user_id, published_at, event_id); батчинг сетевых запросов; таймауты/ретраи.
- **Dependency Hygiene**: зависимости добавлять только по необходимости; LLM-суммаризацию сделать опциональной/заменяемой.

## Project Structure

### Documentation (this feature)

```text
specs/001-personal-news-digest/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
```text
src/
├── bot/
│   ├── handlers/           # команды, callback'и, роутинг aiogram
│   ├── keyboards/          # inline/reply клавиатуры
│   ├── middlewares/
│   └── messages/           # форматирование/рендер сообщений
├── domain/
│   ├── models.py           # Pydantic доменные модели
│   └── rules.py            # правила персонализации/дедупликации
├── ingest/
│   ├── fetch.py            # загрузка RSS/страниц с таймаутами
│   ├── parse.py            # нормализация новости (title, url, time, text)
│   └── sources.py          # каталог источников (предустановки)
├── digest/
│   ├── rank.py             # скоринг “важности/релевантности”
│   └── summarize.py        # краткий пересказ (экстрактивный по умолчанию)
├── storage/
│   ├── db.py               # engine/session
│   ├── schema.py           # SQLAlchemy модели/DDL
│   └── repo.py             # запросы/репозитории
├── workers/
│   ├── scheduler.py        # APScheduler jobs
│   └── jobs.py             # ingest/dedupe/build digest
└── main.py                 # entrypoint

tests/
├── contract/               # контракты команд/кнопок/форматов
├── integration/            # ingest + storage + domain rules
└── unit/                   # дедуп, ранжирование, форматирование
```

**Structure Decision**: Single project. В репозитории пока нет кода, поэтому структура выше — целевая для реализации MVP бота.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
