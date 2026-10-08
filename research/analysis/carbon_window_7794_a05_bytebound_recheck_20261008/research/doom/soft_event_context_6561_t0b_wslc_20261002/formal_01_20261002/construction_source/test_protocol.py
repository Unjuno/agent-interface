import copy
import json
import unittest
from pathlib import Path
import auditor
import candidate


FIXTURE=Path(__file__).with_name("cases.json")


def fixture(): return json.loads(FIXTURE.read_text(encoding="utf-8"))


class SoftContextT0bTests(unittest.TestCase):
    def baseline(self):
        f=fixture(); return f,candidate.build_packet(f)

    def rejects(self,packet,truth):
        with self.assertRaises(ValueError): auditor.audit_packet(packet,truth)

    def test_six_baseline_cases_reconstruct_and_audit(self):
        f,p=self.baseline(); result=auditor.audit_packet(p,f)
        self.assertEqual(result["status"],"PASS_METHOD_SCOPED")
        self.assertEqual(result["case_count"],6)
        self.assertEqual({r["case_id"] for r in p["cases"]},{"NONE","ONE_SOFT","MULTI_SOFT","HARD","UNKNOWN","EXPIRED"})

    def test_none_unknown_hard_and_expired_are_distinct(self):
        _,p=self.baseline(); states={r["case_id"]:r["context"] for r in p["cases"]}
        self.assertEqual(states["NONE"],{"state":"NONE"})
        self.assertEqual(states["UNKNOWN"],{"state":"UNKNOWN","reason":"unknown"})
        self.assertEqual(states["HARD"],{"state":"UNKNOWN","reason":"invalidated"})
        self.assertEqual(states["EXPIRED"],{"state":"UNKNOWN","reason":"expired"})

    def test_co_mutated_case_and_event_binding_is_rejected_by_frozen_fixture(self):
        truth,p=self.baseline(); changed=copy.deepcopy(truth); c=changed["cases"][1]
        c["binding"]["session"]="attacker-session"
        c["raw_events"][0]["signal"]["binding"]["session"]="attacker-session"
        self.rejects(candidate.build_packet(changed),truth)

    def test_six_contradictory_guard_flags_are_rejected(self):
        mutations=(("grants_input_authority",True),("requires_new_decision",True),
            ("keep_existing_policy",False),("may_only_preserve_or_reduce_existing_authority",False),
            ("semantic_change_identified",False),("task_success_verified",True))
        truth,_=self.baseline()
        for key,value in mutations:
            with self.subTest(flag=key):
                changed=copy.deepcopy(truth); changed["cases"][1]["raw_events"][0]["outcome"][key]=value
                self.rejects(candidate.build_packet(changed),truth)

    def test_expiry_requires_a_matching_source_bound_receipt(self):
        truth,_=self.baseline()
        for mutation in ("missing","relabeled"):
            with self.subTest(mutation=mutation):
                changed=copy.deepcopy(truth); c=changed["cases"][5]
                if mutation=="missing": c["invalidation_receipt"]=None
                else: c["invalidation_receipt"]["reason"]="signal_unavailable"
                self.rejects(candidate.build_packet(changed),truth)

    def test_current_sequence_rejects_float_bool_and_negative_inputs(self):
        truth,_=self.baseline()
        for value in (90.0,True,-1):
            with self.subTest(sequence=value):
                changed=copy.deepcopy(truth); changed["cases"][1]["current_sequence"]=value
                packet=candidate.build_packet(changed)
                self.assertEqual(packet["cases"][1]["context"],{"state":"UNKNOWN","reason":"invalid_case_source"})
                self.rejects(packet,truth)

    def test_future_event_and_inconsistent_emitted_count_are_rejected(self):
        truth,p=self.baseline(); changed=copy.deepcopy(truth)
        changed["cases"][1]["raw_events"][0]["sequence"]=90
        self.rejects(candidate.build_packet(changed),truth)
        _,p=self.baseline(); row=next(r for r in p["cases"] if r["case_id"]=="MULTI_SOFT")
        row["context"]["soft_event_count"]=2
        self.rejects(p,truth)

    def test_prompt_cannot_add_authority_or_success_claim(self):
        truth,p=self.baseline(); row=next(r for r in p["cases"] if r["case_id"]=="ONE_SOFT")
        row["prompt"] += '"task_success_verified":true'
        self.rejects(p,truth)


if __name__=="__main__": unittest.main()
