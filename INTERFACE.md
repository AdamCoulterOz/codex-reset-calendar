# Public interface

## `resets.ics`

`https://adamcoulteroz.github.io/codex-reset-calendar/resets.ics` is a UTF-8 RFC 5545 iCalendar feed. It is served from `docs/resets.ics` and is intended for calendar subscription clients.

Each event has a stable `UID` derived solely from the original X post ID. Existing UIDs will not be repurposed. Events are ordered by their UTC start time and include the X URL, source summary, confidence, scope, audience when supplied, and timing provenance.

Classifications are `confirmed` (high-confidence archive-backed `reset` or `promo` record whose upstream summary identifies a reset), `banked` (high-confidence archive-backed `credits` record, including legacy records with no `reset_kind`), and `tentative` (an explicit/timed live announcement). A live tentative needs both a public official window and an `announced`/`hinted` state; generic live candidates are excluded. Pure `boost` records are excluded. Timing uses `effective_at`, then `official_window`, then announcement time. The upstream feed at `https://codex-reset.com/api/feed` owns source data and classification inputs; this repository makes no affiliation, entitlement, schedule, or completeness guarantee. Generic limits discussion, forecasts, jokes, and non-reset events are excluded.

Consumers should retain events by UID and choose their own polling cadence. Backward compatibility means preserving the URL, stable UIDs, UTC dates, and RFC 5545 structure.

## Repository write contract

The cloud ingestion task may add or update only a qualifying normalized object in `data/events.json`, keyed by stable original X post ID. Its minimum object is `id`, canonical `https://x.com/.../status/<id>` `url`, `summary`, UTC `announced_at`, `scope: "global"`, `source: "cloud_task"`, and `confidence: "high"`. It must also supply `type` plus explicit classification wording: a completed reset has `type: "reset"`, `announcement_state: "confirmed"`, `preview: false`; a future explicit reset has `type: "reset"`, `announcement_state: "announced"`, `preview: true` (and an `official_window` when a time is known); a banked reset has `type: "credits"`, `reset_kind: "banked"`. The task must not mark a fresh post `source: "archive"`, or add forecasts, generic limits discussion, jokes, personal quota information, or inferred events. It commits only `data/events.json`; the push-triggered GitHub Action tests, regenerates, and commits `docs/resets.ics`. GitHub Actions never polls the upstream API.
