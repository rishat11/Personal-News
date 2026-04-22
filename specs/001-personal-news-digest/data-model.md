# Data model (Phase 1): Personal news digest Telegram bot

## Entities

### User
- **id**: internal UUID/int
- **telegram_user_id**: int (unique)
- **timezone**: string (IANA), optional
- **created_at**: datetime

### Interest
- **id**
- **name**: string (normalized)
- **created_at**

### UserInterest (M:N)
- **user_id**
- **interest_id**
- **weight**: float (default 1.0), optional

### Source
- **id**
- **name**
- **feed_url**: string (RSS/Atom)
- **site_url**: string, optional
- **enabled_by_default**: bool

### UserSourceOverride
- **user_id**
- **source_id**
- **status**: enum(`included`, `excluded`)

### Article (news item)
- **id**
- **source_id**
- **url**: string (unique-ish after canonicalization)
- **url_canonical**: string (unique index)
- **title**
- **summary**: short text from feed, optional
- **content_text**: extracted article text, optional
- **published_at**: datetime, optional
- **fetched_at**: datetime
- **language**: string, optional
- **hash_title_norm**: string (for quick dedupe)

### Event (dedup cluster)
- **id**
- **key**: string (derived key, e.g. title_norm bucket + day)
- **title**: representative title
- **created_at**
- **updated_at**

### EventArticle (M:N)
- **event_id**
- **article_id**
- **is_primary**: bool

### PreferenceSignal
- **id**
- **user_id**
- **article_id** or **event_id** (one of them)
- **type**: enum(`not_interesting`, `mute_source`, `mute_interest`)
- **created_at**

### FeedEntry (materialized view-ish for user feed)
- **id**
- **user_id**
- **event_id**
- **score**: float
- **reason**: short text (e.g. matched interest “технологии”), optional
- **created_at**

### Digest (daily)
- **id**
- **user_id**
- **date**: date (in user timezone)
- **created_at**

### DigestItem
- **digest_id**
- **event_id**
- **rank**: int
- **summary_text**: short text (generated)
- **primary_url**: string

## Relationships / Notes
- User ↔ Interests: M:N through UserInterest.
- Event clusters multiple Articles; user-facing feed and digest reference Events to avoid duplicates (FR-006).
- Exclusions:
  - sources: UserSourceOverride
  - interests: handled in UserInterest (remove) + optional signal to downweight.

## Validation rules (from spec)
- If user has no interests: bot must propose quick pick and show general feed (FR-008).
- Digest size target: 5–12 items, fewer if not enough relevant events (SC-002, FR-009).

