import copy
import json
import tempfile
import unittest
import urllib.parse
import urllib.request
from pathlib import Path

from visual_memory_fixture_v1 import Fixture
from visual_memory_model_v1 import validate


class Tests(unittest.TestCase):
    def test_positive_decision(self):
        value = {"format": "visual-memory-target-decision-v1", "status": "target_reference",
                 "x": 10, "y": 20, "reason": "matched", "memory_use": "supporting"}
        self.assertEqual(validate(value), value)

    def test_abstention(self):
        value = {"format": "visual-memory-target-decision-v1", "status": "needs_decision",
                 "x": 0, "y": 0, "reason": "ambiguous", "memory_use": "none"}
        self.assertEqual(validate(value), value)

    def test_bad_abstention_coordinate(self):
        value = {"format": "visual-memory-target-decision-v1", "status": "needs_decision",
                 "x": 1, "y": 0, "reason": "ambiguous", "memory_use": "none"}
        with self.assertRaises(ValueError): validate(value)

    def test_outside_frame(self):
        value = {"format": "visual-memory-target-decision-v1", "status": "target_reference",
                 "x": 1280, "y": 20, "reason": "matched", "memory_use": "supporting"}
        with self.assertRaises(ValueError): validate(value)

    def test_fixture_oracle_separates_submit_and_decoy(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary), 218)
            try:
                urllib.request.urlopen(fixture.url("shifted")).read()
                data = urllib.parse.urlencode({"value": fixture.token}).encode()
                urllib.request.urlopen(urllib.request.Request(
                    fixture.url("shifted").replace("/shifted", "/submit/shifted"), data=data)).read()
                with self.assertRaises(urllib.error.HTTPError):
                    urllib.request.urlopen(urllib.request.Request(
                        fixture.url("shifted").replace("/shifted", "/decoy/shifted"), data=data)).read()
                rows = fixture.records(); self.assertTrue(rows[0]["exact"])
                self.assertEqual(rows[1]["kind"], "decoy"); self.assertFalse(rows[1]["exact"])
            finally: fixture.close()


if __name__ == "__main__": unittest.main()
