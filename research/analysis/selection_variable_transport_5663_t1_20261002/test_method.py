import copy, importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/file)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

candidate=load("candidate","candidate.py")
auditor=load("auditor","audit.py")
DOC=json.loads((ROOT/"inputs"/"fixture.json").read_text(encoding="utf-8"))

class T1Tests(unittest.TestCase):
    def setUp(self): self.result=candidate.run(DOC)
    def test_composition_reversal_and_standardization(self):
        x=self.result["scenarios"]["composition_stable"]
        self.assertAlmostEqual(x["source_direct_effect"],.026)
        self.assertAlmostEqual(x["target_direct_effect"],-.086)
        self.assertAlmostEqual(x["transported_effect"],-.086)
        self.assertEqual(x["status"],"TRANSPORT_METHOD_CONTROL_PASS")
    def test_mechanism_shift_refuses(self):
        x=self.result["scenarios"]["mechanism_shift"]
        self.assertAlmostEqual(x["target_direct_effect"],-.006)
        self.assertIsNone(x["transported_effect"])
        self.assertAlmostEqual(x["diagnostic_only_naive_standardization"],-.086)
        self.assertEqual(x["status"],"HOLD_NONTRANSPORTABLE")
    def test_support_and_endpoint_controls_hold(self):
        self.assertEqual(self.result["scenarios"]["support_failure"]["status"],"HOLD_NONTRANSPORTABLE")
        self.assertEqual(self.result["scenarios"]["endpoint_mismatch"]["status"],"HOLD_NONCOMPARABLE")
    def test_auditor_accepts_unmutated_result(self):
        r=copy.deepcopy(self.result); r["candidate_sha256"]=auditor.sha(ROOT/"candidate.py")
        self.assertEqual(auditor.audit(r,DOC,ROOT/"candidate.py"),[])
    def test_auditor_rejects_sign_and_mechanism_mutations(self):
        r=copy.deepcopy(self.result); r["candidate_sha256"]=auditor.sha(ROOT/"candidate.py")
        r["scenarios"]["composition_stable"]["transported_effect"]=.026
        r["scenarios"]["mechanism_shift"]["transported_effect"]=-.086
        self.assertTrue(auditor.audit(r,DOC,ROOT/"candidate.py"))
    def test_auditor_rejects_support_and_contract_mutations(self):
        r=copy.deepcopy(self.result); r["candidate_sha256"]=auditor.sha(ROOT/"candidate.py")
        r["scenarios"]["support_failure"]["status"]="TRANSPORT_METHOD_CONTROL_PASS"
        r["scenarios"]["endpoint_mismatch"]["status"]="TRANSPORT_METHOD_CONTROL_PASS"
        self.assertTrue(auditor.audit(r,DOC,ROOT/"candidate.py"))

if __name__=="__main__": unittest.main(verbosity=2)