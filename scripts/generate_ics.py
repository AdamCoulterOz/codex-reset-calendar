#!/usr/bin/env python3
"""Generate the public, deterministic Codex reset iCalendar feed."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib

UTC = dt.timezone.utc
DEFAULT_DURATION = dt.timedelta(minutes=30)


def parse_time(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def ical_time(value: dt.datetime) -> str:
    return value.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def escape(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")


def fold(line: str) -> list[str]:
    """Fold RFC 5545 content lines at 75 UTF-8 octets, retaining characters."""
    pieces: list[str] = []
    current = ""
    limit = 75
    for character in line:
        if len((current + character).encode("utf-8")) > limit:
            pieces.append(current)
            current = " " + character
            limit = 75
        else:
            current += character
    pieces.append(current)
    return pieces


def is_confirmed(event: dict) -> bool:
    return event.get("source") == "archive" and event.get("confidence") == "high" and not event.get("preview")


def classify(event: dict) -> str | None:
    if event.get("scope") != "global":
        return None
    archive = event.get("source") == "archive" and event.get("confidence") == "high"
    cloud = event.get("source") == "cloud_task" and event.get("confidence") == "high"
    if event.get("type") == "credits" and event.get("reset_kind") == "banked" and (archive or cloud):
        return "banked"
    if event.get("type") == "credits" and archive and not event.get("preview"):
        return "banked"
    if event.get("type") == "promo" and archive and not event.get("preview"):
        return "confirmed"
    if event.get("type") != "reset":
        return None
    if event.get("preview"):
        timed_live_preview = event.get("source") == "live" and event.get("announcement_state") in {"announced", "hinted"} and (event.get("official_window") or {}).get("start_at")
        return "tentative" if (archive or cloud or timed_live_preview) else None
    if is_confirmed(event):
        return "confirmed"
    if cloud and event.get("announcement_state") == "confirmed":
        return "confirmed"
    # The feed's live, non-archived reset announcements are deliberately not
    # upgraded to confirmations here.
    if cloud and event.get("announcement_state") == "announced":
        return "tentative"
    if event.get("source") == "live" and event.get("announcement_state") in {"announced", "hinted"}:
        return "tentative"
    return None


def event_times(event: dict) -> tuple[dt.datetime, dt.datetime, str]:
    if event.get("effective_at"):
        start = parse_time(event["effective_at"])
        return start, start + DEFAULT_DURATION, "effective_at"
    window = event.get("official_window") or {}
    if window.get("start_at"):
        start = parse_time(window["start_at"])
        end = parse_time(window.get("end_at", window["start_at"]))
        return start, max(end, start + dt.timedelta(minutes=1)), "official_window"
    start = parse_time(event["announced_at"])
    return start, start + DEFAULT_DURATION, "announced_at"


def normalized_events(feed: dict) -> list[dict]:
    selected: dict[str, dict] = {}
    for event in feed.get("events", []):
        classification = classify(event)
        source_id = str(event.get("id", ""))
        if not classification or not source_id or not event.get("url") or not event.get("announced_at"):
            continue
        copy = dict(event)
        copy["classification"] = classification
        copy["start"], copy["end"], copy["timing_provenance"] = event_times(copy)
        selected[source_id] = copy
    return sorted(selected.values(), key=lambda item: (item["start"], str(item["id"])))


def title(event: dict) -> str:
    if event["classification"] == "banked":
        return "Confirmed banked reset"
    if event["classification"] == "confirmed":
        return "Confirmed usage reset"
    return "Announced/tentative usage reset"


def vevent(event: dict) -> list[str]:
    audience = ", ".join(event.get("audience") or []) or "not specified"
    description = (
        f"{event.get('summary', '').strip()}\\n\\n"
        f"Classification: {event['classification']}\\n"
        f"Scope: {event.get('scope', 'not specified')}\\n"
        f"Confidence: {event.get('confidence', 'not specified')}\\n"
        f"Timing provenance: {event['timing_provenance']}\\n"
        f"Audience: {audience}\\n"
        f"Source: {event.get('source_label', event.get('source', 'not specified'))}\\n"
        f"Original X post: {event['url']}"
    )
    return [
        "BEGIN:VEVENT",
        f"UID:codex-reset-{event['id']}@adamcoulteroz.github.io",
        f"DTSTAMP:{ical_time(event['start'])}",
        f"DTSTART:{ical_time(event['start'])}",
        f"DTEND:{ical_time(event['end'])}",
        f"SUMMARY:{escape(title(event))}",
        f"DESCRIPTION:{escape(description)}",
        f"URL:{escape(event['url'])}",
        f"CATEGORIES:{escape(event['classification'])}",
        "STATUS:TENTATIVE" if event["classification"] == "tentative" else "STATUS:CONFIRMED",
        "END:VEVENT",
    ]


def generate(feed: dict) -> str:
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Adam Coulter//Codex Reset Calendar//EN",
        "CALSCALE:GREGORIAN", "METHOD:PUBLISH", "X-WR-CALNAME:Codex Reset Calendar",
        "X-WR-TIMEZONE:UTC", "REFRESH-INTERVAL;VALUE=DURATION:PT1H", "X-PUBLISHED-TTL:PT1H",
    ]
    for event in normalized_events(feed):
        lines.extend(vevent(event))
    lines.append("END:VCALENDAR")
    return "\r\n".join(part for line in lines for part in fold(line)) + "\r\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    args = parser.parse_args()
    feed = json.loads(args.input.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(generate(feed).encode("utf-8"))


if __name__ == "__main__":
    main()
