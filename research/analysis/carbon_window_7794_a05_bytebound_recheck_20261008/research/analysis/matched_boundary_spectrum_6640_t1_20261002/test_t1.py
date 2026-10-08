"""Construction checks only; this suite is not the formal candidate/audit run."""
import copy
import json
import unittest
from pathlib import Path

import auditor
import candidate

ROOT = Path(__file__).resolve().parent


def inputs():
    return (json.loads((ROOT / "fixture.json").read_text(encoding="utf-8")),
            json.loads((ROOT / "oracle.json").read_text(encoding="utf-8")))


class ConstructionTests(unittest.TestCase):
    def test_finite_attempt_denominator_and_active_fault_cardinality(self):
        fixture, hidden = inputs()
        self.assertEqual(len(fixture["rows"]), 8192)
        self.assertEqual(len({r["attempt_id"] for r in fixture["rows"]}), 8192)
        self.assertEqual(len(hidden["seeds"]), 32)
        sizes = sorted(len(v["active_faults"]) for v in hidden["seeds"].values())
        self.assertEqual(sizes.count(1), 24)
        self.assertEqual(sizes.count(2), 8)

    def test_confounded_and_no_overlap_controls_are_present(self):
        fixture, _ = inputs()
        rows = fixture["rows"]
        self.assertTrue(any(r["exposure"]["gateway"] and r["stratum"].startswith("hard/") for r in rows))
        self.assertTrue(any(r["exposure"]["gateway"] is False and r["stratum"].startswith("easy/") for r in rows))
        for stratum in {r["stratum"] for r in rows}:
            vals = {r["exposure"]["cache"] for r in rows if r["stratum"] == stratum}
            self.assertEqual(len(vals), 1)
        self.assertEqual({r["exposure"]["cache"] for r in rows}, {False, True})
        self.assertTrue(any(r["exposure"]["instrumentation"] is None for r in rows))

    def test_success_can_coincide_with_active_fault_exposure(self):
        fixture, hidden = inputs()
        found = False
        for seed, truth in hidden["seeds"].items():
            for row in fixture["rows"]:
                if row["seed"] == int(seed) and not row["failed"] and any(row["exposure"][fault] for fault in truth["active_faults"]):
                    found = True
                    break
        self.assertTrue(found)

    def test_candidate_and_independent_raw_auditor_reconstruct_construction_output(self):
        fixture, hidden = inputs()
        raw = candidate.run(fixture)
        audit = auditor.audit(raw, fixture, hidden)
        self.assertEqual(audit["audit_status"], "PASS")
        self.assertEqual(audit["rows"], 8192)
        self.assertEqual(audit["seeds"], 32)
        self.assertTrue(all(x["status"]["matched"]["cache"] == "NO_OVERLAP" for x in raw["seed_results"]))
        self.assertEqual(raw["interpretation"], "inspection_priority_not_causal_evidence")

    def test_raw_mutations_are_rejected(self):
        fixture, hidden = inputs()
        base = candidate.run(fixture)

        altered = copy.deepcopy(base)
        altered["seed_results"][0]["scores"]["matched"]["admission"] += 0.01
        self.assertEqual(auditor.audit(altered, fixture, hidden)["audit_status"], "FAIL")

        altered = copy.deepcopy(base)
        altered["interpretation"] = "causal_proof"
        self.assertEqual(auditor.audit(altered, fixture, hidden)["audit_status"], "FAIL")

        altered_fixture = copy.deepcopy(fixture)
        altered_fixture["rows"].pop()
        self.assertEqual(auditor.audit(candidate.run(altered_fixture), fixture, hidden)["audit_status"], "FAIL")

        altered_fixture = copy.deepcopy(fixture)
        for row in altered_fixture["rows"]:
            if row["exposure"]["instrumentation"] is None:
                row["exposure"]["instrumentation"] = False
        self.assertEqual(auditor.audit(candidate.run(altered_fixture), fixture, hidden)["audit_status"], "FAIL")

        altered = copy.deepcopy(base)
        altered["seed_results"][0]["ranking"]["matched"].remove("admission")
        altered["seed_results"][0]["ranking"]["matched"].insert(0, "render")
        self.assertEqual(auditor.audit(altered, fixture, hidden)["audit_status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
