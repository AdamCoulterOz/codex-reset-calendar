#!/usr/bin/env python3
"""Conservatively merge qualifying upstream event objects into data/events.json."""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from generate_ics import classify

KEEP = {"id", "type", "group", "summary", "url", "announced_at", "effective_at", "official_window", "preview", "scope", "confidence", "source", "source_label", "reset_kind", "banked_state", "audience", "reason_tags", "announcement_state", "time_kind"}


def incoming_events(payload: object) -> list[dict]:
    if isinstance(payload, dict):
        return payload.get("events", [])
    return payload if isinstance(payload, list) else []


def qualifying(event: dict) -> dict | None:
    if not isinstance(event, dict) or not classify(event):
        return None
    if not all(event.get(key) for key in ("id", "url", "announced_at", "summary")):
        return None
    if not str(event["url"]).startswith("https://x.com/"):
        return None
    return {key: event[key] for key in KEEP if key in event}


def merge(existing: dict, incoming: object) -> dict:
    merged = {str(event["id"]): event for event in existing.get("events", []) if isinstance(event, dict) and event.get("id")}
    for event in incoming_events(incoming):
        event = qualifying(event)
        if event:
            merged[str(event["id"])] = event
    return {"schema_version": 1, "events": sorted(merged.values(), key=lambda event: (event["announced_at"], str(event["id"]))) }


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge public feed event object(s) by stable X post ID.")
    parser.add_argument("--data", default="data/events.json", type=pathlib.Path)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=pathlib.Path, help="JSON feed or JSON array of proposed event objects")
    source.add_argument("--url", help="One-off bootstrap feed URL; never used by GitHub Actions")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8")) if args.input else json.load(urllib.request.urlopen(args.url, timeout=30))
    existing = json.loads(args.data.read_text(encoding="utf-8")) if args.data.exists() else {"events": []}
    result = merge(existing, payload)
    args.data.parent.mkdir(parents=True, exist_ok=True)
    args.data.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"stored {len(result['events'])} qualifying events")


if __name__ == "__main__":
    main()
