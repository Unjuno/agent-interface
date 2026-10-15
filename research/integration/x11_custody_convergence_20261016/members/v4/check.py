import ast, hashlib, json, os, pathlib, shlex, sys, unittest

P = pathlib.Path(__file__).resolve().parent
arm, route = sys.argv[1:3]
source = P/'sources'/arm
sys.path.insert(0, str(source))
deps = P.parent/'x11-package-import-01a0ff2c/dependencies'
for wheel in sorted(deps.glob('*.whl')):
    sys.path.insert(0, str(wheel))
events, displays = [], []
def audit(event, args):
    if event in {'socket.__new__','socket.connect','socket.bind','subprocess.Popen','os.system','ctypes.dlopen'}:
        events.append(event)
        raise RuntimeError('forbidden '+event)
sys.addaudithook(audit)
from Xlib import display
def forbidden(*args, **kwargs):
    displays.append('Display')
    raise RuntimeError('native Display forbidden')
display.Display = forbidden
from runtime.backends.x11_v1 import backend, session
from runtime.core_v1 import contract
for mod in (backend, session, contract):
    if not pathlib.Path(mod.__file__).resolve().is_relative_to(source.resolve()):
        raise RuntimeError('wrong source origin')

def selectors(root):
    workflow = (root/'.github/workflows/runtime-x11-v1.yml').read_text(encoding='utf8')
    command = next(line for line in workflow.splitlines() if 'python -m unittest -v runtime.backends.x11_v1.test_integration' in line)
    tokens = shlex.split(command)
    workflow_names = tokens[tokens.index('-v')+1:]
    parsed = ast.parse((root/'runtime/integration_checks/native.py').read_text(encoding='utf8'))
    assignment = next(n for n in parsed.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id=='SUITES' for t in n.targets))
    suites = ast.literal_eval(assignment.value)
    for n in parsed.body:
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call):
            call = n.value
            if isinstance(call.func, ast.Attribute) and call.func.attr=='append' and isinstance(call.func.value, ast.Subscript):
                value = call.func.value
                if isinstance(value.value, ast.Name) and value.value.id=='SUITES':
                    suites[ast.literal_eval(value.slice)].append(ast.literal_eval(call.args[0]))
    return {'workflow':workflow_names, 'native_harness':suites['harness'], 'native_protocol':suites['protocol']}

selection = selectors(source)
side = 'runtime.backends.x11_v1.test_sidebutton_ledger'
if arm != 'baseline':
    before = selectors(P/'sources/baseline')
    for name in ('workflow','native_harness'):
        if selection[name].count(side)!=1 or [x for x in selection[name] if x!=side]!=before[name]:
            raise RuntimeError('selector addition changed previous selection/order')
    if selection['native_protocol']!=before['native_protocol']:
        raise RuntimeError('changed protocol')
targets = [side] if route=='side_only' else [x for x in selection['workflow'] if x in (
    'runtime.backends.x11_v1.test_mapping_boundary', 'runtime.backends.x11_v1.test_text_plan',
    'runtime.backends.x11_v1.test_partial_execution', 'runtime.backends.x11_v1.test_scroll_ledger',
    'runtime.backends.x11_v1.test_explicit_up_ledger', side)]
suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(x) for x in targets)
def flatten(value):
    for item in value:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item.id()
names = list(flatten(suite))
result = unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps({'actor_pid':os.getpid(), 'arm':arm, 'route':route, 'targets':targets,
                 'method_names':names, 'methods':result.testsRun, 'failures':len(result.failures),
                 'errors':len(result.errors), 'skips':len(result.skipped), 'forbidden':events,
                 'native_display_calls':displays, 'selection':selection,
                 'scope':'selected inert modules; not entire workflow/harness/native'}, sort_keys=True))
sys.exit(0 if result.wasSuccessful() and not result.skipped and not events and not displays else 1)
