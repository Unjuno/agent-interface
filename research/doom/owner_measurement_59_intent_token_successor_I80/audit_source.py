from __future__ import annotations
import ast
import hashlib
import importlib.util
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = '12e4c1ebaf382d70760eafbe3cf2e5fda90a9d2c'

def check(condition, message):
    if not condition:
        raise SystemExit('FAIL: ' + message)

source = subprocess.check_output(['git', 'show', BASE + ':research/live_control/input_owner_v10.py'], cwd=ROOT)
check(hashlib.sha256(source).hexdigest() == 'ceae7d9983cd0ba13a35e01ce2ce7dbbf03a0397b23ddc123b0110b4d4de670b', 'input owner pin mismatch')
base_builder = subprocess.check_output(['git', 'show', 'HEAD:research/doom/owner_measurement_59_5ce3_20261004/build_owner.py'], cwd=ROOT).decode('utf-8-sig')
expected_builder = base_builder.replace("intent=getattr(lease, 'token', None)", 'intent=_measurement_intent(lease)')
expected_builder = expected_builder.replace('def _measurement_now(clock):', "def _measurement_intent(lease):\n    value = getattr(lease, 'intent_token', None)\n    return value if isinstance(value, str) and value else None\n\ndef _measurement_now(clock):")
actual_builder = (HERE / 'build_owner.py').read_text(encoding='utf-8-sig')
check(actual_builder.replace('\r\n', '\n') == expected_builder.replace('\r\n', '\n'), 'candidate builder contains changes outside the intended accessor patch')
spec = importlib.util.spec_from_file_location('audited_builder', HERE / 'build_owner.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
generated = builder.instrument(source)
tree = ast.parse(generated)
helpers = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name.startswith('_measurement_')}
check('_measurement_intent' in helpers, 'intent accessor missing')
check("getattr(lease, 'token'" not in generated, 'legacy token lookup remains')
accessor = ast.unparse(helpers['_measurement_intent'])
check("getattr(lease, 'intent_token', None)" in accessor, 'accessor does not use current lease field')
for name in ('_measurement_emit', '_measurement_mark'):
    check('_measurement_intent(lease)' in ast.unparse(helpers[name]), name + ' does not bind lease identity')
for name in ('lease.py', 'lease_cause_v1.py'):
    check((HERE / name).read_bytes() == (ROOT / 'research/live_control' / name).read_bytes(), 'copied lease source differs from current main: ' + name)
lease_cause = (HERE / 'lease_cause_v1.py').read_text(encoding='utf-8-sig')
check('self.intent_token = uuid.uuid4().hex' in lease_cause, 'actual Lease implementation changed')
check('self.token =' not in lease_cause and 'def token(' not in lease_cause, 'fixture unexpectedly adds legacy alias')
print('PASS_SOURCE_IDENTITY_BINDING')
print('source_sha256=' + hashlib.sha256(source).hexdigest())
print('generated_sha256=' + hashlib.sha256(generated.encode()).hexdigest())
print('helper_names=' + ','.join(sorted(helpers)))
