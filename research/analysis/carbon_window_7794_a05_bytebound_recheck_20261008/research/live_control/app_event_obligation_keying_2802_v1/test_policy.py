import unittest
from policy import target_candidate,unsafe_shared

def e(label,oid,seq): return {'label':label,'obligation_id':oid,'seq':seq}
class T(unittest.TestCase):
 def test_cross(self):
  ev=[e('A','o1',1),e('B','o2',2)]; self.assertEqual(target_candidate(ev)[0],'PENDING'); self.assertEqual(unsafe_shared(ev)[0],'SATISFIED')
 def test_right_late(self):
  ev=[e('A','o1',1),e('B','o2',2),e('B','o1',3)]; r,p=target_candidate(ev); self.assertEqual(r,'SATISFIED'); self.assertEqual(p,['PENDING','PENDING','SATISFIED'])
 def test_missing(self): self.assertEqual(target_candidate([e('A','o1',1),e('B',None,2)])[0],'UNKNOWN_ID')
 def test_both(self): self.assertEqual(target_candidate([e('A','o1',1),e('A','o2',2),e('B','o1',3),e('B','o2',4)])[0],'SATISFIED')
if __name__=='__main__': unittest.main()
