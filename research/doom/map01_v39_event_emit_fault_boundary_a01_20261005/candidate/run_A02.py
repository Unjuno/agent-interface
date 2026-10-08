#!/usr/bin/env python3
import ast
import builtins
import hashlib
import json
import pathlib
import threading
import time
import tempfile
from unittest import mock

SRC = pathlib.Path('/src/session_map01_v12.py')
EXPECTED_SHA256 = '97d60f64ae6dc075fd7b18a452813c90d7c5d366d71e324905c17d74604585b2'
EXPECTED_GIT_BLOB = 'e701035302da4802e0db463035c4d653a7e7618b'
text = SRC.read_text(encoding='utf-8')
actual = hashlib.sha256(SRC.read_bytes()).hexdigest()
if actual != EXPECTED_SHA256:
    raise SystemExit('STOP_SOURCE_SHA256_MISMATCH')
tree = ast.parse(text)
main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
emit = next(n for n in main.body if isinstance(n, ast.FunctionDef) and n.name == 'emit')
if len(emit.body) != 5:
    raise SystemExit('STOP_EMIT_AST_SHAPE')

factory = ast.FunctionDef(name='factory', args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]), body=[
    ast.Assign(targets=[ast.Name(id='latest_observation', ctx=ast.Store())], value=ast.Constant(None)),
    ast.Assign(targets=[ast.Name(id='args', ctx=ast.Store())], value=ast.Name(id='argbox', ctx=ast.Load())),
    ast.Assign(targets=[ast.Name(id='lock', ctx=ast.Store())], value=ast.Call(func=ast.Name(id='RLock', ctx=ast.Load()), args=[], keywords=[])),
    emit,
    ast.Return(value=ast.Name(id='emit', ctx=ast.Load()))
], decorator_list=[])
mod = ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[]))
ns = {'argbox': None, 'RLock': threading.RLock, 'time': time, 'json': json}
exec(compile(mod, 'PINNED_MAIN_EMIT', 'exec'), ns)

class ArgBox:
    def __init__(self, out): self.out = pathlib.Path(out)

class FailOpen:
    def __init__(self, original, fault): self.original, self.fault, self.fired = original, fault, False
    def __call__(self, path, *args, **kwargs):
        if not self.fired and str(path).endswith(self.fault):
            self.fired = True
            raise OSError('injected open failure: ' + self.fault)
        return self.original(path, *args, **kwargs)

class FailPrint:
    def __init__(self, original): self.original, self.fired = original, False
    def __call__(self, *args, **kwargs):
        if not self.fired:
            self.fired = True
            raise OSError('injected stdout failure after both appends')
        return self.original(*args, **kwargs)

def counts(out):
    answer = {}
    for name in ('events.jsonl', 'delivered.jsonl'):
        p = pathlib.Path(out) / name
        rows = [json.loads(line) for line in p.read_text().splitlines()] if p.exists() else []
        answer[name] = {'rows': len(rows), 'release_ids': [r.get('id') for r in rows]}
    return answer

def logical_row():
    return {'event':'input_released', 'id':'probe-release-001', 'intent_token':'probe-token',
            'owner_release':{'event':'owner_release','verified':True,'keys_down':[],'buttons_down':[]},
            'grants_input_authority':False}

def run_case(name, fault_kind):
    with tempfile.TemporaryDirectory(prefix='emit-a01-') as d:
        out = pathlib.Path(d)
        fn = ns['factory'].__globals__
        ns['argbox'] = ArgBox(out)
        emit_fn = ns['factory']()
        orig_open = pathlib.Path.open
        orig_print = builtins.print
        caught = None
        with mock.patch.object(pathlib.Path, 'open', FailOpen(orig_open, 'events.jsonl' if fault_kind=='before_events_append' else 'delivered.jsonl') if fault_kind in ('before_events_append','after_events_before_delivered_append') else orig_open):
            with mock.patch('builtins.print', FailPrint(orig_print) if fault_kind=='after_delivered_before_stdout' else orig_print):
                try: emit_fn(logical_row())
                except OSError as e: caught = str(e)
        before = counts(out)
        if caught is not None:
            ns['argbox'] = ArgBox(out)
            emit_fn_retry = ns['factory']()
            emit_fn_retry(logical_row())
        after = counts(out)
        return {'name':name,'fault':fault_kind,'first_error':caught,'before_retry':before,'after_retry':after}

cases = [run_case('baseline',None),
         run_case('before_first_append','before_events_append'),
         run_case('after_first_append','after_events_before_delivered_append'),
         run_case('after_second_append','after_delivered_before_stdout')]
raw = {'schema':'event_emit_fault_boundary_a01_raw_v1','main_sha':'6a2826d391b77496b69752609a6f07b6971b4b6f',
       'source_git_blob':EXPECTED_GIT_BLOB,'source_sha256':actual,'event_id':'probe-release-001','cases':cases,
       'executor_policy_source_review':{'v12_blob':'7e9bb6286d5f674108688ba092300a8ad2421ba9',
       'v13_blob':'b9510765f34907bcfdbf25a5700e9d31d17c76b7',
       'attempt_recorded_before_emit':True,'automatic_retry':False,'failure_disposition':'delivery_unknown'}}
pathlib.Path('/out/RAW.json').write_text(json.dumps(raw,sort_keys=True,indent=2)+'\n')
print(json.dumps({'candidate':'COMPLETE','cases':len(cases),'source_sha256':actual},sort_keys=True))


