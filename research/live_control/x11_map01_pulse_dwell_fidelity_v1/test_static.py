import importlib.util, json, pathlib, tempfile, unittest
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('audit',HERE/'audit.py'); audit=importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
class T(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(audit.MAX_DELTA_MS,5.0); self.assertEqual((audit.MIN_X_DWELL_MS,audit.MAX_X_DWELL_MS),(180,230))
    def test_pairing_positive(self):
        with tempfile.TemporaryDirectory() as td:
            d=pathlib.Path(td); ev=[]; ops=[]
            for i in range(6):
                t=1000+i*200; c=1_000_000_000+i*200_000_000
                ev += [{'kind':'press','keysym':'Right','keycode':114,'x_time_ms':t,'callback_ns':c},{'kind':'release','keysym':'Right','keycode':114,'x_time_ms':t+190,'callback_ns':c+190_000_000}]
                ops += [{'kind':'press','before_ns':c-1_000,'after_sync_ns':c},{'kind':'release','before_ns':c+190_000_000,'after_sync_ns':c+190_001_000}]
            (d/'events.json').write_text(json.dumps(ev)); (d/'controller.json').write_text(json.dumps({'ops':ops,'focus_after':5,'window_id':5,'final_right_down':False,'keycode':114}))
            errors,rows=audit.audit_case(d); self.assertEqual(errors,[]); self.assertEqual(len(rows),6)
    def test_extra_event_rejects(self):
        with tempfile.TemporaryDirectory() as td:
            d=pathlib.Path(td); (d/'events.json').write_text(json.dumps([{'kind':'press','keysym':'Right','keycode':114,'x_time_ms':1,'callback_ns':1}])); (d/'controller.json').write_text(json.dumps({'ops':[],'focus_after':1,'window_id':1,'final_right_down':False,'keycode':114}))
            errors,_=audit.audit_case(d); self.assertTrue(any('event_count' in e for e in errors))
if __name__=='__main__': unittest.main()
