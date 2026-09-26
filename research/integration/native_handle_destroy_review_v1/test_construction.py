import pathlib, sys, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from audit import audit

class Construction(unittest.TestCase):
    def test_audit_rejects_missing(self):
        self.assertTrue(audit({'mode':'formal','sessions':[]})['errors'])
    def test_source_pin_is_literal_in_runner(self):
        text=(pathlib.Path(__file__).resolve().parent/'run.py').read_text()
        self.assertIn("'research/live_control/native_handle_bridge_v1.py':'aa72a835a60ab9bf9f053c680a1a3d81e49c14d5'", text)

if __name__=='__main__': unittest.main(verbosity=2)
