import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "scripts"))
import generate_ics


class GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.feed = json.loads((pathlib.Path(__file__).parent / "fixture.json").read_text())

    def test_filter_classify_and_deduplicate(self):
        events = generate_ics.normalized_events(self.feed)
        self.assertEqual([event["id"] for event in events], ["100", "200", "300"])
        self.assertEqual([event["classification"] for event in events], ["confirmed", "banked", "tentative"])

    def test_timestamp_precedence(self):
        event = self.feed["events"][2]
        start, end, provenance = generate_ics.event_times(event)
        self.assertEqual(provenance, "official_window")
        self.assertEqual(generate_ics.ical_time(start), "20260103T020000Z")
        self.assertEqual(generate_ics.ical_time(end), "20260103T030000Z")

    def test_stable_ics_crlf_escaping_folding_and_order(self):
        text = generate_ics.generate(self.feed)
        self.assertTrue(text.startswith("BEGIN:VCALENDAR\r\n"))
        self.assertTrue(text.endswith("END:VCALENDAR\r\n"))
        self.assertNotIn("\n", text.replace("\r\n", ""))
        self.assertIn("UID=codex-reset-100@adamcoulteroz.github.io", text)
        self.assertEqual(
            generate_ics.escape("A; comma, slash \\ and newline\ntext."),
            "A\\; comma\\, slash \\\\ and newline\\ntext.",
        )
        self.assertEqual(text, generate_ics.generate(self.feed))
        self.assertTrue(all(len(line.encode("utf-8")) <= 75 for line in text.split("\r\n") if line))

    def test_utf8_octet_folding(self):
        lines = generate_ics.fold("SUMMARY:" + "é" * 50)
        self.assertGreater(len(lines), 1)
        self.assertTrue(all(len(line.encode("utf-8")) <= 75 for line in lines))
        self.assertTrue(all(line.startswith(" ") for line in lines[1:]))


if __name__ == "__main__":
    unittest.main()
