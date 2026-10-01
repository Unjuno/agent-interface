"""Pure construction/regression checks. No archived script is executed."""
import unittest
from verify_readonly import CHANGES, changed_record, encoded, require, blob_id

class Construction(unittest.TestCase):
    def test_twelve_unique(self):
        self.assertEqual(len(CHANGES),12)
        self.assertEqual(len({n for n,_,_ in CHANGES}),12)
    def test_boolean_numeric_change_is_effective(self):
        obj={'x':False}; out=changed_record(obj,['x'],0)
        self.assertNotEqual(encoded(obj),encoded(out))
        self.assertIs(obj['x'],False)
    def test_deep_copy(self):
        obj={'x':[{'a':1}]};out=changed_record(obj,['x',0,'a'],7)
        self.assertEqual(obj,{'x':[{'a':1}]});self.assertEqual(out,{'x':[{'a':7}]})
    def test_noop_refused(self):
        with self.assertRaises(ValueError):changed_record({'x':3},['x'],3)
    def test_require(self):
        with self.assertRaises(ValueError):require(False,'expected')
    def test_empty_blob(self):
        self.assertEqual(blob_id(b''),'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391')
if __name__=='__main__':unittest.main()
