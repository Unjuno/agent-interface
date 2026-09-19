import json, tempfile, unittest
from pathlib import Path
from scorer import score

def fixture():
    return {"schema":"agent_interface_golden_desktop_live_v2","passed":True,
            "tasks_exact":6,"routes":["cold","reuse","reuse","repair","reuse","reuse"],
            "independent_evaluation":{"success":True,"record_count":6,"unexpected":[],"missing":[]},
            "all_releases_verified":True,
            "tasks":[{"typed_outcome":"completed","exact_submission":True,"releases_verified":True} for _ in range(6)]}

class ScorerTests(unittest.TestCase):
    def test_valid_report_holds_without_authority(self):
        r=score(fixture())
        self.assertEqual(r["status"],"HOLD")
        self.assertEqual(r["reason"],"HOLD_NO_MODEL_AUTHORITY")
    def test_valid_report_can_only_be_marked_by_explicit_gate(self):
        r=score(fixture(),live_authority=True)
        self.assertEqual(r["status"],"PASS")
        self.assertTrue(r["authority_granted"])
    def test_stale_or_ambiguous_evidence_fails_closed(self):
        bad=fixture(); bad["tasks"][3]["exact_submission"]=False
        r=score(bad)
        self.assertEqual(r["status"],"FAIL")
        self.assertIn("task_outcomes",r["reason"])
    def test_missing_authority_is_not_pseudo_success(self):
        r=score({"schema":"wrong"})
        self.assertEqual(r["status"],"FAIL")
        self.assertFalse(r["authority_granted"])

if __name__=="__main__":
    unittest.main()
