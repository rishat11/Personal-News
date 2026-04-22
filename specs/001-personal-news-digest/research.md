# Research (Phase 0): Personal news digest Telegram bot

## Decisions

### Decision: Python + aiogram as the bot framework
- **Rationale**: зрелая async-экосистема, быстрый MVP, удобный роутинг/finite-state flows.
- **Alternatives considered**: `python-telegram-bot`, `telebot` (pyTelegramBotAPI).

### Decision: SQLite + SQLAlchemy для хранения (MVP)
- **Rationale**: минимум инфраструктуры; достаточно для 1k пользователей и 10k материалов/день; легко мигрировать на Postgres позже.
- **Alternatives considered**: PostgreSQL сразу; файлы/JSON (хуже для индексации/дедупа).

### Decision: RSS/Atom как основной канал источников, HTML-парсинг как дополнение
- **Rationale**: RSS проще и стабильнее; HTML-текст нужен для пересказа, если RSS даёт только анонс.
- **Alternatives considered**: парсинг сайтов “в лоб” без RSS (хрупко), платные агрегаторы/News API (зависимость/ключи).

### Decision: Дедупликация как кластеризация в “Event”
- **Rationale**: требования FR-006/“не показывать повторы” проще выполнить, если хранить “материалы” и “события” отдельно.
- **Technique (MVP)**:
  - canonicalize URL (utm, tracking params)
  - normalize title (lower, punctuation)
  - near-duplicate by \(title\_sim \ge 0.9\) (RapidFuzz) + окно по времени (например, 48 часов)
  - при совпадении — привязать Article к существующему Event
- **Alternatives considered**: embedding-based clustering (требует LLM/векторного стора), только URL-based (не ловит разные URL про одно событие).

### Decision: Пересказ по умолчанию — экстрактивный (без LLM), LLM как опциональный адаптер
- **Rationale**: детерминированность для тестов и отсутствие зависимости от внешних сервисов; LLM можно добавить позже для качества.
- **Alternatives considered**: обязательный LLM (дорого/нестабильно, усложняет CI).

### Decision: Планировщик фоновых задач — APScheduler
- **Rationale**: простой запуск джоб в одном процессе для MVP; позже можно вынести в отдельный воркер/очередь.
- **Alternatives considered**: Celery/RQ/Arq (лишняя инфраструктура для MVP).

## Open Questions (for Phase 2 tasks / implementation)
- Каталог источников: фиксированный список в коде или управление через админ-команды?
- Выбор интересов: свободный текст vs предопределённые темы.
- Язык контента: RU-only или multi-language? (влияет на токенизацию/суммаризацию).

