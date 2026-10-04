import unittest
from audit_commands import admit_freeze_bytes

class FreezeBytes(unittest.TestCase):
    def test_exact_frozen_bytes(self):admit_freeze_bytes(b'{"mode":"readiness"}',b'{"mode":"readiness"}')
    def test_different_supplied_freeze_rejected_before_execution(self):
        with self.assertRaises(ValueError):admit_freeze_bytes(b'{"mode":"formal"}',b'{"mode":"readiness"}')
        with self.assertRaises(ValueError):admit_freeze_bytes(b'',b'')

if __name__=='__main__':unittest.main()
