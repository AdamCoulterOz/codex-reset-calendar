# Public interface

## `resets.ics`

`https://adamcoulteroz.github.io/codex-reset-calendar/resets.ics` is a UTF-8 RFC 5545 iCalendar feed. It is served from `docs/resets.ics` and is intended for calendar subscription clients.

Each event has a stable `UID` derived solely from the original X post ID. Existing UIDs will not be repurposed. Events are ordered by their UTC start time and include the X URL, source summary, confidence, scope, audience when supplied, and timing provenance.

Classifications are `confirmed` (high-confidence archive-backed reset), `banked` (confirmed reset credit), and `tentative` (an explicit/timed live announcement). Timing uses `effective_at`, then `official_window`, then announcement time. The upstream feed at `https://codex-reset.com/api/feed` owns source data and classification inputs; this repository makes no affiliation, entitlement, schedule, or completeness guarantee. Generic limits discussion, forecasts, jokes, and non-reset events are excluded.

Consumers should retain events by UID and choose their own polling cadence. Backward compatibility means preserving the URL, stable UIDs, UTC dates, and RFC 5545 structure.

## Repository write contract

The cloud ingestion task may add or update only a qualifying normalized object in `data/events.json`, keyed by stable original X post ID. A proposed object must have its source `https://x.com/` URL, summary, UTC `announced_at`, global scope, and conservative classification inputs. It must satisfy the generator’s documented rules: archive-backed high-confidence reset; banked credit; or an explicit/timed reset announcement. The task must not add forecasts, generic limits discussion, jokes, personal quota information, or inferred events. Run `python scripts/ingest_events.py --input proposed.json`, then `python scripts/generate_ics.py --input data/events.json --output docs/resets.ics`, test, and commit both changed files. A push triggers validation and Pages refresh; GitHub Actions never polls the upstream API.
