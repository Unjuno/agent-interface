"""Regression checks for the frozen replay enumerator's acceptance gate."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze


class ReplayAnalysisGateTests(unittest.TestCase):
    def mutated_readout(self, path):
        readout = json.loads(analyze.SOURCE.read_text(encoding="utf-8"))
        sample = next(
            row for row in readout["samples"]
            if row["game_clock"] == "0047.0s"
            and row["phase"] == "MODEL THINKING + LOCAL COVER")
        sample["health"] = 97
        path.write_text(json.dumps(readout), encoding="utf-8")
        return path

    def test_changed_retained_source_is_refused_by_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.mutated_readout(root / "VISUAL_READOUT.json")
            with patch.object(analyze, "SOURCE", source), patch.object(
                    analyze, "OUT", root / "RESULT.json"):
                with self.assertRaisesRegex(ValueError, "source digest mismatch"):
                    analyze.main()

    def test_newly_pinned_source_recomputes_the_event_distribution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.mutated_readout(root / "VISUAL_READOUT.json")
            accepted_digest = hashlib.sha256(source.read_bytes()).hexdigest()
            with patch.object(analyze, "SOURCE", source), patch.object(
                    analyze, "OUT", root / "RESULT.json"), patch.object(
                        analyze, "EXPECTED_SOURCE_SHA256", accepted_digest,
                        create=True):
                analyze.main()
            result = json.loads((root / "RESULT.json").read_text(encoding="utf-8"))
            expected = {"47.0": 354, "53.6": 114, "54.8": 222,
                        "never_during_wait": 1410}
            enumeration = result["enumeration"]
            self.assertEqual(enumeration["first_sample_distribution"], expected)
            self.assertEqual(
                enumeration["independent_threshold_oracle"].get(
                    "first_sample_distribution", {}), expected)

    def test_frozen_source_reproduces_recorded_result(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "RESULT.json"
            with patch.object(analyze, "OUT", output):
                analyze.main()
            actual = json.loads(output.read_text(encoding="utf-8"))
            recorded = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
            self.assertEqual(
                actual["source_sha256"],
                "610b77f02302150f26c7de81e46bcba5e8a4fc646d6195442c86db93c6305724")
            self.assertEqual(
                actual["enumeration"]["first_sample_distribution"],
                {"47.0": 468, "54.8": 222, "never_during_wait": 1410})
            self.assertEqual(actual, recorded)


if __name__ == "__main__":
    unittest.main()
