# Contracts (Phase 1): Telegram bot interface

## Commands

### `/start`
- **Behavior**: приветствие + предложение выбрать интересы (если интересы пустые) или показать меню.
- **States**:
  - empty interests → show quick picks
  - configured → show main menu

### `/feed`
- **Behavior**: показать персональную ленту (события), отсортированную по актуальности/важности.
- **Empty**: если ничего нет — объяснить и предложить расширить интересы или посмотреть “общие”.

### `/digest`
- **Behavior**: “главные события дня” (5–12 пунктов), каждый пункт содержит:
  - заголовок события
  - краткий пересказ
  - ссылку на первоисточник (primary_url)
- **Empty**: корректное сообщение + предложения (FR-009).

### `/interests`
- **Behavior**: управление интересами (добавить/удалить).

### `/sources`
- **Behavior**: включение/исключение источников.

## Inline buttons (callback data)

### Button: “Не интересно”
- **Callback**: `ni:{event_id}`
- **Effect**: создать PreferenceSignal(type=not_interesting, event_id=...), пересчитать выдачу/скоринг.

### Button: “Исключить источник”
- **Callback**: `xs:{source_id}`
- **Effect**: UserSourceOverride(excluded), убрать из ленты.

### Button: “Добавить интерес”
- **Callback**: `ai:{interest_name_or_id}`

### Button: “Убрать интерес”
- **Callback**: `ri:{interest_name_or_id}`

## Message formatting (high-level)
- **Feed item**: 1 событие = 1 карточка, без дубликатов (FR-006), с кнопками действий.
- **Digest item**: коротко, сканируемо, максимум 2–4 строки текста + ссылка.

