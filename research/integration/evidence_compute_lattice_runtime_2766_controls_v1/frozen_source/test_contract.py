import tempfile, unittest
from pathlib import Path
from lattice import decide_cached, decide_active
from runtime_path import write_source,capture,decode_png,calibrate_profile

class T(unittest.TestCase):
    def test_cached(self):
        self.assertEqual(decide_cached([1],[2],1,100),'REBUILD_REQUIRED')
        self.assertEqual(decide_cached([1],[1],101,100),'DROP_EXPIRED')
        self.assertEqual(decide_cached([1],[1],100,100),'REUSE')
    def test_cached_exact_deadline_fixture(self):
        text=Path(__file__).with_name('run_case.py').read_text()
        self.assertIn("if a.case=='cached_reuse_at_deadline': deadline=t", text)
    def test_active_hard_gates(self):
        self.assertEqual(decide_active([1],[2],0,0,9,1,2,1,1),'CANCEL_STALE')
        self.assertEqual(decide_active([1],[1],9,1,9,1,2,1,1),'CANCEL_TARDY')
    def test_selector(self):
        self.assertEqual(decide_active([1],[1],0,0,9,1,4,8,1),'RUN')
        self.assertEqual(decide_active([1],[1],0,0,9,3,4,1,8),'WAIT')
        self.assertEqual(decide_active([1],[1],0,0,9,1,2,5,5),'TIE')
    def test_png_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            s=Path(td)/'s.json'; p=Path(td)/'a.png'; write_source(s,1,17); r=capture(s,p); self.assertEqual(len(decode_png(p.read_bytes())),32*32*3); self.assertEqual(r['source_version_before'],1)
    def test_calibration_sources(self):
        with tempfile.TemporaryDirectory() as td:
            s=Path(td)/'s.json'; p=Path(td)/'a.png'; write_source(s,1,17); capture(s,p); c=calibrate_profile('run',p,s); self.assertEqual((c['p_num'],c['p_den']),(1,4)); self.assertGreater(c['g_ns'],0); self.assertGreater(c['w_ns'],0)
if __name__=='__main__': unittest.main()
