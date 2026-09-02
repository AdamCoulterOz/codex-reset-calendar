# Context

This repository publishes a static iCalendar subscription for public Codex and ChatGPT Work usage-reset information. `scripts/generate_ics.py` uses only Python’s standard library and checked-in `data/events.json`. GitHub Pages serves `docs/`; GitHub Actions validates that committed data and generated calendar are in sync.

The generator intentionally distinguishes archive-backed confirmations from live announcements and does not infer an individual's usage state. A separate cloud task, not GitHub Actions, may poll public data and commit a conservatively qualified normalized event.
