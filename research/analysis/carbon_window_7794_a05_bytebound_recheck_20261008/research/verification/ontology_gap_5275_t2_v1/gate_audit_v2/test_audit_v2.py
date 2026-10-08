"""T2-specific maintenance controls; no scientific candidate/runner execution."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from audit_v2 import audit_payload

SOURCE = Path(__file__).resolve().parents[1]


class T2GateAuditTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads((SOURCE / "FORMAL-01.json").read_text())
        self.corpus = json.loads((SOURCE / "corpus.json").read_text())
        self.identity = dict(self.raw["source_identity"])

    def check(self, raw):
        return audit_payload(raw, self.corpus, self.identity)

    def test_original_negative_evidence_is_integrity_valid_fail(self):
        r = self.check(self.raw)
        self.assertTrue(r["integrity_pass"], r)
        self.assertEqual(r["scientific_disposition"], "FAIL_HELDOUT_LEXICAL_BOUNDARY")

    def test_corrupted_count_gate_is_rejected(self):
        self.raw["gates"]["corpus_counts_fixed"] = False
        r = self.check(self.raw)
        self.assertFalse(r["integrity_pass"], r)
        self.assertIn("gates", r["errors"])

    def test_exact_gate_keys_required(self):
        changed = copy.deepcopy(self.raw)
        changed["gates"] = {}
        self.assertFalse(self.check(changed)["integrity_pass"])
        changed.pop("gates")
        self.assertFalse(self.check(changed)["integrity_pass"])
        for key in self.raw["gates"]:
            changed = copy.deepcopy(self.raw)
            del changed["gates"][key]
            self.assertFalse(self.check(changed)["integrity_pass"])
        changed = copy.deepcopy(self.raw)
        changed["gates"]["undeclared_gate"] = False
        self.assertFalse(self.check(changed)["integrity_pass"])

    def test_exact_boolean_gate_values_required(self):
        for key, expected in self.raw["gates"].items():
            for value in (not expected, int(expected), str(expected), None):
                with self.subTest(key=key, value=value):
                    changed = copy.deepcopy(self.raw)
                    changed["gates"][key] = value
                    result = self.check(changed)
                    self.assertFalse(result["integrity_pass"], result)
                    self.assertIn("gates", result["errors"])

    def test_false_pass_relabeling_is_rejected(self):
        self.raw["gates"] = {k: True for k in self.raw["gates"]}
        self.raw["disposition"] = "PASS_HELDOUT_LEXICAL_BOUNDARY"
        result = self.check(self.raw)
        self.assertFalse(result["integrity_pass"])
        self.assertIn("gates", result["errors"])
        self.assertIn("disposition", result["errors"])

    def test_nonfinite_and_boolean_numeric_values_are_rejected(self):
        for value in (float("nan"), float("inf"), False):
            changed = copy.deepcopy(self.raw)
            changed["rows"][0]["lexical_oov_fraction"] = value
            self.assertFalse(self.check(changed)["integrity_pass"])
            changed = copy.deepcopy(self.raw)
            changed["arms"]["combined"]["iid_abstention_rate"] = value
            self.assertFalse(self.check(changed)["integrity_pass"])

    def test_rows_denominators_and_families_are_independent_checks(self):
        changes = [
            lambda x: x["counts"].update(cases=15),
            lambda x: x["arms"]["combined"].update(iid=7),
            lambda x: x["rows"][0].update(combined="PLAN_COVERED"),
            lambda x: x["family_counts"]["combined"]["iid_supported_heldout_surface"].update(abstained=0),
            lambda x: x.update(rows=[]),
        ]
        for change in changes:
            changed = copy.deepcopy(self.raw)
            change(changed)
            self.assertFalse(self.check(changed)["integrity_pass"])

    def test_honest_synthetic_pass_is_not_hardcoded_to_fail(self):
        # Explicit TEST-ONLY reference: known-token supported text; OOV OOD text.
        # These are authored control data, not measurements or a new allocation.
        corpus, raw = copy.deepcopy(self.corpus), copy.deepcopy(self.raw)
        for case, row in zip(corpus["evaluation"], raw["rows"]):
            case["task_summary"] = "quasar nebula" if case["oracle_unknown"] else "save draft"
            row["lexical_oov_fraction"] = 1.0 if case["oracle_unknown"] else 0.0
            row["lexical_only"] = row["combined"] = "UNKNOWN_CHECK_REQUIRED" if case["oracle_unknown"] else "PLAN_COVERED"
        for arm in ("lexical_only", "combined"):
            raw["arms"][arm].update(false_pass_ids=[], false_pass_ood=0, false_abstain_ids=[], false_abstain_iid=0, ood_recall=1.0, iid_abstention_rate=0.0)
        for arm in raw["family_counts"]:
            families = {}
            for row in raw["rows"]:
                group = families.setdefault(row["family"], [])
                group.append(row)
            raw["family_counts"][arm] = {
                family: {"cases": len(rows), "oracle_unknown": sum(int(r["oracle_unknown"]) for r in rows),
                    "abstained": sum(int(r[arm] == "UNKNOWN_CHECK_REQUIRED") for r in rows),
                    "false_pass": sum(int(r["oracle_unknown"] and r[arm] != "UNKNOWN_CHECK_REQUIRED") for r in rows),
                    "mean_oov_fraction": sum(r["lexical_oov_fraction"] for r in rows) / len(rows)}
                for family, rows in families.items()
            }
        identity = dict(self.identity)
        identity["corpus_sha256"] = hashlib.sha256(json.dumps(corpus, sort_keys=True).encode()).hexdigest()
        raw["source_identity"] = identity
        raw["gates"] = {k: True for k in raw["gates"]}
        raw["disposition"] = "PASS_HELDOUT_LEXICAL_BOUNDARY"
        result = audit_payload(raw, corpus, identity)
        self.assertTrue(result["integrity_pass"], result)
        self.assertEqual(result["scientific_disposition"], "PASS_HELDOUT_LEXICAL_BOUNDARY")


if __name__ == "__main__":
    unittest.main()
