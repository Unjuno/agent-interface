"""Mutation tests for C02 admission/keymap temporal binding."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

import audit_temporal_v2 as audit_v2
from audit_temporal_v2 import build_report
from test_audit import make_fixture


class TemporalBindingTests(unittest.TestCase):
    def setUp(self):
        roots = (audit_v2.ROOT, audit_v2.parent_audit.ROOT)
        self.addCleanup(setattr, audit_v2, "ROOT", roots[0])
        self.addCleanup(setattr, audit_v2.parent_audit, "ROOT", roots[1])

    def _fixture(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        raw, cases, freeze, started, environment = make_fixture(Path(temp.name))
        # Times are [pre finish, admitted, ack, post start, post finish].
        for index, occurrence in enumerate(raw["occurrences"]):
            offset = index * 100
            raw["events"][index * 2]["admitted_ns"] = 12 + offset
            raw["events"][index * 2]["input_ack_ns"] = 15 + offset
            raw["events"][index * 2]["valid_until_ns"] = 40 + offset
        return temp, raw, cases, freeze, started, environment

    def test_ordered_admission_and_ack_inside_down_witness_pass(self):
        _, raw, cases, _, _, _ = self._fixture()
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertTrue(result["all_occurrences_temporally_bound"], result)

    def test_admission_before_pre_down_fails(self):
        _, raw, cases, _, _, _ = self._fixture()
        raw["events"][0]["admitted_ns"] = 9
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])

    def test_ack_after_post_down_sample_fails(self):
        _, raw, cases, _, _, _ = self._fixture()
        raw["events"][0]["input_ack_ns"] = 22
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])

    def test_admission_after_down_witness_fails(self):
        _, raw, cases, _, _, _ = self._fixture()
        raw["events"][0]["admitted_ns"] = 22
        raw["events"][0]["input_ack_ns"] = 23
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])

    def test_missing_or_duplicate_admission_fails(self):
        _, raw, cases, _, _, _ = self._fixture()
        del raw["events"][0]["input_ack_ns"]
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])

    def test_temporal_audit_rejects_missing_times_accepted_by_parent_audit(self):
        temp, raw, cases, freeze, started, environment = self._fixture()
        previous_root = audit_v2.parent_audit.ROOT
        audit_v2.parent_audit.ROOT = Path(temp.name)
        self.addCleanup(setattr, audit_v2.parent_audit, "ROOT", previous_root)
        for event in raw["events"]:
            event.pop("admitted_ns", None)
            event.pop("input_ack_ns", None)
        parent_checks = audit_v2.parent_audit.evaluate(
            raw, cases, freeze, started, environment)
        self.assertTrue(all(parent_checks.values()), parent_checks)
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])

    def test_duplicate_admission_fails(self):
        _, raw, cases, _, _, _ = self._fixture()
        raw["events"].append(copy.deepcopy(raw["events"][0]))
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])

    def test_ack_at_or_after_lease_deadline_fails(self):
        _, raw, cases, _, _, _ = self._fixture()
        raw["events"][0]["valid_until_ns"] = 15
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])

    def test_down_sample_at_lease_deadline_fails(self):
        _, raw, cases, _, _, _ = self._fixture()
        raw["events"][0]["valid_until_ns"] = 21
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])

    def test_cross_occurrence_timestamps_fail(self):
        _, raw, cases, _, _, _ = self._fixture()
        raw["events"][0]["admitted_ns"] = 112
        raw["events"][0]["input_ack_ns"] = 115
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])

    def test_malformed_occurrence_or_event_fails_closed(self):
        _, raw, cases, _, _, _ = self._fixture()
        raw["events"].append(None)
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])
        _, raw, cases, _, _, _ = self._fixture()
        raw["occurrences"][0] = None
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])

    def test_empty_occurrence_set_fails(self):
        result = audit_v2.evaluate_temporal_binding(
            {"occurrences": [], "events": []}, {"occurrences": 2, "key": "w"})
        self.assertFalse(result["all_occurrences_temporally_bound"])

    def test_full_report_fails_closed_on_malformed_parent_event(self):
        temp, raw, cases, freeze, started, environment = self._fixture()
        root = Path(temp.name)
        previous_roots = (audit_v2.ROOT, audit_v2.parent_audit.ROOT)
        audit_v2.ROOT = root
        audit_v2.parent_audit.ROOT = root
        self.addCleanup(setattr, audit_v2, "ROOT", previous_roots[0])
        self.addCleanup(setattr, audit_v2.parent_audit, "ROOT", previous_roots[1])
        raw["events"].append(None)
        for name, value in (("FREEZE.json", freeze), ("ENVIRONMENT.json", environment),
                            ("candidate.raw.json", raw), ("cases.json", cases)):
            (root / name).write_text(json.dumps(value), encoding="utf-8")
        report = build_report(raw, cases, freeze, started, environment)
        self.assertFalse(report["checks"]["parent_evaluator_completed"])
        self.assertFalse(report["checks"]["admission_timestamps_within_key_down_witness"])
        self.assertEqual(report["gate"], "FAIL_OR_HOLD_V39_KEYMAP_TEMPORAL_BINDING")
        self.assertIn("AttributeError", report["parent_evaluator_error"])

    def _install_main_inputs(self, root, raw, cases, freeze, started, environment):
        for name, value in (("FREEZE.json", freeze), ("ENVIRONMENT.json", environment),
                            ("candidate.raw.json", raw), ("cases.json", cases),
                            ("candidate.started.json", started)):
            (root / name).write_text(json.dumps(value), encoding="utf-8")
        audit_v2.ROOT = root
        audit_v2.parent_audit.ROOT = root

    def test_main_replaces_stale_pass_when_any_json_root_is_not_an_object(self):
        names = ("candidate.raw.json", "cases.json", "FREEZE.json",
                 "candidate.started.json", "ENVIRONMENT.json")
        for malformed_name in names:
            with self.subTest(document=malformed_name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                _, raw, cases, freeze, started, environment = self._fixture()
                self._install_main_inputs(root, raw, cases, freeze, started, environment)
                (root / malformed_name).write_text("null", encoding="utf-8")
                output = root / "AUDIT_V2.json"
                output.write_text('{"gate":"PASS_V39_XVFB_KEYMAP_TEMPORAL_BINDING_SCOPED"}\n',
                                  encoding="utf-8")
                with self.assertRaises(SystemExit) as raised:
                    audit_v2.main()
                report = json.loads(output.read_text(encoding="utf-8"))
                self.assertEqual(raised.exception.code, 1)
                self.assertEqual(report["gate"], "FAIL_OR_HOLD_V39_KEYMAP_TEMPORAL_BINDING")
                self.assertIn("ValueError", report["error"])

    def test_main_replaces_stale_pass_when_input_json_is_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, raw, cases, freeze, started, environment = self._fixture()
            self._install_main_inputs(root, raw, cases, freeze, started, environment)
            (root / "candidate.raw.json").write_text("{", encoding="utf-8")
            output = root / "AUDIT_V2.json"
            output.write_text('{"gate":"PASS_V39_XVFB_KEYMAP_TEMPORAL_BINDING_SCOPED"}\n',
                              encoding="utf-8")
            with self.assertRaises(SystemExit) as raised:
                audit_v2.main()
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(raised.exception.code, 1)
            self.assertEqual(report["gate"], "FAIL_OR_HOLD_V39_KEYMAP_TEMPORAL_BINDING")
            self.assertIn("JSONDecodeError", report["error"])

    def test_main_passes_valid_fixture_and_replaces_stale_report(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, raw, cases, freeze, started, environment = self._fixture()
            self._install_main_inputs(root, raw, cases, freeze, started, environment)
            output = root / "AUDIT_V2.json"
            output.write_text('{"gate":"stale"}\n', encoding="utf-8")
            with self.assertRaises(SystemExit) as raised:
                audit_v2.main()
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(raised.exception.code, 0)
            self.assertEqual(report["gate"], audit_v2.PASS)
            self.assertEqual(report["failed_checks"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
