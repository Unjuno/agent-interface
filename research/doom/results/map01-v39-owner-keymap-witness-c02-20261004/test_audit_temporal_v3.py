"""Fail-closed root-shape regression for the additive C02 audit v3."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import audit_temporal_v3 as audit_v3
from test_audit import make_fixture


class TemporalAuditV3Tests(unittest.TestCase):
    def test_valid_temporal_witness_keeps_scoped_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw, cases, freeze, started, environment = make_fixture(root)
            previous_roots = (audit_v3.ROOT, audit_v3.parent_audit.ROOT)
            audit_v3.ROOT = root
            audit_v3.parent_audit.ROOT = root
            self.addCleanup(setattr, audit_v3, "ROOT", previous_roots[0])
            self.addCleanup(setattr, audit_v3.parent_audit, "ROOT", previous_roots[1])
            for index in range(2):
                offset = index * 100
                raw["events"][index * 2]["admitted_ns"] = 12 + offset
                raw["events"][index * 2]["input_ack_ns"] = 15 + offset
                raw["events"][index * 2]["valid_until_ns"] = 40 + offset
            for name, value in (("candidate.raw.json", raw), ("cases.json", cases),
                                ("FREEZE.json", freeze),
                                ("candidate.started.json", started),
                                ("ENVIRONMENT.json", environment)):
                (root / name).write_text(json.dumps(value), encoding="utf-8")

            report = audit_v3.build_report(raw, cases, freeze, started, environment)

            self.assertEqual(report["gate"], audit_v3.PASS)
            self.assertTrue(all(report["checks"].values()), report["checks"])

    def test_non_object_input_roots_fail_closed(self):
        result = audit_v3.evaluate_temporal_binding(None, None)
        self.assertFalse(result["all_occurrences_temporally_bound"])
        self.assertEqual(result["reason"], "raw_root_not_object")

        result = audit_v3.evaluate_temporal_binding({}, None)
        self.assertFalse(result["all_occurrences_temporally_bound"])
        self.assertEqual(result["reason"], "cases_root_not_object")

    def test_null_raw_root_replaces_prior_pass_without_touching_v2_report(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, cases, freeze, started, environment = make_fixture(root)
            previous_roots = (audit_v3.ROOT, audit_v3.parent_audit.ROOT)
            audit_v3.ROOT = root
            audit_v3.parent_audit.ROOT = root
            self.addCleanup(setattr, audit_v3, "ROOT", previous_roots[0])
            self.addCleanup(setattr, audit_v3.parent_audit, "ROOT", previous_roots[1])
            (root / "candidate.raw.json").write_text("null", encoding="utf-8")
            (root / "candidate.started.json").write_text(
                json.dumps(started), encoding="utf-8")
            (root / "cases.json").write_text(json.dumps(cases), encoding="utf-8")
            (root / "FREEZE.json").write_text(json.dumps(freeze), encoding="utf-8")
            (root / "ENVIRONMENT.json").write_text(
                json.dumps(environment), encoding="utf-8")
            prior_v2 = {"schema": "map01-v39-owner-keymap-witness-audit-v2",
                        "gate": "PASS_V39_XVFB_KEYMAP_TEMPORAL_BINDING_SCOPED"}
            (root / "AUDIT_V2.json").write_text(
                json.dumps(prior_v2), encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    audit_v3.main()

            self.assertEqual(raised.exception.code, 1)
            report = json.loads((root / "AUDIT_V3.json").read_text(encoding="utf-8"))
            self.assertEqual(report["gate"],
                             "FAIL_OR_HOLD_V39_KEYMAP_TEMPORAL_BINDING_V3")
            self.assertFalse(report["checks"]["parent_evaluator_completed"])
            self.assertFalse(
                report["checks"]["admission_timestamps_within_key_down_witness"])
            self.assertEqual(json.loads((root / "AUDIT_V2.json").read_text(encoding="utf-8")),
                             prior_v2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
