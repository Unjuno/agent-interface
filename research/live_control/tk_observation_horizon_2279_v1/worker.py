"""Execute one instrumented copy of the pinned Tk preflight, never the archive's cases."""
import ast
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
import tkinter as tk

ORIGINAL_BLOB = 'f60bd81d37f574337d8aebb9a02fe35b12ab26fd'
SCENARIOS = {'fast': (.05, .20, False), 'delayed': (.35, .20, False),
             'absent': (None, .20, False), 'late': (.35, .50, False),
             'blocked_fast': (.05, .20, True), 'blocked_absent': (None, .20, True)}
OLD = '            state = "COMPLETED"\n            observed_at = time.monotonic() - start\n'
NEW = '            observed_at = time.monotonic() - start\n            state = "COMPLETED" if observed_at < horizon else "UNKNOWN"\n'

def program(policy, scenario):
    data = Path(__file__).with_name('predecessor.py').read_bytes()
    blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if blob != ORIGINAL_BLOB:
        raise ValueError('source mismatch')
    text = data.decode()
    if text.count(OLD) != 1:
        raise ValueError('unexpected decision block')
    if policy == 'POST_OBSERVATION':
        text = text.replace(OLD, NEW)
    elif policy != 'PRECHECK_ONLY':
        raise ValueError('unknown policy')
    # Only scenario selection and passive start instrumentation change the baseline AST.
    text = text.replace('    start = time.monotonic()\n',
                        '    start = time.monotonic()\n    record_start(start)\n')
    tree = ast.parse(text)
    delay, horizon, _ = SCENARIOS[scenario]
    assignments = [n for n in tree.body if isinstance(n, ast.Assign)
                   and isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'CASES']
    if len(assignments) != 1:
        raise ValueError('CASES shape mismatch')
    assignments[0].value = ast.parse(repr([(scenario, delay, horizon)]), mode='eval').body
    ast.fix_missing_locations(tree)
    return tree, hashlib.sha256(ast.dump(tree, include_attributes=False).encode()).hexdigest()

def execute(policy, scenario):
    tree, effective = program(policy, scenario)
    events = []
    def event(kind, **fields):
        events.append(dict(kind=kind, ns=time.monotonic_ns(), **fields))
    factory_root, factory_label = tk.Tk, tk.Label
    root_objects = []
    def make_root(*args, **kwargs):
        root = factory_root(*args, **kwargs)
        root_objects.append(root)
        update, destroy = root.update, root.destroy
        calls = 0
        def block():
            event('block_start')
            time.sleep(.30)
            event('block_end')
        def observed_update():
            nonlocal calls
            calls += 1
            if calls == 2 and SCENARIOS[scenario][2]:
                root.after(0, block)
                event('block_queued')
            event('update_start', call=calls)
            update()
            event('update_end', call=calls)
        def observed_destroy():
            destroy()
            event('destroyed')
        root.update, root.destroy = observed_update, observed_destroy
        root.report_callback_exception = lambda *a: event('callback_error', detail=str(a))
        event('root_created', tcl=str(root.tk.call('info', 'patchlevel')),
              tk=str(root.tk.call('package', 'provide', 'Tk')))
        return root
    def make_label(*args, **kwargs):
        label = factory_label(*args, **kwargs)
        configure, cget = label.config, label.cget
        def observed_config(*a, **kw):
            event('config_start', text=kw.get('text'))
            result = configure(*a, **kw)
            event('config_end', text=str(cget('text')))
            return result
        def observed_cget(option):
            event('read_start')
            value = cget(option)
            event('read_end', value=str(value))
            return value
        label.config, label.cget = observed_config, observed_cget
        return label
    stream = io.StringIO()
    tk.Tk, tk.Label = make_root, make_label
    try:
        with contextlib.redirect_stdout(stream):
            exec(compile(tree, 'pinned_preflight_instrumented', 'exec'),
                 {'record_start': lambda start: event('origin', seconds=start)})
        result = json.loads(stream.getvalue())
        event('worker_complete')
        return {'policy': policy, 'scenario': scenario, 'pid': os.getpid(),
                'effective_ast_sha256': effective, 'original_blob': ORIGINAL_BLOB,
                'result': result, 'original_stdout': stream.getvalue(), 'events': events,
                'grants_input_authority': False}
    finally:
        tk.Tk, tk.Label = factory_root, factory_label
        for root in root_objects:
            try:
                if root.winfo_exists():
                    root.destroy()
            except tk.TclError:
                pass

if __name__ == '__main__':
    print(json.dumps(execute(sys.argv[1], sys.argv[2]), separators=(',', ':')))
