import json
import unittest
from pathlib import Path

from contract import evaluate


ROOT = Path(__file__).resolve().parents[1]


class FrozenCorpusConstructionTests(unittest.TestCase):
    def test_fixture_decisions_match_preregistered_finite_gate(self):
        spec = json.loads((ROOT / "spec.json").read_text(encoding="utf-8"))
        corpus = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
        expected = {
            "reference-direct": "CONFORMANT",
            "reference-hidden-batch-retry": "CONFORMANT",
            "forbidden-target-switch": "NONCONFORMANT",
            "forbidden-stale-admission": "NONCONFORMANT",
            "forbidden-unauthorized-admission": "NONCONFORMANT",
            "forbidden-semantic-false-success": "NONCONFORMANT",
            "delayed-unknown-and-explicit-quiescence": "CONFORMANT",
            "missing-output-is-not-quiescence": "UNKNOWN",
        }
        self.assertEqual({c["case_id"] for c in corpus["cases"]}, set(expected))
        for case in corpus["cases"]:
            with self.subTest(case=case["case_id"]):
                self.assertEqual(evaluate(spec, case["trace"])["status"], expected[case["case_id"]])

    def test_same_visible_behavior_can_hide_different_internal_paths(self):
        corpus = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
        cases = {c["case_id"]: c for c in corpus["cases"]}
        direct = cases["reference-direct"]["trace"]
        hidden = cases["reference-hidden-batch-retry"]["trace"]
        self.assertNotEqual(direct, hidden)
        self.assertEqual(
            [(x["input"], x["outputs"]) for x in direct],
            [(x["input"], x["outputs"]) for x in hidden],
        )


if __name__ == "__main__":
    unittest.main()
