import json
import unittest
from pathlib import Path
from candidate import run
from audit import audit_payload
ROOT=Path(__file__).parent
class AuditConstruction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v=json.loads((ROOT/'visible.json').read_text()); cls.t=json.loads((ROOT/'truth.json').read_text()); cls.r=run(cls.v)
    def test_expected_rank_reversal_and_controls(self):
        result=audit_payload(self.v,self.t,self.r)
        self.assertEqual(result['disposition'],'PASS_METHOD_SCOPED',result['errors'])
        self.assertEqual(result['summaries']['A']['es20'],2.2)
        self.assertEqual(result['summaries']['B']['es20'],1.0)
        self.assertEqual(len(result['mutation_controls']),6)
    def test_allocation_and_safety_stay_separate(self):
        result=audit_payload(self.v,self.t,self.r)
        self.assertEqual(result['assigned_opportunities'],24)
        self.assertEqual(result['hard_safety_violations'],0)
        self.assertIsNone(result['controls']['hard_safety_violation']['numeric_value'])
if __name__=='__main__': unittest.main()
