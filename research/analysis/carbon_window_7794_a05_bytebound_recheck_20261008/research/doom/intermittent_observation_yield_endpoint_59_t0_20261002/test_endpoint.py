"""Frozen endpoint regression test; standard library only."""
import json
import unittest
from pathlib import Path

from candidate import decide


class CaptureEndpointTest(unittest.TestCase):
    def test_closed_interval_boundaries_match_frozen_expectations(self):
        fixture = json.loads((Path(__file__).parent / "fixture.json").read_text(encoding="utf-8"))
        for event in fixture["events"]:
            with self.subTest(event=event["id"]):
                self.assertEqual(
                    event["expected"],
                    decide(fixture["source_sequence"], fixture["source_health"], event),
                )


if __name__ == "__main__":
    unittest.main()
