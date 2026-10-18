import copy, json, unittest
from pathlib import Path
import auditor, candidate

ROOT=Path(__file__).parent
CASES=json.loads((ROOT/"cases.json").read_text())
SCORING=json.loads((ROOT/"scoring_cases.json").read_text())


class MethodTests(unittest.TestCase):
    def setUp(self): self.raw=candidate.build(CASES,SCORING)

    def test_independent_gate_and_schedule_contract(self):
        result=auditor.reconstruct(CASES,SCORING,self.raw)
        self.assertEqual(result["decision"],"METHOD_PASS_SCOPED")
        self.assertEqual(result["errors"],[])
        self.assertEqual(result["human_effect"],"NOT_TESTED")

    def test_heterogeneity_gate_and_uniform_neutral_fallback(self):
        rows={r["case_id"]:r for r in self.raw["rows"]}
        self.assertTrue(rows["hetero-ab"]["eligible"])
        self.assertEqual(rows["uniform"]["adaptive_mode"],"NEUTRAL_FALLBACK")
        self.assertEqual(rows["uniform"]["adaptive"],rows["uniform"]["random"])
        self.assertTrue(rows["span-boundary"]["eligible"])

    def test_mutations_rejected_for_leak_exposure_gate_and_false_effect(self):
        mutations=[]
        x=copy.deepcopy(self.raw);x["rows"][0]["adaptive"][0]="hA";mutations.append(x)
        x=copy.deepcopy(self.raw);x["rows"][0]["random"].pop();mutations.append(x)
        x=copy.deepcopy(self.raw);x["rows"][3]["eligible"]=True;mutations.append(x)
        x=copy.deepcopy(self.raw);x["scoring_controls"][2]["score"]="VALID_EXACT_EFFECT";mutations.append(x)
        for raw in mutations:self.assertTrue(auditor.reconstruct(CASES,SCORING,raw)["errors"])


if __name__=="__main__":unittest.main()
