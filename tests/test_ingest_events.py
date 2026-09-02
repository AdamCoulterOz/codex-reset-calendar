import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "scripts"))
import ingest_events


class IngestTests(unittest.TestCase):
    def test_merge_uses_id_and_rejects_non_reset_and_bad_source(self):
        existing = {"events": [{"id": "1", "summary": "old", "announced_at": "2026-01-01T00:00:00Z"}]}
        incoming = [
            {"id": "1", "type": "reset", "scope": "global", "source": "archive", "confidence": "high", "summary": "new", "url": "https://x.com/a/status/1", "announced_at": "2026-01-02T00:00:00Z"},
            {"id": "2", "type": "limits", "scope": "global", "summary": "no", "url": "https://x.com/a/status/2", "announced_at": "2026-01-02T00:00:00Z"},
            {"id": "3", "type": "reset", "scope": "global", "source": "archive", "confidence": "high", "summary": "no", "url": "https://example.com/3", "announced_at": "2026-01-02T00:00:00Z"},
        ]
        merged = ingest_events.merge(existing, incoming)
        self.assertEqual([event["id"] for event in merged["events"]], ["1"])
        self.assertEqual(merged["events"][0]["summary"], "new")
