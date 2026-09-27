import tempfile
from pathlib import Path
import unittest
from batch_probe import validate_next,save

class BatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'allocation';self.root.mkdir()
        self.plan={'allocation':'allocation','schedule':[{'index':i} for i in range(24)]}
    def test_disjoint_fixed_batches(self):
        seen=[]
        for b in range(4):
            cases=validate_next(self.root,self.plan,b);seen.extend(i for i,_ in cases)
            p=self.root/f'batch-{b:02d}';p.mkdir();save(p/'complete.json',{'pass':True})
        self.assertEqual(seen,list(range(24)))
    def test_consumed_incomplete_cannot_resume(self):
        (self.root/'batch-00').mkdir()
        with self.assertRaises(FileExistsError):validate_next(self.root,self.plan,0)
        with self.assertRaises(FileNotFoundError):validate_next(self.root,self.plan,1)
    def test_failure_blocks_later_batches(self):
        save(self.root/'failure.json',{'error':'killed'})
        with self.assertRaises(ValueError):validate_next(self.root,self.plan,0)
    def test_wrong_allocation_and_type(self):
        with self.assertRaises(ValueError):validate_next(self.root,{'allocation':'other'},0)
        with self.assertRaises(ValueError):validate_next(self.root,self.plan,True)
if __name__=='__main__':unittest.main()
