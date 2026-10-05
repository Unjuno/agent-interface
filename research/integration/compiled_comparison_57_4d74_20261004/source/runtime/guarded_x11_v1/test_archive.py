"""Linux/X11 dependency-bearing archive integration; never opens a display."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from runtime.distribution_v2.build import build

class GuardedArchiveTests(unittest.TestCase):
    def test_guarded_api_imports_from_archive_without_research_checkout(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            archive = td/'runtime.pyz'
            build(root, archive, td/'manifest.json', td/'sum')
            code = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from runtime.guarded_x11_v1 import bridge, handles, form, compiled
from PIL import Image
assert Path(bridge.__file__).is_relative_to(Path(sys.argv[1]))
assert Path(compiled.__file__).is_relative_to(Path(sys.argv[1]))
assert callable(compiled.run)
assert not any(name.startswith('native_') or name.startswith('scoped_target_') for name in sys.modules)
image = Image.new('RGB', (100, 100), 'white')
for i in range(10):
    image.putpixel((20+i, 20+i%3), (i*20, 10, 255-i))
observation = {'sequence': 1, 'capture_ns': 1000000,
    'pointer_binding': {'focus': 10, 'surface': 20, 'geometry': [0,0,100,100]}}
store = handles.TargetHandleStore('archive')
store.mint('field', 'window_content', [20,20,12,8], observation, image, 1000100)
assert store.resolve_point('field', [3,3], observation, image, 1000200,
    session_scope='archive')['point'] == [23,23]
image.paste('black', (20,20,32,28))
assert store.resolve_point('field', [3,3], observation, image, 1000300,
    session_scope='archive')['status'] != 'VALID'
events = []
class Bridge:
    def click(self, alias, offset, **kwargs):
        events.append(alias)
        return {'status':'completed','recovery_required':False,
            'execution':{'releases':[{'verified':True,'keys_down':[],'buttons_down':[]}]}}
result = form.fill_and_submit(Bridge(), {'field':('field',[3,3]), 'submit':('save',[2,2])},
    'text', wait_ms=0, on_step=lambda name, result: events.append(name))
assert events == ['field','entered','save','saved']
assert result['task_success'] is None and result['replay_allowed'] is False
print('archive guarded API passed')
"""
            run = subprocess.run([sys.executable, '-I', '-c', code, str(archive)],
                                 cwd=td, capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn('archive guarded API passed', run.stdout)
