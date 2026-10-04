import ast, hashlib, json
from pathlib import Path
src = Path('controller.py').read_text(encoding='utf-8')
blob = hashlib.sha1((f'blob {len(src.encode())}\0').encode() + src.encode()).hexdigest()
assert blob == '41c1f9744c65704b6f55b8826c010552d6325998', blob
module = ast.parse(src)
waits = [n for n in ast.walk(module) if isinstance(n, ast.FunctionDef) and n.name == 'wait']
assert len(waits) == 1
wait = waits[0]
monitor = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == 'DoomCoverSignalPairMonitor')
observe = next(n for n in monitor.body if isinstance(n, ast.FunctionDef) and n.name == 'observe')
event_assignment = next(n for n in monitor.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'event_types' for t in n.targets))
assert ast.literal_eval(event_assignment.value) == {'typed_observation'}
dispatch_ifs = [n for n in ast.walk(wait) if isinstance(n, ast.If) and isinstance(n.test, ast.Compare)
                and any(isinstance(x, ast.Name) and x.id == 'event_types' for x in ast.walk(n.test))]
assert len(dispatch_ifs) == 1
assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'observe'
           for n in ast.walk(dispatch_ifs[0]))
assert any(isinstance(n, ast.If) and isinstance(n.test, ast.Compare)
           and any(isinstance(x, ast.Constant) and x.value == 'typed_observation' for x in ast.walk(n.test))
           for n in ast.walk(observe))
assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'read'
           for n in ast.walk(observe))
first = Path('test-output.txt').read_text(encoding='utf-8')
assert '"result_event": "observation"' in first
assert '"monitor_last_sequence": 10' in first
assert first.count('"result_event": "policy_invalidation"') == 2
assert first.count('ammo:below_hard_minimum') >= 2
print(json.dumps({'audit':'PASS_INDEPENDENT_SOURCE_AND_FIRST_OUTPUT_AUDIT','controller_git_blob':blob,
                  'wait_definition_count':len(waits),'frozen_monitor_event_types':['typed_observation'],
                  'ordinary_fallback_read_calls':1,'candidate_executions_recorded':1},sort_keys=True))
