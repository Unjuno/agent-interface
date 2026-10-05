import copy,json,unittest
from pathlib import Path
import auditor,candidate

ROOT=Path(__file__).parent
CASES=json.loads((ROOT/"cases.json").read_text())
TRUTH=json.loads((ROOT/"scoring_cases.json").read_text())


class MethodTest(unittest.TestCase):
    def setUp(self):self.raw=candidate.execute(CASES)

    def test_audited_gate_and_scoring_controls(self):
        result=auditor.audit(CASES,TRUTH,self.raw)
        self.assertEqual(result["decision"],"METHOD_PASS_SCOPED")
        self.assertEqual(result["errors"],[])
        self.assertEqual([x["score"] for x in result["scoring_controls"]],
                         ["VALID_EXACT_EFFECT","REJECT_WRONG_TARGET","REJECT_FALSE_SUCCESS","UNKNOWN_OUTSIDE_FAMILY"])
        self.assertEqual(result["human_effect"],"NOT_TESTED")

    def test_mutations_break_exposure_eligibility_leak_and_optimizer(self):
        for row_index,field,value in ((0,"adaptive",["hA"]*12),(3,"eligible",True),(0,"random",["vA"]*12),(0,"adaptive",["vA","vB"]*6)):
            raw=copy.deepcopy(self.raw);raw["rows"][row_index][field]=value
            self.assertTrue(auditor.audit(CASES,TRUTH,raw)["errors"],field)

    def test_candidate_input_schema_has_no_heldout_or_effect_truth(self):
        self.assertNotIn("heldout",CASES)
        self.assertNotIn("expected_effect",CASES)
        self.assertNotIn("scoring_cases",candidate.__dict__)


if __name__=="__main__":unittest.main()
