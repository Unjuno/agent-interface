"""Portable import/continuation without a research checkout or desktop."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from runtime.distribution_v2.build import SOURCE_FILES, build
from runtime.core_v1.test_compiled_gui import interface

class CompiledArchiveTests(unittest.TestCase):
    def test_isolated_archive_has_graph_without_research_imports(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            snapshot = temporary / 'snapshot'
            for name in SOURCE_FILES:
                destination = snapshot / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(root / name, destination)
            archive = temporary / 'runtime.pyz'
            build(snapshot, archive, temporary / 'manifest.json', temporary / 'SHA256SUMS')
            code = """
import json,sys
sys.path.insert(0, sys.argv[1])
from runtime.core_v1.compiled_gui import run
spec = json.loads(sys.argv[2]); calls=[]
now=[0]
def observe(payload):
    now[0]=10000000
    return dict(sequence=1,captured_ns=0,surface='form',predicates={'phase':0},evidence_ref='frame',evidence_digest='digest')
def unexpected(payload):
    calls.append(payload)
    raise RuntimeError('late work reached an adapter')
result=run(spec,dict(observe=observe,admit=unexpected,execute=unexpected,verify_effect=unexpected,cancelled=lambda:False),clock=lambda:now[0])
if (result['outcome'],result['reason'])!=('SAFE_YIELD','budget_exhausted') or calls:
    raise RuntimeError('deadline continuation regression')
if any(name.startswith('research') for name in sys.modules):
    raise RuntimeError('research dependency in portable archive')
print('isolated archive compiled boundary passed')
"""
            result = subprocess.run([sys.executable, '-I', '-c', code, str(archive), json.dumps(interface())], cwd=temporary, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('isolated archive compiled boundary passed', result.stdout)
