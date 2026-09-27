import copy,json,unittest
from audit_v2 import audit
class AuditV2Controls(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  with open('formal.json',encoding='utf-8') as f: cls.base=json.load(f)
 def reject(self,mut):
  r=audit(mut); self.assertEqual('FAIL',r['audit']); self.assertTrue(r['errors'])
 def test_drop_row(self): x=copy.deepcopy(self.base); x['rows'].pop(); self.reject(x)
 def test_wrong_decision(self): x=copy.deepcopy(self.base); x['rows'][0]['decision']='YIELD_UNKNOWN'; self.reject(x)
 def test_authority(self): x=copy.deepcopy(self.base); x['rows'][0]['authority']='input'; self.reject(x)
 def test_input(self): x=copy.deepcopy(self.base); x['rows'][0]['input_dispatched']=True; self.reject(x)
 def test_worker(self): x=copy.deepcopy(self.base); x['rows'][0]['worker_status'][0]='failed'; self.reject(x)
 def test_pair_diverge(self): x=copy.deepcopy(self.base); [r for r in x['rows'] if r['arm']=='DEPENDENCY_READY' and r['scenario']=='NORMAL'][0]['decision']='YIELD_UNKNOWN'; self.reject(x)
 def test_latency(self): x=copy.deepcopy(self.base); r=[r for r in x['rows'] if r['arm']=='DEPENDENCY_READY' and r['scenario']=='NORMAL'][0]; r['decision_ms']=999; self.reject(x)
 def test_partial(self): x=copy.deepcopy(self.base); r=[r for r in x['rows'] if r['arm']=='DEPENDENCY_READY'][0]; r['decision_ms']=r['results']['P_slow_semantic']['evaluated_ms']+1; self.reject(x)
if __name__=='__main__': unittest.main()
