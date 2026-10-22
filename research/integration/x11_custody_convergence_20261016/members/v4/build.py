import ast, hashlib, json, pathlib, shutil, textwrap

P = pathlib.Path(__file__).resolve().parent
OLD = P.parent / 'x11-unified-custody-01a0ff2c/sources/candidate'
PRIOR = P.parent / 'x11-sidebutton-construction-01a0ff2c'
sha = lambda b: hashlib.sha256(b).hexdigest()
backend_path = 'runtime/backends/x11_v1/backend.py'
test_path = 'runtime/backends/x11_v1/test_sidebutton_ledger.py'
assert sha((OLD / backend_path).read_bytes()) == 'f0ceebe949965435e6a08d69293dadd40b9c28a4ac9f892bab5a52fde3a0019f'

original = (PRIOR / 'test_sidebutton_v5.py').read_text(encoding='utf8')
start = original.index('def button_info(')
end = original.index("if __name__=='__main__':")
test = original[start:end]
test = test.replace('xinput.XIQueryVersion=version_request\nxinput.XIQueryDevice=device_request\nbackend.xtest.fake_input=lambda d,kind,number,**kw:d.send(kind,number,**kw)\n', '')
test = test.replace("        if ARM=='BASELINE':return\n", '')
setup = '''    def setUp(self):
        for target, value in (
            ("runtime.backends.x11_v1.backend.time", Clock),
            ("Xlib.ext.xinput.XIQueryVersion", version_request),
            ("Xlib.ext.xinput.XIQueryDevice", device_request),
            ("runtime.backends.x11_v1.backend.xtest.fake_input",
             lambda d, kind, number, **kw: d.send(kind, number, **kw)),
        ):
            patcher = mock.patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

'''
test = test.replace('class SideButtonTests(unittest.TestCase):\n', 'class SideButtonTests(unittest.TestCase):\n' + setup)
header = '''"""Owned side-button custody with real XI2 decoding and inert transport.

This suite does not qualify a native server, ClientPointer association, changing
device topology, or concurrent physical input. Patches are scoped per method.
"""
import json
import struct
import types
import unittest
from unittest import mock

from Xlib import X
from Xlib.ext import xinput
from runtime.backends.x11_v1 import backend, session
from runtime.core_v1 import contract

class Clock:
    @staticmethod
    def monotonic_ns():
        return 1

    @staticmethod
    def sleep(value):
        raise RuntimeError('unplanned sleep')

'''
test = header + test
assert len([n for n in ast.walk(ast.parse(test)) if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]) == 9

for arm in ('baseline', 'candidate', 'wrong_index'):
    dest = P / 'sources' / arm
    shutil.copytree(OLD, dest)
    (dest / test_path).write_bytes(test.encode('utf8'))

candidate = P / 'sources/candidate'
file = candidate / backend_path
source = file.read_text(encoding='utf8')
module = ast.parse(source)
method = next(n for n in ast.walk(module) if isinstance(n, ast.FunctionDef) and n.name == '_physical_buttons_down')
lines = source.splitlines(keepends=True)
prototype = (PRIOR / 'prototype_v3.py').read_text(encoding='utf8')
body = prototype[prototype.index('def physical_buttons_down'):]
body = body.replace('def physical_buttons_down(self):', 'def _physical_buttons_down(self) -> list[str]:')
body = body.replace('    mask=', '    # Core QueryPointer has only button 1-5 state bits.\n    mask=', 1)
body = body.replace('    devices=', '    # Union all master pointers conservatively. Native ClientPointer association,\n    # topology changes, and physical input remain separate qualification needs.\n    devices=', 1)
lines[method.lineno-1:method.end_lineno] = [textwrap.indent(body, '   ')]
source = ''.join(lines).replace('from Xlib.ext import xtest', 'from Xlib.ext import xtest, xinput', 1)
file.write_bytes(source.encode('utf8'))

for relative in ('.github/workflows/runtime-x11-v1.yml', 'runtime/integration_checks/native.py'):
    file = candidate / relative
    source = file.read_text(encoding='utf8')
    old = 'runtime.backends.x11_v1.test_explicit_up_ledger'
    assert source.count(old) == 1
    replacement = old + (' runtime.backends.x11_v1.test_sidebutton_ledger' if relative.endswith('.yml') else "', 'runtime.backends.x11_v1.test_sidebutton_ledger")
    file.write_bytes(source.replace(old, replacement).encode('utf8'))

negative = P / 'sources/wrong_index'
for f in candidate.rglob('*'):
    if f.is_file():
        (negative / f.relative_to(candidate)).write_bytes(f.read_bytes())
file = negative / backend_path
source = file.read_text(encoding='utf8')
assert source.count('state[number-1]') == 1
file.write_bytes(source.replace('state[number-1]', 'state[number]').encode('utf8'))
manifest = {arm: {f.relative_to(P/'sources'/arm).as_posix(): {'bytes': f.stat().st_size, 'sha256': sha(f.read_bytes())} for f in sorted((P/'sources'/arm).rglob('*')) if f.is_file()} for arm in ('baseline', 'candidate', 'wrong_index')}
(P/'SOURCE_MANIFEST.json').write_bytes((json.dumps(manifest, indent=2)+'\n').encode())
print(json.dumps({'source_files': {k: len(v) for k,v in manifest.items()}, 'methods':9, 'candidate_backend':manifest['candidate'][backend_path]}))
