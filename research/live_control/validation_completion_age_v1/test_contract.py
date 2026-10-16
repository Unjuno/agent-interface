"""No live experiment is invoked by these construction tests."""
import unittest
from candidate import finalize
import legacy_transport as legacy
from audit import from_directory,controls,load_text
from pathlib import Path

class ContractTests(unittest.TestCase):
    def setUp(self):self.meta={'capture_start_ns':100,'capture_end_ns':110}
    def test_inside(self):self.assertEqual(finalize('FRAME_FRESH',self.meta,120,130,30),'FRESH_AT_VALIDATION_SAMPLE')
    def test_outside(self):self.assertEqual(finalize('FRAME_FRESH',self.meta,120,131,30),'YIELD_STALE_AT_VALIDATION')
    def test_preserve_stale(self):self.assertEqual(finalize('YIELD_STALE',self.meta,120,130,300),'YIELD_STALE')
    def test_preserve_invalid(self):self.assertEqual(finalize('YIELD_INVALID',None,120,130),'YIELD_INVALID')
    def test_bad_clocks(self):
        for x in [True,None,-1,1.0,'1']:
            with self.subTest(x=x):self.assertEqual(finalize('FRAME_FRESH',self.meta,120,x),'YIELD_INVALID')
    def test_reversal(self):self.assertEqual(finalize('FRAME_FRESH',self.meta,130,120),'YIELD_INVALID')
    def test_future_capture(self):self.assertEqual(finalize('FRAME_FRESH',{'capture_start_ns':121,'capture_end_ns':122},120,130),'YIELD_INVALID')
    def test_unknown_status(self):self.assertEqual(finalize('DONE',self.meta,120,130),'YIELD_INVALID')
    def test_hash_equivalence(self):
        for data in [b'',b'a'*4096,bytes(range(256))*16]:self.assertEqual(legacy.pixel_digest(data,False),legacy.pixel_digest(data,True))
    def test_raw_construction(self):
        _,_,result=from_directory(Path(__file__).with_name('construction04'),0,True)
        self.assertEqual(result['errors'],[]);self.assertTrue(all(r['boundary_gate'] for r in result['rows']))
    def test_mutations(self):
        s,r,_=from_directory(Path(__file__).with_name('construction04'),0,True)
        result=controls(s,r,0,True);self.assertEqual(len(result),12);self.assertTrue(all(result.values()))
    def test_duplicate_json(self):
        with self.assertRaises(ValueError):load_text('{"a":1,"a":2}')
if __name__=='__main__':unittest.main()
