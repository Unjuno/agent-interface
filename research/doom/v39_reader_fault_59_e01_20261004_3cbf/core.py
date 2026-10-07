import ast
import hashlib
import json
import queue
import time

SOURCE_HASH = 'a0bcfa076970b7cf6d048155478952958280b7958e0bbe486c0f1f12a55e4f0e'

def extract(source):
    digest = hashlib.sha256(source).hexdigest()
    if digest != SOURCE_HASH:
        raise ValueError('source identity mismatch')
    tree = ast.parse(source.decode('utf-8'))
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    nodes = [n for n in main.body if isinstance(n, ast.FunctionDef) and n.name in ('reader', 'wait')]
    if [n.name for n in nodes] != ['reader', 'wait']:
        raise ValueError('unexpected source structure')
    factory = ast.parse('def factory(process, incoming):\n latest = None\n all_events = []\n').body[0]
    factory.body.extend(nodes)
    factory.body.extend(ast.parse('return reader, wait, all_events').body)
    module = ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[]))
    scope = dict(json=json, queue=queue, time=time)
    exec(compile(module, 'pinned-v39-reader-wait', 'exec'), scope)
    return scope['factory'], dict(sha256=digest, functions=[n.name for n in nodes],
        ast_sha256=hashlib.sha256(ast.dump(ast.Module(body=nodes,type_ignores=[])).encode()).hexdigest())

def judge(rows):
    if len(rows) != 3 or [r['case'] for r in rows] != ['healthy','malformed','array']:
        return 'STOP_CUSTODY_OR_CLEANUP'
    if any(r.get('fatal') or r.get('cleanup_faults') or type(r['reader_alive']) is not bool
           or r['child_alive'] is not True or type(r['cleanup_exit']) is not int
           or r['cleanup_exit'] != 0 or r['reader_retired'] is not True for r in rows):
        return 'STOP_CUSTODY_OR_CLEANUP'
    expected = [('ready',True,[]),('TimeoutError',False,['JSONDecodeError']),('TypeError',True,[])]
    if any((r['outcome'],r['reader_alive'],r['errors']) != e for r,e in zip(rows,expected)):
        return 'HOLD_EXPECTATION_NOT_MET'
    return 'FINDING_PARSE_FAILURE_NOT_SURFACED'
