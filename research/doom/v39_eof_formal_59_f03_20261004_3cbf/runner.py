"""Prospective four-cell pipe notification protocol; never reuse prior output."""
import hashlib
import builtins
import json
from pathlib import Path
import queue
import subprocess
import signal
import sys
import tarfile
import threading
import time

PACKAGES = Path(__file__).resolve().parent.parent
CASES = ('baseline_eof', 'candidate_eof', 'candidate_events_eof', 'candidate_json')
PINS = {
    'candidate': '2b569e6697720bef1f9d0381af6bc4876770132f26e418f697f136c40fc8a1a1',
    'helper': '8359de6a8c714eabc08e88b6d22d51935be23fc3cfde5663fdc85bf44d1d1ae0',
}


def load_factories(candidate_bytes, helper_bytes):
    """Compile hash-checked bytes; do not resolve the mutable module cache or pyc."""
    if hashlib.sha256(candidate_bytes).hexdigest() != PINS['candidate']:
        raise ValueError('candidate source pin')
    if hashlib.sha256(helper_bytes).hexdigest() != PINS['helper']:
        raise ValueError('helper source pin')
    helper = type(sys)('_f03_pinned_probe')
    helper.__file__ = '<frozen-F01-probe-bytes>'
    exec(compile(helper_bytes, helper.__file__, 'exec'), helper.__dict__)
    candidate = type(sys)('_f03_pinned_candidate')
    candidate.__file__ = '<frozen-F02-candidate-bytes>'
    namespace = dict(vars(builtins))
    import_function = builtins.__import__

    def pinned_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'probe' and level == 0:
            return helper
        return import_function(name, globals, locals, fromlist, level)

    namespace['__import__'] = pinned_import
    candidate.__dict__['__builtins__'] = namespace
    exec(compile(candidate_bytes, candidate.__file__, 'exec'), candidate.__dict__)
    return helper.factory, candidate.factory


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True) + '\n')


def sigint_blocked_reader(reader):
    # This thread is dedicated to one reader invocation. Leave SIGINT blocked
    # until the OS thread exits, avoiding an unmasked return/finalization window.
    signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
    reader()


def expected(case, row):
    if row.get('cleanup_child_alive') is not False or row.get('cleanup_reader_alive') is not False:
        return False
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


def finalize_cell(output, rows, case, row, child, thread, journal):
    """Defer SIGINT only across owned cleanup and durable row/STOP writes."""
    old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
    try:
        if child is not None:
            row.setdefault('child_alive', child.poll() is None)
        if thread is not None:
            row.setdefault('reader_alive', thread.is_alive())
        if child is not None:
            try:
                child.terminate()
            except (Exception, KeyboardInterrupt) as error:
                row['cleanup_faults'].append(repr(error))
            try:
                child.wait(timeout=2)
            except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
                if isinstance(error, KeyboardInterrupt):
                    row['cleanup_faults'].append(repr(error))
                try:
                    child.kill(); child.wait(timeout=2)
                except (Exception, KeyboardInterrupt) as error:
                    row['cleanup_faults'].append(repr(error))
            except Exception as error:
                row['cleanup_faults'].append(repr(error))
            row['cleanup_exit'] = child.returncode
            for handle in (child.stdin, child.stdout, child.stderr):
                try:
                    handle.close()
                except (Exception, KeyboardInterrupt) as error:
                    row['cleanup_faults'].append(repr(error))
        if thread is not None:
            if thread.ident is not None:
                try:
                    thread.join(1)
                except (Exception, KeyboardInterrupt) as error:
                    row['cleanup_faults'].append(repr(error))
            if thread.is_alive():
                row['cleanup_faults'].append('reader still alive')
        row['cleanup_child_alive'] = child.poll() is None if child is not None else None
        row['cleanup_reader_alive'] = thread.is_alive() if thread is not None else None
        row['end_ns'] = time.perf_counter_ns()
        row['gate'] = expected(case, row) if row['fatal'] is None else False
        if journal is not None:
            journal.write('F03_CELL_RECORD ' + json.dumps(row, sort_keys=True) + '\n')
            journal.flush()
        write(output / (case + '.json'), row)
        rows.append(row)
        # A checkpoint protects the first STOP if SIGINT is pending when the
        # mask is restored. A final scientific PASS is written only afterward.
        checkpoint = {
            'cases': [saved['case'] for saved in rows], 'retries': 0, 'model_calls': 0,
            'verdict': 'STOP_CELL_SEQUENCE_INCOMPLETE',
            'stop_reason': row.get('fatal_type') or ('cleanup_fault' if row['cleanup_faults'] else 'next_cell_or_final_audit_pending')}
        write(output / 'SUMMARY.json', checkpoint)
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)


def run(output, journal=None):
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
        candidate_bytes = pins['candidate'].read_bytes()
        helper_bytes = pins['helper'].read_bytes()
        baseline_factory, candidate_factory = load_factories(candidate_bytes, helper_bytes)
        with tarfile.open(archive, 'r:gz') as source:
            code = source.extractfile('research/doom/v39_reader_signal_59_e02_20261004_3cbf/source/v39-candidate.py.txt').read()
    except (Exception, KeyboardInterrupt) as error:
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
            # Keep a process-directed SIGINT pending until Popen returns and its
            # live handle is owned by `child`; otherwise a tiny handoff window
            # can orphan a process that the cleanup path cannot see.
            previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
            try:
                child = subprocess.Popen([sys.executable, '-u', '-c', script, wire], stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
            row['child_pid'] = child.pid
            factory = baseline_factory if case == 'baseline_eof' else candidate_factory
            reader, wait, events = factory(code)(child, queue.Queue())
            thread = threading.Thread(target=sigint_blocked_reader, args=(reader,), name='f03-reader'); thread.start()
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
        except (Exception, KeyboardInterrupt) as error:
            row['fatal'] = repr(error)
            row['fatal_type'] = type(error).__name__
        finally:
            finalize_cell(output, rows, case, row, child, thread, journal)
        if row['gate'] is not True:
            break
    summary = {'cases': [row['case'] for row in rows], 'retries': 0, 'model_calls': 0,
               'verdict': 'FOUR_CELL_GATES_TRUE_AWAITING_EXIT' if len(rows) == 4 and all(row['gate'] for row in rows) else 'STOP_FIRST_UNEXPECTED_CELL'}
    if rows and rows[-1].get('fatal_type'):
        summary['stop_reason'] = rows[-1]['fatal_type']
    elif rows and rows[-1]['cleanup_faults']:
        summary['stop_reason'] = 'cleanup_fault'
    old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
    try:
        write(output / 'SUMMARY.json', summary)
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
    return 0 if summary['verdict'] == 'FOUR_CELL_GATES_TRUE_AWAITING_EXIT' else 1


if __name__ == '__main__':
    sys.exit(run(Path(sys.argv[1]), journal=sys.stdout))
