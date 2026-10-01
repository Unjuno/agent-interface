import copy, json, unittest
from audit import audit
class T(unittest.TestCase):
 def base(self):
  rows=[]; i=0
  for rep in range(2):
   for fam in ['TK_CALLBACK','WORKER_FILE']:
    for sc in ['NORMAL','HORIZON_LATE','FOCUS_LOSS','OWNER_DEATH','BOUND_VIOLATION','UNKNOWN_BOUND']:
     for pol in ['GENERIC_CENSOR','CAUSE_AWARE']:
      unsafe=pol=='GENERIC_CENSOR' and sc in ['FOCUS_LOSS','OWNER_DEATH','BOUND_VIOLATION','UNKNOWN_BOUND']
      action='HOLD' if pol=='CAUSE_AWARE' and sc in ['FOCUS_LOSS','OWNER_DEATH','BOUND_VIOLATION','UNKNOWN_BOUND'] else 'PROCEED'
      rows.append({'family':fam,'scenario':sc,'policy':pol,'rep':rep,'action':action,'safe_precondition':not unsafe if action=='PROCEED' else False,'unsafe_proceed':unsafe,'typed_receipt':{'clock':'CLOCK_MONOTONIC','family':fam}}); i+=1
  return rows
 def test_reference(self): self.assertEqual(audit(self.base())['errors'],[])
 def test_missing(self): self.assertTrue(audit(self.base()[:-1])['errors'])
 def test_duplicate(self): r=self.base(); r[-1]=copy.deepcopy(r[0]); self.assertTrue(audit(r)['errors'])
 def test_candidate_unsafe(self): r=self.base(); x=next(x for x in r if x['policy']=='CAUSE_AWARE' and x['scenario']=='FOCUS_LOSS'); x['action']='PROCEED'; x['safe_precondition']=False; x['unsafe_proceed']=True; self.assertTrue(audit(r)['errors'])
 def test_wrong_clock(self): r=self.base(); r[0]['typed_receipt']['clock']='wall'; self.assertTrue(audit(r)['errors'])
 def test_wrong_family_binding(self): r=self.base(); r[0]['typed_receipt']['family']='OTHER'; self.assertTrue(audit(r)['errors'])
if __name__=='__main__': unittest.main()
