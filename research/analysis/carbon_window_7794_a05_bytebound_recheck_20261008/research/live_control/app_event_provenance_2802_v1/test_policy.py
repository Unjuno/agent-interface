from __future__ import annotations
import unittest
from policy import candidate, unsafe_timestamp_only

def e(label,source,seq,domain,t): return {'label':label,'source_id':source,'seq':seq,'clock_domain':domain,'t_ns':t}
class T(unittest.TestCase):
    def test_good(self): self.assertEqual(candidate([e('A','a',1,'M',0),e('B','a',2,'M',1)],10),'SATISFIED')
    def test_domain(self): self.assertEqual(candidate([e('A','a',1,'M',0),e('B','a',2,'B',1)],10),'UNKNOWN_CLOCK_DOMAIN')
    def test_gap(self): self.assertEqual(candidate([e('A','a',1,'M',0),e('B','a',3,'M',1)],10),'UNKNOWN_GAP')
    def test_order(self): self.assertEqual(candidate([e('A','a',2,'M',0),e('B','a',1,'M',1)],10),'UNKNOWN_ORDER')
    def test_source(self): self.assertEqual(candidate([e('A','a',1,'M',0),e('B','b',2,'M',1)],10),'UNKNOWN_SOURCE')
    def test_late(self): self.assertEqual(candidate([e('A','a',1,'M',0),e('B','a',2,'M',11)],10),'EXPIRED')
    def test_unsafe_gap(self): self.assertEqual(unsafe_timestamp_only([e('A','a',1,'M',0),e('B','a',3,'M',1)],10),'SATISFIED')
if __name__=='__main__': unittest.main()
