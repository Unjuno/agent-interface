import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent)); from audit import evaluate
def base_rows():
 rows=[]
 for rep in range(3):
  for app,scenario,cand,actual in [("inkscape","stable","MATCH",True),("inkscape","pointer_displaced","MISMATCH",False),("inkscape","observer_unavailable","UNKNOWN",False),("calc","stable","MATCH",True),("calc","focus_transferred","MISMATCH",False),("calc","observer_unavailable","UNKNOWN",False)]:
   rows.append({"case_id":f"{app}-{scenario}-r{rep}","app":app,"scenario":scenario,"status":"ok","candidate_class":cand,"held_observed_during":True,"release_observed_before_perturbation":True,"cleanup_neutral":True,"actual_match":actual,"naive_command_only_class":"MATCH"})
 return rows
class AuditControls(unittest.TestCase):
 def test_base(self): self.assertEqual(evaluate(base_rows())["errors"],[])
 def reject(self,mut):
  r=base_rows(); mut(r); self.assertTrue(evaluate(r)["errors"])
 def test_controls(self):
  controls=[lambda r:r.pop(),lambda r:r.append(copy.deepcopy(r[0])),lambda r:r[0].__setitem__("candidate_class","MISMATCH"),lambda r:r[1].__setitem__("actual_match",True),lambda r:r[2].__setitem__("candidate_class","MATCH"),lambda r:r[3].__setitem__("held_observed_during",False),lambda r:r[4].__setitem__("cleanup_neutral",False),lambda r:r[5].__setitem__("naive_command_only_class","UNKNOWN"),lambda r:r[6].__setitem__("status","error"),lambda r:r[7].__setitem__("case_id",r[6]["case_id"])]
  for c in controls: self.reject(c)
if __name__=="__main__": unittest.main()
