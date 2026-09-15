import pathlib,re,unittest
HERE=pathlib.Path(__file__).resolve().parent
class Static(unittest.TestCase):
    def test_fork_isolated(self):
        self.assertTrue((HERE/'backend_text.go').is_file())
        self.assertNotIn('research/runtime_native_x11_v0',str(HERE))
    def test_text_subset_explicit(self):
        s=(HERE/'backend_text.go').read_text()
        self.assertIn('TEXT_SUBSET_UNSUPPORTED',s); self.assertIn('native-x11-text-v1',s)
    def test_timing_receipts_present(self):
        s=(HERE/'backend_text.go').read_text()
        self.assertIn('TextCharDurationsNS',s); self.assertIn('TextCharStartIntervalsNS',s)
    def test_stale_receipt_is_explicit(self):
        s=(HERE/'run_arm.py').read_text()
        self.assertIn("injected_events')==0",s)
        self.assertIn("STALE_OBSERVATION",s)
if __name__=='__main__': unittest.main()
