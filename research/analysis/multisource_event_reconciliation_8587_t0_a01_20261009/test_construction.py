import json
import unittest
from pathlib import Path

import auditor
import candidate

ROOT=Path(__file__).resolve().parent
MODEL=json.loads((ROOT/"model.json").read_text())
ORACLE=json.loads((ROOT/"oracle.json").read_text())
FREEZE={"allocation_id":"CONSTRUCTION_ONLY"}

class ConstructionTests(unittest.TestCase):
    def test_all_identifiable_fault_boundaries_are_detected(self):
        expected={x["case_id"]:(x["expected_classification"],x["expected_boundary"]) for x in ORACLE["cases"]}
        rows=[candidate.reconcile(case) for case in MODEL["cases"]]
        for row in rows:
            self.assertEqual((row["classification"],row["boundary"]),expected[row["case_id"]],row["case_id"])
        self.assertEqual(sum(x["classification"]=="FAULT" for x in rows),8)

    def test_nonidentifiable_controls_fail_closed(self):
        rows={c["case_id"]:candidate.reconcile(c) for c in MODEL["cases"]}
        self.assertEqual(rows["missing_correlation"]["classification"],"UNKNOWN_CORRELATION")
        self.assertEqual(rows["os_truncated"]["classification"],"UNKNOWN_SOURCE_COVERAGE")
        self.assertIsNone(rows["missing_correlation"]["boundary"])

    def test_source_omission_and_forged_token_change_the_reconstruction(self):
        omitted=json.loads(json.dumps(MODEL))
        clean=next(c for c in omitted["cases"] if c["case_id"]=="clean")
        clean["logs"]["toolkit"].clear()
        self.assertEqual(candidate.classify(clean)[:2],("FAULT","CLIENT_TO_TOOLKIT"))
        forged=json.loads(json.dumps(MODEL))
        concurrent=next(c for c in forged["cases"] if c["case_id"]=="concurrent_reorder")
        concurrent["logs"]["toolkit"][0]["correlation_token"]="a1"
        self.assertEqual(candidate.classify(concurrent)[:2],("FAULT","TOOLKIT"))

    def test_incomparable_actions_are_not_totally_ordered_by_source_sequences(self):
        row=candidate.reconcile(next(c for c in MODEL["cases"] if c["case_id"]=="concurrent_reorder"))
        self.assertEqual(row["declared_action_order"],[])
        self.assertEqual(row["incomparable_action_pairs"],["a1|a2"])

    def test_weak_comparators_miss_seeded_cross_source_faults(self):
        rows=[candidate.reconcile(case) for case in MODEL["cases"]]
        self.assertEqual(sum(r["classification"]=="FAULT" for r in rows),8)
        self.assertEqual(sum(r["baselines"]["CLIENT_LEDGER_ONLY"]!="NO_SIGNAL" for r in rows),1)
        self.assertEqual(sum(r["baselines"]["FINAL_STATE_ONLY"]!="NO_SIGNAL" for r in rows),0)

    def test_full_independent_audit_and_five_mutations(self):
        rows=[candidate.reconcile(case) for case in MODEL["cases"]]
        raw={"schema":"multisource-event-candidate-v1","allocation_id":FREEZE["allocation_id"],
             "cases":rows,"summary":{"localized_faults":sum(r["classification"]=="FAULT" for r in rows),
             "unknowns":sum(r["classification"].startswith("UNKNOWN") for r in rows),
             "final_state_only_signals":0,"client_only_signals":1}}
        self.assertEqual(auditor.audit_rows(MODEL,ORACLE,raw,FREEZE["allocation_id"]),[])
        self.assertTrue(auditor.audit_rows(MODEL,ORACLE,{**raw,"cases":rows[:-1]},FREEZE["allocation_id"]))

if __name__=="__main__": unittest.main()
