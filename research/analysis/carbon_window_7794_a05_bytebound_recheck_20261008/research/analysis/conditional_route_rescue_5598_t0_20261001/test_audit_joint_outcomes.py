import json
import tempfile
import unittest
from pathlib import Path

from audit_joint_outcomes import summarize


class PairedOutcomeSummaryTests(unittest.TestCase):
    def run_rows(self, rows):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inputs.jsonl"
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            return summarize(path)

    @staticmethod
    def row(a, b, regime="fixture", incident=None):
        return {"primary": {"route-a": a, "route-b": b}, "regime": regime, "incident": incident}

    def test_matches_and_conditions_on_same_row(self):
        result = self.run_rows([self.row("severe", "ok"), self.row("ok", "severe")])
        group = result["regimes"]["fixture"]
        self.assertEqual(group["a_non_ok"], 1)
        self.assertEqual(group["b_ok_given_a_non_ok"], 1)
        self.assertEqual(group["b_severe_given_a_non_ok"], 0)

    def test_non_ok_includes_transient_and_severe(self):
        group = self.run_rows([self.row("transient", "severe")])["regimes"]["fixture"]
        self.assertEqual(group["a_non_ok"], 1)
        self.assertEqual(group["b_severe_given_a_non_ok"], 1)

    def test_severe_condition_is_reported_separately(self):
        group = self.run_rows([self.row("transient", "ok"), self.row("catastrophic", "ok")])["regimes"]["fixture"]
        self.assertEqual(group["a_severe"], 1)
        self.assertEqual(group["b_ok_given_a_severe"], 1)

    def test_incident_stratum_requires_non_null_identity(self):
        rows = [self.row("severe", "ok", incident="incident-1"), self.row("severe", "severe")]
        group = self.run_rows(rows)["regimes"]["fixture"]
        self.assertEqual(group["incident_rows"], 1)
        self.assertEqual(group["incident_a_non_ok"], 1)
        self.assertEqual(group["incident_b_ok_given_a_non_ok"], 1)

    def test_empty_condition_denominator_is_null(self):
        group = self.run_rows([self.row("ok", "ok")])["regimes"]["fixture"]
        self.assertIsNone(group["p_b_ok_given_a_non_ok"])
        self.assertIsNone(group["p_b_severe_given_a_non_ok_and_incident"])

    def test_input_hash_is_over_exact_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inputs.jsonl"
            payload = b'{"primary":{"route-a":"ok","route-b":"ok"},"regime":"fixture","incident":null}\n'
            path.write_bytes(payload)
            result = summarize(path)
        import hashlib
        self.assertEqual(result["inputs_sha256"], hashlib.sha256(payload).hexdigest())


if __name__ == "__main__":
    unittest.main()

