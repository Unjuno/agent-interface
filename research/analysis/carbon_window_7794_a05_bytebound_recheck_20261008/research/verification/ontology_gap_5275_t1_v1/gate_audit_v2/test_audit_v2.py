"""Construction controls only; never execute the frozen candidate or runner."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from audit_v2 import audit_payload

SOURCE = Path(__file__).resolve().parents[1]


class GateAuditTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads((SOURCE / "FORMAL-01.json").read_text())
        self.corpus = json.loads((SOURCE / "corpus.json").read_text())
        self.identity = dict(self.raw["source_identity"])

    def test_original_retained_evidence_is_valid(self):
        r = audit_payload(self.raw, self.corpus, self.identity)
        self.assertTrue(r["integrity_pass"], r)
        self.assertEqual(r["scientific_disposition"], "PASS_SCOPED_LEXICAL_BOUNDARY")

    def test_empty_gates_cannot_vacuously_certify_pass(self):
        self.raw["gates"] = {}
        r = audit_payload(self.raw, self.corpus, self.identity)
        self.assertFalse(r["integrity_pass"], r)
        self.assertIn("gates", r["errors"])

    def test_each_gate_requires_exact_boolean_value(self):
        for key in self.raw["gates"]:
            for value in (False, 1, "true", None):
                with self.subTest(key=key, value=value):
                    changed = copy.deepcopy(self.raw)
                    changed["gates"][key] = value
                    r = audit_payload(changed, self.corpus, self.identity)
                    self.assertFalse(r["integrity_pass"], r)
                    self.assertIn("gates", r["errors"])

    def test_gate_key_set_is_complete_and_closed(self):
        changed = copy.deepcopy(self.raw)
        changed.pop("gates")
        self.assertFalse(audit_payload(changed, self.corpus, self.identity)["integrity_pass"])
        for key in self.raw["gates"]:
            changed = copy.deepcopy(self.raw)
            del changed["gates"][key]
            self.assertFalse(audit_payload(changed, self.corpus, self.identity)["integrity_pass"])
        changed = copy.deepcopy(self.raw)
        changed["gates"]["undeclared_gate"] = True
        self.assertFalse(audit_payload(changed, self.corpus, self.identity)["integrity_pass"])

    def test_coherently_flipped_gate_and_verdict_are_rejected(self):
        changed = copy.deepcopy(self.raw)
        changed["gates"]["combined_zero_ood_false_pass"] = False
        changed["disposition"] = "FAIL_LEXICAL_BOUNDARY"
        r = audit_payload(changed, self.corpus, self.identity)
        self.assertFalse(r["integrity_pass"])
        self.assertIn("gates", r["errors"])
        self.assertIn("disposition", r["errors"])

    def test_coherent_falsifying_evidence_remains_valid_fail(self):
        # Hand-constructed TEST FIXTURE, not a new scientific measurement.
        # One supported description uses only words absent from training.
        corpus = copy.deepcopy(self.corpus)
        corpus["evaluation"][0]["task_summary"] = "quasar nebula"
        identity = dict(self.identity)
        identity["corpus_sha256"] = hashlib.sha256(json.dumps(corpus, sort_keys=True).encode()).hexdigest()
        raw = copy.deepcopy(self.raw)
        raw["source_identity"] = identity
        raw["rows"][0].update(lexical_oov_fraction=1.0, lexical_only="UNKNOWN_CHECK_REQUIRED", combined="UNKNOWN_CHECK_REQUIRED")
        for arm in ("lexical_only", "combined"):
            raw["arms"][arm].update(false_abstain_iid=1, false_abstain_ids=["iid-save-paraphrase"], iid_abstention_rate=1/6)
        raw["gates"]["combined_zero_iid_false_abstention"] = False
        raw["disposition"] = "FAIL_LEXICAL_BOUNDARY"
        result = audit_payload(raw, corpus, identity)
        self.assertTrue(result["integrity_pass"], result)
        self.assertEqual(result["scientific_disposition"], "FAIL_LEXICAL_BOUNDARY")
        # Truthful FAIL may not be relabeled PASS by submitting all-true gates.
        raw["gates"] = dict(self.raw["gates"])
        raw["disposition"] = "PASS_SCOPED_LEXICAL_BOUNDARY"
        result = audit_payload(raw, corpus, identity)
        self.assertFalse(result["integrity_pass"], result)
        self.assertIn("gates", result["errors"])
        self.assertIn("disposition", result["errors"])

    def test_malformed_inputs_fail_closed(self):
        for field, value in (("gates", []), ("gates", None), ("rows", []), ("rows", None), ("counts", {}), ("arms", {})):
            with self.subTest(field=field, value=value):
                changed = copy.deepcopy(self.raw)
                changed[field] = value
                self.assertFalse(audit_payload(changed, self.corpus, self.identity)["integrity_pass"])

    def test_nonfinite_scores_and_boolean_numbers_are_rejected(self):
        for value in (float("nan"), float("inf"), False):
            changed = copy.deepcopy(self.raw)
            changed["rows"][0]["lexical_oov_fraction"] = value
            self.assertFalse(audit_payload(changed, self.corpus, self.identity)["integrity_pass"])

    def test_row_and_arm_corruption_are_rejected(self):
        changes = [
            lambda r: r["rows"][0].update(oracle_unknown=True),
            lambda r: r["rows"][0].update(combined="UNKNOWN_CHECK_REQUIRED"),
            lambda r: r["arms"]["combined"].update(ood_recall=0.5),
            lambda r: r["counts"].update(cases=12),
        ]
        for change in changes:
            changed = copy.deepcopy(self.raw)
            change(changed)
            self.assertFalse(audit_payload(changed, self.corpus, self.identity)["integrity_pass"])


if __name__ == "__main__":
    unittest.main()
