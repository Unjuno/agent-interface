"""Finite real subprocess stdout-pipe boundary, no GUI/model/native allocation replay."""
import ast
import hashlib
import json
from pathlib import Path
import queue
import subprocess
import sys
import tarfile
import threading
import time

CASES = [('original_fault', 'v39-original.py.txt', 'not-json\n'),
         ('candidate_fault', 'v39-candidate.py.txt', 'not-json\n'),
         ('candidate_healthy', 'v39-candidate.py.txt', '{"event":"ready"}\n'),
         ('candidate_eof_alive', 'v39-candidate.py.txt', '')]


def factory(source):
    main = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    nodes = [n for n in main.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))
             and n.name in ('reader', 'wait', '_SessionReaderFailure')]
    if [n.name for n in nodes] not in (['reader', 'wait'], ['_SessionReaderFailure', 'reader', 'wait']):
        raise ValueError('unexpected extraction')
    create = ast.parse('def create(process, incoming):\n latest=None\n all_events=[]\n').body[0]
    create.body.extend(nodes)
    create.body.extend(ast.parse('return reader, wait, all_events').body)
    scope = dict(json=json, queue=queue, time=time)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[create], type_ignores=[])), 'exact-reader-f01', 'exec'), scope)
    return scope['create']


def run(archive, output):
    output.mkdir(exist_ok=False)
    oldhook = threading.excepthook
    rows = []
    try:
        with tarfile.open(archive, 'r:gz') as source:
            for case, name, wire in CASES:
                code = source.extractfile('research/doom/v39_reader_signal_59_e02_20261004_3cbf/source/' + name).read()
                expected = {'v39-original.py.txt': 'a0bcfa076970b7cf6d048155478952958280b7958e0bbe486c0f1f12a55e4f0e',
                            'v39-candidate.py.txt': 'dca770e5e0c532b301b12032c9532bd5fae602947caff4fff21bde60634a57f1'}[name]
                if hashlib.sha256(code).hexdigest() != expected:
                    raise ValueError('source hash')
                errors = []
                threading.excepthook = lambda event: errors.append({'type': event.exc_type.__name__, 'thread': event.thread.name})
                script = 'import os,sys,time; sys.stdout.write(sys.argv[1]); sys.stdout.flush(); os.close(1); time.sleep(3)'
                child = subprocess.Popen([sys.executable, '-u', '-c', script, wire], stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, text=True, encoding='utf-8')
                thread = None
                row = {'case': case, 'source_sha256': expected, 'wire': wire,
                       'child_pid': child.pid, 'start_ns': time.perf_counter_ns()}
                try:
                    reader, wait, events = factory(code)(child, queue.Queue())
                    thread = threading.Thread(target=reader, name='f01-exact-reader')
                    thread.start()
                    row['wait_start_ns'] = time.perf_counter_ns()
                    try:
                        row['ready'] = wait(lambda event: event.get('event') == 'ready', timeout=.35)
                        row['outcome'] = 'ready'; row['cause'] = None
                    except Exception as error:
                        row['outcome'] = type(error).__name__
                        row['cause'] = type(error.__cause__).__name__ if error.__cause__ else None
                    row['wait_end_ns'] = time.perf_counter_ns()
                    thread.join(1)
                    row.update(reader_alive=thread.is_alive(), child_alive=child.poll() is None,
                               unhandled=errors, events=events)
                finally:
                    child.terminate()
                    child.wait(timeout=2)
                    child.stdout.close(); child.stderr.close()
                    if thread is not None:
                        thread.join(1)
                    row['cleanup_child_exit'] = child.returncode
                    row['end_ns'] = time.perf_counter_ns()
                rows.append(row)
                (output / (case + '.json')).write_text(json.dumps(row, sort_keys=True) + '\n')
        (output / 'SUMMARY.json').write_text(json.dumps({'rows': rows, 'retries': 0, 'model_calls': 0,
            'scope': 'real subprocess stdout pipe, exact extracted reader/wait only; no GUI/game/controller/adoption'}, sort_keys=True) + '\n')
    finally:
        threading.excepthook = oldhook


if __name__ == '__main__':
    run(Path(sys.argv[1]), Path(sys.argv[2]))
