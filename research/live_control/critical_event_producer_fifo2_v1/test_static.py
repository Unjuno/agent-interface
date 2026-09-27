import tempfile,sqlite3,pathlib,unittest
from model import *
class T(unittest.TestCase):
 def test_fifo(self):
  with tempfile.TemporaryDirectory() as x:
   p=str(pathlib.Path(x)/'d'); init_db(p); c=sqlite3.connect(p,isolation_level=None)
   self.assertEqual(producer_offer(c,2,4,'E4',digest('p4')),'PENDING_RETAINED'); self.assertEqual(producer_offer(c,2,5,'E5',digest('p5')),'PENDING_RETAINED'); c.commit(); self.assertEqual(snap(p)['pending'],['E4','E5'])
 def test_conflict(self):
  with tempfile.TemporaryDirectory() as x:
   p=str(pathlib.Path(x)/'d'); init_db(p); c=sqlite3.connect(p,isolation_level=None); producer_offer(c,2,4,'E4',digest('p4')); self.assertEqual(producer_offer(c,2,4,'E4',digest('x')),'PENDING_EVENT_CONFLICT')
if __name__=='__main__': unittest.main()
