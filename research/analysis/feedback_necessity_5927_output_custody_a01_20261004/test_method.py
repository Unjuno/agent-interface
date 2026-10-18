from __future__ import annotations

import copy
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import auditor
import candidate


CASES = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))["cases"]


class EpistemicControlsTests(unittest.TestCase):
    def test_action_intent_and_dispatch_ack_do_not_prove_effect(self):
        row = candidate.analyze(CASES[0])
        self.assertEqual(row["minimum_additional_exchanges"], 1)
        self.assertEqual(row["minimum_additional_channel_set"], ["independent_persistence_receipt"])
        self.assertEqual(row["current_transcript_partitions"][0]["common_safe_actions"], [])

    def test_fresh_local_typed_receipt_makes_another_exchange_unnecessary(self):
        row = candidate.analyze(CASES[1])
        self.assertEqual(row["minimum_additional_exchanges"], 0)
        self.assertEqual(row["minimum_additional_channel_set"], [])
        self.assertEqual(len(row["current_transcript_partitions"]), 2)

    def test_raw_only_auditor_reconstructs_both_controls(self):
        payload = candidate.run(CASES)
        result = auditor.audit(CASES, payload)
        self.assertEqual(result["status"], "PASS_RAW_AUDIT")
        self.assertEqual(result["errors"], [])

    def test_auditor_rejects_false_zero_exchange_claim(self):
        payload = candidate.run(CASES)
        payload["results"][0]["minimum_additional_exchanges"] = 0
        result = auditor.audit(CASES, payload)
        self.assertEqual(result["status"], "FAIL_RAW_AUDIT")

    def test_stale_local_receipt_cannot_justify_zero_exchange(self):
        stale = copy.deepcopy(CASES[1])
        stale["initial_transcript"][-1]["fresh"] = False
        row = candidate.analyze(stale)
        self.assertEqual(row["decision"], "HOLD_NO_FRESH_SAFE_POLICY")
        self.assertIsNone(row["minimum_additional_exchanges"])

    def test_undeclared_channel_fails_closed(self):
        corrupt = copy.deepcopy(CASES[0])
        corrupt["channels"][0]["declared"] = False
        with self.assertRaisesRegex(ValueError, "undeclared"):
            candidate.analyze(corrupt)

    def test_safe_action_oracle_mismatch_fails_independent_audit(self):
        corrupt = copy.deepcopy(CASES[0])
        corrupt["worlds"][0]["oracle_safe_progress_actions"] = ["continue_anyway"]
        result = auditor.audit([corrupt], candidate.run([corrupt]))
        self.assertEqual(result["status"], "FAIL_RAW_AUDIT")
        self.assertTrue(any("oracle mismatch" in error for error in result["errors"]))

    def test_candidate_cli_refuses_to_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "candidate.json"
            output.write_text("first candidate\n", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    candidate.main(["--cases", str(Path(__file__).parent / "cases.json"),
                                    "--out", str(output)])
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(output.read_text(encoding="utf-8"), "first candidate\n")

    def test_auditor_cli_refuses_to_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            candidate_path = directory / "candidate.json"
            candidate_path.write_text(json.dumps(candidate.run(CASES)), encoding="utf-8")
            output = directory / "audit.json"
            output.write_text("first audit\n", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    auditor.main(["--cases", str(Path(__file__).parent / "cases.json"),
                                  "--candidate", str(candidate_path), "--out", str(output)])
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(output.read_text(encoding="utf-8"), "first audit\n")


if __name__ == "__main__":
    unittest.main()
