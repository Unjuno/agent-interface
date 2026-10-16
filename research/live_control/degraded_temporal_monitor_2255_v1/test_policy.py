import unittest
from policy import decide

def p(events,**kw):
 d={'events':events,'coverage_complete':True,'order_complete':True,'clock_coherent':True,'scope':'title-contract-v1'}; d.update(kw); return d
def e(ph,t,epoch=1,clock='xserver'): return {'phase':ph,'server_ms':t,'epoch':epoch,'clock_domain':clock}
class T(unittest.TestCase):
 def test_ab(self): self.assertEqual(decide(p([e('A',10),e('B',40)]),'FAIL_CLOSED')['status'],'SATISFIED')
 def test_late(self): self.assertEqual(decide(p([e('A',10),e('B',100)]),'FAIL_CLOSED')['status'],'NOT_SATISFIED')
 def test_cancel(self): self.assertEqual(decide(p([e('A',10),e('CANCEL',20),e('B',30)]),'FAIL_CLOSED')['status'],'NOT_SATISFIED')
 def test_gap(self): self.assertEqual(decide(p([e('A',10),e('B',30)],coverage_complete=False),'FAIL_CLOSED')['status'],'UNKNOWN')
 def test_order(self): self.assertEqual(decide(p([e('B',30),e('A',10)],order_complete=False),'FAIL_CLOSED')['status'],'UNKNOWN')
 def test_clock(self): self.assertEqual(decide(p([e('A',10),e('B',30,clock='foreign')],clock_coherent=False),'FAIL_CLOSED')['status'],'UNKNOWN')
 def test_naive_ignores_gap(self): self.assertEqual(decide(p([e('A',10),e('B',30)],coverage_complete=False),'NAIVE_COMPILED')['status'],'SATISFIED')
if __name__=='__main__': unittest.main()
