import copy
import unittest
from audit import audit
from candidate import score
from pathlib import Path
import json

FIXTURE=json.loads((Path(__file__).parent/"fixture.json").read_text())

class MethodTests(unittest.TestCase):
    def test_preserves_full_principal_and_event_ledger(self):
        r=score(FIXTURE); self.assertEqual(audit(FIXTURE,r)["status"],"PASS_METHOD_SCOPED")
    def test_detects_requester_gain_bystander_burden(self):
        r=score(FIXTURE); self.assertEqual(r["requester_only_fast_gain_minutes"],14); self.assertEqual(r["collaborator_burden_minutes_by_route"],{"plain":1,"fast":17})
    def test_zero_contact_and_scheduled_approval_are_controls(self):
        r=score(FIXTURE); self.assertEqual(r["by_route_and_principal"]["fast"]["requester"]["delivered_interruptions"],0); self.assertEqual(r["by_route_and_principal"]["plain"]["collab-a"]["delivered_interruptions"],1)
    def test_maximum_burst_is_principal_indexed(self):
        r=score(FIXTURE)["by_route_and_principal"]
        self.assertEqual(r["fast"]["collab-b"]["maximum_burst_events"],3)
        self.assertEqual(r["fast"]["collab-b"]["maximum_burst_minutes"],6)
        self.assertEqual(r["fast"]["collab-a"]["maximum_burst_events"],2)
        self.assertEqual(r["fast"]["collab-a"]["maximum_burst_minutes"],4)
    def test_rejects_dropped_recipient(self):
        r=score(FIXTURE); r["by_route_and_principal"]["fast"].pop("collab-b")
        with self.assertRaises(AssertionError): audit(FIXTURE,r)
    def test_candidate_rejects_duplicate_task_route_assignment(self):
        f=copy.deepcopy(FIXTURE); duplicate=copy.deepcopy(next(e for e in f["events"] if e["id"]=="e01")); duplicate["id"]="e28"; duplicate["active_minutes"]=0; f["events"].append(duplicate)
        with self.assertRaisesRegex(ValueError,"task_assignment_coverage"): score(f)
    def test_independent_auditor_rejects_duplicate_zero_minute_assignment(self):
        f=copy.deepcopy(FIXTURE); duplicate=copy.deepcopy(next(e for e in f["events"] if e["id"]=="e01")); duplicate["id"]="e28"; duplicate["active_minutes"]=0; f["events"].append(duplicate)
        r=score(FIXTURE); r["event_ids"].append("e28"); r["logged_event_count"]+=1; r["event_status_counts"]["verified"]+=1
        with self.assertRaisesRegex(AssertionError,"assigned_task_route_coverage_and_uniqueness"): audit(f,r)
    def test_rejects_unsent_as_delivered(self):
        f=copy.deepcopy(FIXTURE); f["events"][-1]["status"]="delivered"
        with self.assertRaisesRegex(ValueError,"event_status_count"): score(f)
    def test_rejects_collapsed_burst(self):
        f=copy.deepcopy(FIXTURE); f["events"].remove(next(e for e in f["events"] if e["id"]=="e08"))
        with self.assertRaisesRegex(ValueError,"event_status_count"): score(f)
    def test_rejects_double_counted_review(self):
        r=score(FIXTURE); r["by_route_and_principal"]["fast"]["collab-a"]["active_minutes"]+=2
        with self.assertRaises(AssertionError): audit(FIXTURE,r)
    def test_rejects_erased_nonresponse(self):
        f=copy.deepcopy(FIXTURE); next(e for e in f["events"] if e["id"]=="e13")["status"]="delivered"
        with self.assertRaisesRegex(ValueError,"event_status_count"): score(f)

if __name__=="__main__": unittest.main()
