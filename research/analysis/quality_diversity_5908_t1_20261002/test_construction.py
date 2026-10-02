import copy
import importlib.util
import json
from pathlib import Path
import unittest

P=Path(__file__).parent
def load(name,file):
    s=importlib.util.spec_from_file_location(name,P/file); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
cand=load("cand5908","candidate.py")
audit=load("audit5908","audit.py")
PUBLIC=json.loads((P/"public.json").read_text())
TRUTH=json.loads((P/"truth.json").read_text())


class Construction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=cand.run(PUBLIC,TRUTH)

    def test_counts_and_common_input_pool(self):
        self.assertEqual(len(PUBLIC["cases"]),12)
        self.assertEqual(sum(x["admit"] for x in TRUTH["admission"].values()),8)
        self.assertTrue(all(v["call_count"]==6 for v in self.out["policies"].values()))

    def test_selector_boundary_contains_only_visible_inputs(self):
        self.assertEqual(self.out["audit_boundary"],{"selector_input_keys":["id","features"],"selector_received_truth":False,"selector_received_traces_for_unevaluated_cases":False})
        for case in PUBLIC["cases"]:
            self.assertEqual(set(case),{"id","features"})

    def test_independent_audit_passes_frozen_pool(self):
        got=audit.independently_expected(PUBLIC,TRUTH,self.out)
        self.assertEqual(got["status"],"METHOD_PASS_SCOPED",got)

    def test_descriptor_corruption_detected(self):
        bad=copy.deepcopy(self.out)
        row=bad["policies"]["descriptor-archive"]["rows"][1]
        row["observed_trace"]["event"]="stale-target-refusal"
        result=audit.independently_expected(PUBLIC,TRUTH,bad)
        self.assertTrue(any("raw_reconstruction_mismatch" in e for e in result["errors"]))

    def test_oracle_label_corruption_detected(self):
        bad=copy.deepcopy(self.out)
        bad["policies"]["uniform-seeded"]["rows"][0]["adjudication_label"]="M_RELEASE_GAP"
        result=audit.independently_expected(PUBLIC,TRUTH,bad)
        self.assertTrue(any("raw_reconstruction_mismatch" in e for e in result["errors"]))

    def test_invalid_filter_bypass_detected(self):
        bad=copy.deepcopy(self.out)
        method=bad["policies"]["descriptor-archive"]
        method["selected_case_ids"][-1]="c09"
        result=audit.independently_expected(PUBLIC,TRUTH,bad)
        self.assertTrue(any("inadmissible_case_selected" in e or "no_eligible_evaluation" in e for e in result["errors"]))

    def test_archive_does_not_claim_advantage_when_baselines_match(self):
        counts={k:len(v["unique_mechanisms"]) for k,v in self.out["policies"].items()}
        self.assertEqual(counts,{"uniform-seeded":2,"pairwise":2,"descriptor-archive":2})

    def test_duplicate_descriptor_cell_cannot_pass(self):
        bad=copy.deepcopy(self.out)
        truth=copy.deepcopy(TRUTH)
        truth["evaluation"]["c04"]["trace"]=copy.deepcopy(truth["evaluation"]["c00"]["trace"])
        got=audit.independently_expected(PUBLIC,truth,bad)
        self.assertNotEqual(got["status"],"METHOD_PASS_SCOPED")

    def test_future_case_count_is_not_a_call(self):
        self.assertNotIn("c08",self.out["policies"]["descriptor-archive"]["selected_case_ids"])
        self.assertNotIn("c09",self.out["policies"]["descriptor-archive"]["selected_case_ids"])


if __name__=="__main__": unittest.main(verbosity=2)
