import ast, hashlib, json, py_compile, unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path('/src')
SOURCE = ROOT / 'map01_overlap_controller_v39.py'
TEST = ROOT / 'test_map01_v39_typed_state_feedback.py'
EXPECTED_SOURCE_SHA256 = '41329ce5735aa80b0cb6710c10f2c2bf9627f3b22e57faf197cf37eef335129a'
EXPECTED_TEST_SHA256 = 'b82a97f32d51749988df059c963ccc163dfbfe5f294ff33aebcc39854173fb5b'
source_bytes = SOURCE.read_bytes()
test_bytes = TEST.read_bytes()
source_sha = hashlib.sha256(source_bytes).hexdigest()
test_sha = hashlib.sha256(test_bytes).hexdigest()
if source_sha != EXPECTED_SOURCE_SHA256:
    raise SystemExit('current controller SHA256 mismatch')
if test_sha != EXPECTED_TEST_SHA256:
    raise SystemExit('current committed test SHA256 mismatch')

source_tree = ast.parse(source_bytes.decode('utf-8'))
projector = next(n for n in source_tree.body
                 if isinstance(n, ast.FunctionDef) and n.name == 'input_edge_receipts')
controller_module = ast.Module(
    body=[ast.Import(names=[ast.alias(name='hashlib')]), projector], type_ignores=[])
controller_ns = {}
exec(compile(ast.fix_missing_locations(controller_module), 'pinned-current-controller', 'exec'), controller_ns)

test_tree = ast.parse(test_bytes.decode('utf-8'))
test_class = next(n for n in test_tree.body
                  if isinstance(n, ast.ClassDef) and n.name == 'V39TypedStateFeedbackTests')
method = next(n for n in test_class.body
              if isinstance(n, ast.FunctionDef) and
              n.name == 'test_input_edge_receipt_rejects_duplicate_adapter_rows')
runner_class = ast.ClassDef(
    name='CurrentCardinalityRegression',
    bases=[ast.Attribute(value=ast.Name(id='unittest', ctx=ast.Load()),
                         attr='TestCase', ctx=ast.Load())],
    keywords=[], body=[method], decorator_list=[])
module = ast.Module(
    body=[ast.Import(names=[ast.alias(name='json')]),
          ast.Import(names=[ast.alias(name='unittest')]),
          ast.ImportFrom(module='types', names=[ast.alias(name='SimpleNamespace')], level=0),
          runner_class], type_ignores=[])
namespace = {'HERE': ROOT, 'controller': SimpleNamespace(
    input_edge_receipts=controller_ns['input_edge_receipts'])}
exec(compile(ast.fix_missing_locations(module), 'pinned-current-cardinality-test', 'exec'), namespace)
suite = unittest.defaultTestLoader.loadTestsFromTestCase(namespace['CurrentCardinalityRegression'])
result = unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful():
    raise SystemExit(1)
py_compile.compile(str(SOURCE), cfile='/tmp/current-controller.pyc', doraise=True)
py_compile.compile(str(TEST), cfile='/tmp/current-test.pyc', doraise=True)
resource = {}
for name, path in (('cpu_max', '/sys/fs/cgroup/cpu.max'),
                   ('memory_max', '/sys/fs/cgroup/memory.max'),
                   ('memory_swap_max', '/sys/fs/cgroup/memory.swap.max')):
    try: resource[name] = Path(path).read_text().strip()
    except OSError: resource[name] = 'UNAVAILABLE'
report = {'result':'PASS', 'test':method.name, 'unittest_methods':1, 'duplicate_subcases':5,
          'controller_sha256':source_sha, 'test_sha256':test_sha,
          'py_compile':'PASS', 'resource_snapshot':resource}
Path('/out/a02b-current-regression-result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
