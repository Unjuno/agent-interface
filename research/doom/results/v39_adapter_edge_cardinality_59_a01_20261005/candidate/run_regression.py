import ast
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path('/src')
source_path = ROOT / 'map01_overlap_controller_v39.py'
test_path = ROOT / 'test_map01_v39_typed_state_feedback.py'
source_bytes = source_path.read_bytes()
test_bytes = test_path.read_bytes()
source_sha = hashlib.sha256(source_bytes).hexdigest()
test_sha = hashlib.sha256(test_bytes).hexdigest()
if source_sha != '888c3a8f5ea682e0e63d4f63c71a737877829c5a893b427de118d1be958fba8a':
    raise SystemExit('source SHA mismatch')
if test_sha != 'bdd7092901ab6faad926a86333848b4a5c51d23b0a43aa51537f6974f66b571d':
    raise SystemExit('test SHA mismatch')

controller_tree = ast.parse(source_bytes.decode('utf-8'))
projector = next(node for node in controller_tree.body
                 if isinstance(node, ast.FunctionDef) and node.name == 'input_edge_receipts')
controller_module = ast.Module(
    body=[ast.Import(names=[ast.alias(name='hashlib')]), projector], type_ignores=[])
controller_ns = {}
exec(compile(ast.fix_missing_locations(controller_module), 'exact-controller', 'exec'), controller_ns)

test_tree = ast.parse(test_bytes.decode('utf-8'))
original_class = next(node for node in test_tree.body
                      if isinstance(node, ast.ClassDef) and node.name == 'V39TypedStateFeedbackTests')
method = next(node for node in original_class.body
              if isinstance(node, ast.FunctionDef) and
              node.name == 'test_input_edge_receipt_rejects_duplicate_adapter_rows')
case_class = ast.ClassDef(
    name='CardinalityRegressionTests',
    bases=[ast.Attribute(value=ast.Name(id='unittest', ctx=ast.Load()), attr='TestCase', ctx=ast.Load())],
    keywords=[], body=[method], decorator_list=[])
test_module = ast.Module(
    body=[ast.Import(names=[ast.alias(name='json')]),
          ast.Import(names=[ast.alias(name='unittest')]), case_class],
    type_ignores=[])
test_ns = {'HERE': ROOT, 'controller': controller_ns['input_edge_receipts']}
exec(compile(ast.fix_missing_locations(test_module), 'exact-cardinality-test', 'exec'), test_ns)
suite = unittest.defaultTestLoader.loadTestsFromTestCase(test_ns['CardinalityRegressionTests'])
result = unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful():
    raise SystemExit(1)

import py_compile
py_compile.compile(str(source_path), cfile='/tmp/controller.pyc', doraise=True)
py_compile.compile(str(test_path), cfile='/tmp/test_module.pyc', doraise=True)
resource = {}
for name, path in (('cpu_max', '/sys/fs/cgroup/cpu.max'),
                   ('memory_max', '/sys/fs/cgroup/memory.max'),
                   ('memory_swap_max', '/sys/fs/cgroup/memory.swap.max')):
    try: resource[name] = Path(path).read_text().strip()
    except OSError: resource[name] = 'UNAVAILABLE'
report = {'result': 'PASS', 'test': method.name, 'test_cases': 1,
          'subcases': 5, 'source_sha256': source_sha, 'test_sha256': test_sha,
          'py_compile': 'PASS', 'resource_snapshot': resource}
Path('/out/parent-81c-regression-result.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
