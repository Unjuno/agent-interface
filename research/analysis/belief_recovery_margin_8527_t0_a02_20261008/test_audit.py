import copy
import hashlib
import json
import unittest
from pathlib import Path

from candidate import run
from audit import audit


ROOT = Path(__file__).parent
FIXTURE = json.loads((ROOT / "input.json").read_text(encoding="utf-8"))
TRUTH = json.loads((ROOT / "truth.json").read_text(encoding="utf-8"))


def canonical_digest(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


class IndependentPolicyTreeAuditTests(unittest.TestCase):
    def test_auditor_reconstructs_every_case_horizon_and_witness(self):
        raw = run(FIXTURE)
        report = audit(FIXTURE, raw, canonical_digest(FIXTURE), TRUTH)
        self.assertEqual(report["status"], "PASS_BELIEF_RECOVERY_MARGIN_SCOPED")
        self.assertEqual(report["rows"], 40)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["mutations_rejected"], 3)

    def test_auditor_rejects_corrupted_classification(self):
        raw = run(FIXTURE)
        changed = copy.deepcopy(raw)
        next(x for x in changed["rows"] if x["case_id"] == "aliased-opposite-actions" and x["horizon"] == 3)["status"] = "RECOVERABLE"
        with self.assertRaises(ValueError):
            audit(FIXTURE, changed, canonical_digest(FIXTURE), TRUTH)

    def test_auditor_rejects_incomplete_policy_branch(self):
        raw = run(FIXTURE)
        changed = copy.deepcopy(raw)
        row = next(x for x in changed["rows"] if x["case_id"] == "safe-information-gathering" and x["horizon"] == 2)
        row["policy"]["branches"].pop("right-cue")
        with self.assertRaises(ValueError):
            audit(FIXTURE, changed, canonical_digest(FIXTURE), TRUTH)

    def test_auditor_rejects_mutated_model_even_if_raw_is_unchanged(self):
        raw = run(FIXTURE)
        changed = copy.deepcopy(FIXTURE)
        changed["cases"][1]["initial_belief"] = ["L"]
        with self.assertRaises(ValueError):
            audit(changed, raw, canonical_digest(FIXTURE), TRUTH)


if __name__ == "__main__":
    unittest.main()
