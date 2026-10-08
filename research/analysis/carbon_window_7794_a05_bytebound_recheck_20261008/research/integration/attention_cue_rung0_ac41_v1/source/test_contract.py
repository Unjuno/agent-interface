import copy
import json
from pathlib import Path
import time
import unittest
from engine import package
from audit import verify_case
from controls import changed_cases

ROOT=Path(__file__).resolve().parent.parent
class Contract(unittest.TestCase):
    def setUp(self):
        self.base=json.loads((ROOT/'construction/b1/c0/case.json').read_text())
    def request(self):
        r=copy.deepcopy(self.base['request']); r['cue']['emitted_ns']=time.monotonic_ns(); return r
    def test_valid(self): self.assertEqual(package(self.request())['reason'],'ACCEPTED')
    def test_autonomous(self):
        r=self.request(); r['cue']=None; o=package(r); self.assertEqual(o['reason'],'NO_CUE');self.assertEqual(o['decoded_bytes'],3072)
    def test_generation(self):
        r=self.request();r['cue']['generation']=2;self.assertEqual(package(r)['reason'],'GENERATION')
    def test_authority(self):
        r=self.request();r['cue']['authority_granted']=True;o=package(r);self.assertEqual(o['reason'],'SCHEMA');self.assertFalse(o['authority_granted'])
    def test_roi(self):
        r=self.request();r['cue']['roi']=[63,47,16,16];self.assertEqual(package(r)['reason'],'ROI')
    def test_missing(self):
        r=self.request();r['frames']=r['frames'][-1:];o=package(r);self.assertEqual(o['history'],'MISSING_HISTORY');self.assertEqual(len(o['frames']),1)
    def test_bool_generation(self):
        r=self.request();r['cue']['generation']=True;self.assertEqual(package(r)['reason'],'SCHEMA')
    def test_future(self):
        r=self.request();r['cue']['emitted_ns']+=10_000_000_000;self.assertEqual(package(r)['reason'],'TIME')
    def test_expired(self):
        r=self.request();r['cue']['emitted_ns']-=3_000_000_000;self.assertEqual(package(r)['reason'],'TIME')
    def test_never_action(self):
        o=package(self.request());self.assertIsNone(o['action']);self.assertFalse(o['lease_extended'])
    def test_raw_baseline(self): self.assertEqual(verify_case(self.base)['errors'],[])
    def test_effective_controls(self):
        for name,o in changed_cases(self.base):
            with self.subTest(name=name):
                self.assertNotEqual(o,self.base);errors=verify_case(o)['errors'];self.assertTrue(errors);self.assertFalse(any(e.startswith('malformed:') for e in errors))
if __name__=='__main__': unittest.main(verbosity=2)
