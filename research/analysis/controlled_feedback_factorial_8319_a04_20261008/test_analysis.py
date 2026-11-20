import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import analyze
import audit


def rows_fixture():
    rows = []
    for updater in analyze.UPDATERS:
        for feedback in analyze.FEEDBACKS:
            for seed in analyze.SEEDS:
                u = updater == "STRATUM_PATCH"
                f = feedback == "FULL"
                dev = 16 + int(u) + int(f) * (2 if not u else 1) + seed % 3
                fresh = 16 + int(u) + seed % 2
                rows.append({
                    "updater": updater, "feedback": feedback, "seed": seed,
                    "dev_correct": dev, "dev_total": 32,
                    "fresh_correct": fresh, "fresh_total": 32,
                    "optimism": (dev - fresh) / 32,
                    "query_count": 5, "safety_veto_count": 1,
                    "candidate_locked_before_fresh": True,
                    "raw_released_after_lock": True,
                })
    return rows


class AnalysisContractTests(unittest.TestCase):
    def test_exact_factorial_and_registered_estimands(self):
        result = analyze.summarize(rows_fixture(), "a" * 64)
        self.assertEqual(result["rows"], 400)
        self.assertEqual(result["seeds_per_cell"], 100)
        self.assertEqual(result["interaction_case_minus_stratum_of_feedback_effect"]["dev_accuracy"]["mean_fraction"], "1/32")
        self.assertEqual(result["cell_summaries"]["CASE_PATCH"]["FULL"]["metrics"]["dev_accuracy"]["n"], 100)

    def test_exact_types_protocol_bounds_and_duplicate_frame_rejected(self):
        for mutate in (
            lambda x: x.__setitem__("seed", True),
            lambda x: x.__setitem__("safety_veto_count", True),
            lambda x: x.__setitem__("dev_correct", 33),
            lambda x: x.__setitem__("raw_released_after_lock", False),
        ):
            data = rows_fixture(); mutate(data[0])
            with self.assertRaises(ValueError): analyze.validate_rows(data)
        data = rows_fixture(); data[-1] = dict(data[0])
        with self.assertRaises(ValueError): analyze.validate_rows(data)

    def test_cli_creates_parent_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); raw = root / "raw.json"; out = root / "nested" / "analysis.json"
            source = Path(__file__).parent / "inputs" / "a01_candidate.json"
            raw.write_bytes(source.read_bytes())
            with self.assertRaises(FileNotFoundError): analyze.write_result(raw, out)
            out.parent.mkdir()
            out.write_text("occupied", encoding="utf-8")
            with self.assertRaises(ValueError): analyze.write_result(raw, out)

    def test_analysis_digest_is_enforced_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); raw = root / "raw.json"; out = root / "analysis.json"
            raw.write_text("[]", encoding="utf-8")
            with self.assertRaises(ValueError): analyze.write_result(raw, out)
            self.assertFalse(out.exists())

    def test_independent_auditor_reconstructs_and_rejects_mutations(self):
        raw = rows_fixture()
        reconstructed = audit.rebuild(raw, "a" * 64)
        self.assertEqual(reconstructed["rows"], 400)
        mutations = audit.mutation_probes(reconstructed)
        self.assertEqual(len(mutations), 6)
        self.assertTrue(all(probe != reconstructed for probe in mutations))


if __name__ == "__main__":
    unittest.main()
