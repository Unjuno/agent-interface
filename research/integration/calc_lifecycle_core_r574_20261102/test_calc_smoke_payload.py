import json
import runpy
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

class SmokePayloadTests(unittest.TestCase):
    def test_error_after_window_observation_exits_nonzero(self):
        script = Path(__file__).with_name('calc_smoke_payload.py')
        real_path = Path
        with tempfile.TemporaryDirectory() as directory:
            root = real_path(directory)
            def mapped(path, *args, **kwargs):
                if isinstance(path, str) and path.startswith('/tmp/'):
                    return root / path[5:]
                return real_path(path, *args, **kwargs)
            class Child:
                id=42
                def get_wm_name(self): return 'Untitled - LibreOffice Calc'
                def get_attributes(self): return types.SimpleNamespace(map_state=2)
                def query_tree(self): return types.SimpleNamespace(children=[])
            class Root:
                def query_tree(self): return types.SimpleNamespace(children=[Child()])
                def get_image(self,*args): return types.SimpleNamespace(data=b'pixels')
            class Display:
                def __init__(self,*args): pass
                def screen(self): return types.SimpleNamespace(root=Root())
                def close(self): pass
            class Process:
                def __init__(self,*args,**kwargs): pass
                def poll(self): return None
                def terminate(self): pass
                def wait(self,timeout=None): return 0
            def sleep(seconds):
                if seconds == 20: raise RuntimeError('failure after window observation')
            def save(path): mapped(path).write_bytes(b'png')
            xlib=types.ModuleType('Xlib');xlib.X=types.SimpleNamespace(IsViewable=2,ZPixmap=2);xlib.display=types.SimpleNamespace(Display=Display)
            pil=types.ModuleType('PIL');pil.Image=types.SimpleNamespace(frombytes=lambda *a,**k:types.SimpleNamespace(save=save))
            sig=types.ModuleType('signal');sig.SIGALRM=14;sig.signal=lambda *a:None;sig.alarm=lambda *a:None
            with patch.dict('sys.modules', {'Xlib':xlib,'PIL':pil,'signal':sig}), \
                 patch('pathlib.Path',side_effect=mapped), \
                 patch('subprocess.Popen',Process), patch('time.sleep',side_effect=sleep):
                with self.assertRaises(SystemExit) as ex:runpy.run_path(str(script),run_name='__main__')
            self.assertEqual(ex.exception.code,1)
            report=json.loads((root/'calc-smoke.json').read_text())
            self.assertEqual(report['status'],'error')
            self.assertEqual(report['error_type'],'RuntimeError')
            self.assertTrue((root/'calc-ready.json').exists())

if __name__=='__main__':unittest.main()
