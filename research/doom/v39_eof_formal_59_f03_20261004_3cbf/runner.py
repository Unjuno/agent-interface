"""Prospective four-cell pipe notification protocol; never reuse prior output."""
import hashlib
import json
from pathlib import Path
import queue
import subprocess
import sys
import tarfile
import threading
import time

PACKAGES = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PACKAGES / 'v39_eof_59_f02_20261004_3cbf'))
from candidate import factory as candidate_factory
from probe import factory as baseline_factory
CASES = ('baseline_eof', 'candidate_eof', 'candidate_events_eof', 'candidate_json')


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True) + '\n')


def expected(case, row):
    if case == 'candidate_events_eof' and not (
            row.get('ready') == {'event': 'ready'}
            and row.get('terminal') == {'event': 'terminal'}
            and row.get('reader_alive_after_ready') is True):
        return False
    outcome = 'TimeoutError' if case == 'baseline_eof' else '_SessionReaderFailure'
    cause = None if case == 'baseline_eof' else ('JSONDecodeError' if case == 'candidate_json' else 'EOFError')
    return (len(row['waits']) == 2 and all(wait['outcome'] == outcome and wait['cause'] == cause for wait in row['waits'])
            and row['reader_alive'] is False and row['child_alive'] is True
            and row['cleanup_exit'] == -15 and row['fatal'] is None and row['cleanup_faults'] == []
            and row['events'] == ([{'event': 'ready'}, {'event': 'terminal'}] if case == 'candidate_events_eof' else []))


def run(output):
    output.mkdir(exist_ok=False)
    archive = PACKAGES / 'v39_native_fault_59_e05_20261004_3cbf/source-closure.tar.gz'
    pins = {
        'candidate': PACKAGES / 'v39_eof_59_f02_20261004_3cbf/candidate.py',
        'helper': PACKAGES / 'v39_os_pipe_59_f01_20261004_3cbf/probe.py',
        'archive': archive,
    }
    require = {'candidate': '2b569e6697720bef1f9d0381af6bc4876770132f26e418f697f136c40fc8a1a1',
               'helper': '8359de6a8c714eabc08e88b6d22d51935be23fc3cfde5663fdc85bf44d1d1ae0',
               'archive': 'd1ad6dcb8720b27766702361b4898d13259d2efe0b173e7d0fbc970fe3d988db'}
    try:
        hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in pins.items()}
        if hashes != require:
            raise ValueError('source pins')
        with tarfile.open(archive, 'r:gz') as source:
            code = source.extractfile('research/doom/v39_reader_signal_59_e02_20261004_3cbf/source/v39-candidate.py.txt').read()
    except Exception as error:
        write(output / 'SUMMARY.json', {
            'cases': [], 'retries': 0, 'model_calls': 0,
            'verdict': 'STOP_PREFLIGHT_SOURCE', 'error_type': type(error).__name__,
            'error': repr(error)})
        return 1
    rows = []
    for case in CASES:
        row = {'case': case, 'start_ns': time.perf_counter_ns(), 'pins': hashes,
               'waits': [], 'events': [], 'cleanup_faults': [], 'fatal': None}
        child = thread = None
        try:
            wire = 'not-json\n' if case == 'candidate_json' else ''
            script = ('import os,sys,time;print(\'{"event":"ready"}\',flush=True);sys.stdin.readline();'
                      'print(\'{"event":"terminal"}\',flush=True);os.close(1);time.sleep(3)') if case == 'candidate_events_eof' else (
                      'import os,sys,time;sys.stdout.write(sys.argv[1]);sys.stdout.flush();os.close(1);time.sleep(3)')
            child = subprocess.Popen([sys.executable, '-u', '-c', script, wire], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            row['child_pid'] = child.pid
            factory = baseline_factory if case == 'baseline_eof' else candidate_factory
            reader, wait, events = factory(code)(child, queue.Queue())
            thread = threading.Thread(target=reader, name='f03-reader'); thread.start()
            if case == 'candidate_events_eof':
                row['ready'] = wait(lambda event: event['event'] == 'ready', timeout=1)
                row['reader_alive_after_ready'] = thread.is_alive()
                child.stdin.write('continue\n'); child.stdin.flush()
                row['terminal'] = wait(lambda event: event['event'] == 'terminal', timeout=1)
            for attempt in range(2):
                result = {'start_ns': time.perf_counter_ns()}
                try:
                    wait(lambda event: False, timeout=.35)
                    result.update(outcome='unexpected_return', cause=None)
                except Exception as error:
                    result.update(outcome=type(error).__name__,
                                  cause=type(error.__cause__).__name__ if error.__cause__ else None,
                                  detail=repr(error))
                result['end_ns'] = time.perf_counter_ns(); row['waits'].append(result)
            thread.join(1)
            row.update(reader_alive=thread.is_alive(), child_alive=child.poll() is None, events=events)
        except Exception as error:
            row['fatal'] = repr(error)
        finally:
            if child is not None:
                try:
                    child.terminate()
                    try:
                        child.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        child.kill(); child.wait(timeout=2)
                    row['cleanup_exit'] = child.returncode
                except Exception as error:
                    row['cleanup_faults'].append(repr(error))
                for handle in (child.stdin, child.stdout, child.stderr):
                    try:
                        handle.close()
                    except Exception as error:
                        row['cleanup_faults'].append(repr(error))
            if thread is not None:
                thread.join(1)
                if thread.is_alive():
                    row['cleanup_faults'].append('reader still alive')
            row['end_ns'] = time.perf_counter_ns()
            row['gate'] = expected(case, row) if row['fatal'] is None else False
            write(output / (case + '.json'), row); rows.append(row)
        if row['gate'] is not True:
            break
    summary = {'cases': [row['case'] for row in rows], 'retries': 0, 'model_calls': 0,
               'verdict': 'PASS_SCOPED_PIPE_NOTIFICATION' if len(rows) == 4 and all(row['gate'] for row in rows) else 'STOP_FIRST_UNEXPECTED_CELL'}
    write(output / 'SUMMARY.json', summary)
    return 0 if summary['verdict'] == 'PASS_SCOPED_PIPE_NOTIFICATION' else 1


if __name__ == '__main__':
    sys.exit(run(Path(sys.argv[1])))
