import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import research_soft_event_context_6561 as target


class SoftEventContextConstructionTests(unittest.TestCase):
    def setUp(self):
        self.binding, self.rows, _ = target.fixture()

    def derive(self, row):
        _, state, count, event, now, _, _raw = row
        return target.candidate_context(state, count, event, now, self.binding)

    def audit(self, row):
        _, state, count, event, now, _, _raw = row
        return target.auditor_derive(state, count, event, now, self.binding)

    def test_frozen_rows_match_oracle_and_independent_auditor(self):
        for row in self.rows:
            with self.subTest(row=row[0]):
                actual = self.derive(row)
                self.assertEqual(actual, row[5])
                self.assertEqual(self.audit(row), actual)
                self.assertTrue(target.auditor_verify_context(
                    row[1], row[6], row[4], self.binding, actual))

    def test_none_is_not_unknown(self):
        none = self.derive(self.rows[0])
        unknown = self.derive(self.rows[4])
        self.assertEqual(none["state"], "NONE")
        self.assertEqual(unknown["state"], "UNKNOWN")
        self.assertNotEqual(none, unknown)

    def test_context_is_prompt_serializable_and_authority_free(self):
        for row in self.rows[1:3]:
            context = self.derive(row)
            prompt = target.render_prompt_context(context)
            self.assertIn('"state":"OBSERVED"', prompt)
            self.assertIn('"grants_input_authority":false', prompt)
            self.assertIn('"task_success_verified":false', prompt)

    def test_future_or_current_event_is_unknown(self):
        row = self.rows[1]
        event = copy.deepcopy(row[3])
        for seq in (row[4], row[4] + 1):
            event["sequence"] = seq
            got = target.candidate_context("observed", 1, event, row[4], self.binding)
            audited = target.auditor_derive("observed", 1, event, row[4], self.binding)
            self.assertEqual(got["state"], "UNKNOWN")
            self.assertEqual(got, audited)

    def test_cross_binding_fails_closed(self):
        row = self.rows[1]
        event = copy.deepcopy(row[3])
        event["signal"]["binding"] = {"session": "other"}
        got = target.candidate_context("observed", 1, event, row[4], self.binding)
        self.assertEqual(got["state"], "UNKNOWN")
        self.assertEqual(got, target.auditor_derive("observed", 1, event, row[4], self.binding))

    def test_authority_mutation_is_detected_by_frozen_contract(self):
        context = self.derive(self.rows[1])
        context["grants_input_authority"] = True
        with self.assertRaises(ValueError):
            target.auditor_verify_context("observed", self.rows[1][6],
                                          self.rows[1][4], self.binding, context)

    def test_old_event_substitution_is_detected_from_raw_history(self):
        row = self.rows[2]
        older = copy.deepcopy(row[6][0])
        emitted_old = target.auditor_derive("observed", 3, older, row[4], self.binding)
        with self.assertRaises(ValueError):
            target.auditor_verify_context("observed", row[6], row[4],
                                          self.binding, emitted_old)

    def test_none_cannot_hide_nonempty_monitor_history(self):
        with self.assertRaises(ValueError):
            target.candidate_context("none", 1, self.rows[1][3], 90, self.binding)

    def test_nonfinite_age_and_boolean_health_values_fail_closed(self):
        row = self.rows[1]
        event = copy.deepcopy(row[3])
        event["outcome"]["source_age_ms"] = float("nan")
        actual = target.candidate_context("observed", 1, event, row[4], self.binding)
        self.assertEqual(actual["state"], "UNKNOWN")
        self.assertEqual(actual, target.auditor_derive("observed", 1, event, row[4], self.binding))

    def test_oversized_guard_identifier_fails_closed(self):
        row = self.rows[1]
        event = copy.deepcopy(row[3])
        event["outcome"]["guard_id"] = "g" * 65
        actual = target.candidate_context("observed", 1, event, row[4], self.binding)
        self.assertEqual(actual["state"], "UNKNOWN")
        self.assertEqual(actual, target.auditor_derive("observed", 1, event, row[4], self.binding))

        event = copy.deepcopy(row[3])
        event["outcome"]["source_value"] = True
        actual = target.candidate_context("observed", 1, event, row[4], self.binding)
        self.assertEqual(actual["state"], "UNKNOWN")
        self.assertEqual(actual, target.auditor_derive("observed", 1, event, row[4], self.binding))

    def test_standalone_raw_auditor_accepts_packet_and_rejects_old_event_substitution(self):
        runner = Path(__file__).with_name("run_candidate_soft_event_context_6561.py")
        auditor = Path(__file__).with_name("audit_soft_event_context_6561.py")
        with tempfile.TemporaryDirectory() as temp_dir:
            packet = Path(temp_dir) / "candidate_raw.json"
            candidate = subprocess.run(
                [sys.executable, str(runner), str(packet)],
                capture_output=True, text=True, check=False)
            self.assertEqual(candidate.returncode, 0, candidate.stderr)
            repeated = subprocess.run(
                [sys.executable, str(runner), str(packet)],
                capture_output=True, text=True, check=False)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn("ALREADY_EXISTS", repeated.stderr)
            cases = json.loads(packet.read_text(encoding="utf-8"))["cases"]
            accepted = subprocess.run(
                [sys.executable, str(auditor), str(packet)],
                capture_output=True, text=True, check=False)
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            self.assertIn("PASS_RAW_AUDIT cases=6", accepted.stdout)

            mutated = copy.deepcopy(cases)
            older = mutated[2]["raw_events"][0]
            mutated[2]["context"] = target.auditor_derive(
                "observed", 3, older, mutated[2]["current_sequence"], self.binding)
            mutated[2]["prompt"] = target.render_prompt_context(mutated[2]["context"])
            packet.write_text(json.dumps({"cases": mutated}), encoding="utf-8")
            rejected = subprocess.run(
                [sys.executable, str(auditor), str(packet)],
                capture_output=True, text=True, check=False)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("latest", rejected.stderr.lower())

if __name__ == "__main__":
    unittest.main(verbosity=2)
