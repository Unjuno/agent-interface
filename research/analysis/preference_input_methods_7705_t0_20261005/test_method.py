import copy,json,pathlib,unittest
from auditor import schema_errors
from candidate import evaluate
ROOT=pathlib.Path(__file__).parent

class MethodTests(unittest.TestCase):
    def setUp(self):self.doc=json.loads((ROOT/"cases.json").read_text())
    def test_frozen_cases_cover_required_shapes(self):
        out={c["id"]:evaluate(c) for c in self.doc["cases"]}
        self.assertEqual(out["weights-fast"]["selected"],["fast"])
        self.assertEqual(out["classify-balanced"]["selected"],["balanced","balanced-copy"])
        self.assertEqual(out["classify-impossible"]["status"],"NO_FEASIBLE_ROUTE")
        self.assertEqual(out["classify-tie"]["status"],"AMBIGUOUS_SET")
        self.assertEqual(out["pairwise-balanced"]["selected"],["balanced"])
        self.assertEqual(out["incomplete"]["status"],"HOLD_INPUT_INCOMPLETE")
        self.assertEqual(out["convex-front"]["pareto"],["left","mid","right"])
        self.assertEqual(out["disconnected-front"]["pareto"],["left","right"])
    def test_four_frozen_mutations_are_rejected(self):
        mutants=[]
        x=copy.deepcopy(self.doc);x["criteria"]["actual_tokens"]["unit"]="ms";mutants.append(x)
        x=copy.deepcopy(self.doc);x["routes"][0]["outcomes"].pop("actual_tokens");mutants.append(x)
        x=copy.deepcopy(self.doc);x["criteria"]["wait_ms"]["direction"]="maximize";mutants.append(x)
        x=copy.deepcopy(self.doc);x["routes"][-1]["eligible"]=True;mutants.append(x)
        self.assertTrue(all(schema_errors(x) for x in mutants))

if __name__=="__main__":unittest.main()
