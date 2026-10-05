import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "inputs" / "a02_candidate_raw.json"
BASELINE_AUDIT_PATH = ROOT / "inputs" / "a06_audit_v5.py"
AUDIT_PATH = ROOT / "audit.py"
REFERENCE_PATH = ROOT / "reference_audit.py"
FIELDS = ("id", "intent_token", "owner_id")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_raw():
    return json.loads(RAW_PATH.read_text(encoding="utf-8"))


def prior_failed_checks(raw):
    prior_audit = load_module(BASELINE_AUDIT_PATH, "prior_audit_v5")
    return [check for check in prior_audit.evaluate_a06(raw) if not check["passed"]]


def mutation(raw, side, mask):
    result = copy.deepcopy(raw)
    rows = result["cases"][0]["rows"]
    event = "input_admission" if side == "admission" else "input_release_transition"
    row = next(row for row in rows if row.get("event") == event)
    for bit, field in enumerate(FIELDS):
        if mask & (1 << bit):
            row[field] = "foreign-" + field
    return result


class ReleaseIdentityAuditTests(unittest.TestCase):
    def setUp(self):
        self.audit = load_module(AUDIT_PATH, "audit_a07")
        self.reference = load_module(REFERENCE_PATH, "reference_a07")

    def test_retained_a06_baseline_still_passes_without_mutation(self):
        self.assertEqual(prior_failed_checks(load_raw()), [])

    def test_prior_a06_acceptance_gap_is_reproducible(self):
        self.assertEqual(prior_failed_checks(mutation(load_raw(), "admission", 1)), [])

    def test_baseline_identity_pairs_match_independent_reference(self):
        raw = load_raw()
        result = self.audit.evaluate(raw)
        self.assertTrue(self.reference.reference_passes(raw))
        self.assertTrue(result["passed"])
        self.assertEqual(result["case_count"], 2)
        self.assertEqual(sum(case["matched_count"] for case in result["cases"]), 4)

    def test_all_fourteen_identity_mutations_are_rejected(self):
        raw = load_raw()
        for side in ("admission", "release"):
            for mask in range(1, 8):
                changed = mutation(raw, side, mask)
                result = self.audit.evaluate(changed)
                expected = self.reference.reference_passes(changed)
                self.assertFalse(expected, (side, mask))
                self.assertEqual(result["passed"], expected, (side, mask, result))

    def test_duplicate_release_cannot_reuse_one_admission(self):
        raw = load_raw()
        case = raw["cases"][0]
        release = next(row for row in case["rows"] if row.get("event") == "input_release_transition")
        case["rows"].append(copy.deepcopy(release))
        self.assertFalse(self.audit.evaluate(raw)["passed"])
        self.assertFalse(self.reference.reference_passes(raw))


if __name__ == "__main__":
    unittest.main()
