"""One-shot native X11 session fault injection. No model or production adoption."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import traceback
from types import SimpleNamespace
from gate import release_gate, fault_gate
from cleanup import close_resources

CASES = ('original_fault', 'candidate_fault', 'candidate_healthy')
EXPECTED = {'original_fault': ('TimeoutError', None, False),
            'candidate_fault': ('_SessionReaderFailure', 'JSONDecodeError', False),
            'candidate_healthy': ('TimeoutError', None, True)}
E02 = 'research/doom/v39_reader_signal_59_e02_20261004_3cbf/source/'


def factory(source):
    tree = ast.parse(source.decode())
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    nodes = [n for n in main.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))
             and n.name in ('reader', 'wait', '_SessionReaderFailure')]
    names = [n.name for n in nodes]
    if names not in (['reader', 'wait'], ['_SessionReaderFailure', 'reader', 'wait']):
        raise ValueError('reader/wait extraction cardinality')
    node = ast.parse('def create(process, incoming):\n latest=None\n all_events=[]\n').body[0]
    node.body.extend(nodes)
    node.body.extend(ast.parse('return reader, wait, all_events').body)
    scope = dict(json=json, queue=queue, time=time)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                 'exact-v39-reader-wait-e05', 'exec'), scope)
    return scope['create']


class InjectionStream:
    def __init__(self, incoming, inject):
        self.incoming = incoming; self.inject = inject
        self.injected_ns = None
        self.observe = None; self.injection_state = None

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            if self.inject.is_set() and self.injected_ns is None:
                self.injection_state = self.observe()
                self.injected_ns = time.perf_counter_ns()
                return 'not-json\n'
            try:
                line = self.incoming.get(timeout=.01)
            except queue.Empty:
                continue
            if line is None:
                raise StopIteration
            return line


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True) + '\n')


def verify_pins(manifest, base):
    count = 0
    for line in manifest.read_text().splitlines():
        digest, relative = line.split('  ', 1)
        path = (base / relative).resolve()
        if not path.is_relative_to(base.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('frozen input hash mismatch: ' + relative)
        count += 1
    return count


def wait_native(rows, predicate, budget=3):
    deadline = time.monotonic() + budget
    while time.monotonic() < deadline:
        for row in list(rows):
            if predicate(row):
                return row
        time.sleep(.005)
    raise TimeoutError('native side-channel evidence deadline')


def state(display):
    bitmap = display.query_keymap()
    mask = display.screen().root.query_pointer().mask
    return {'keys': [k for k in range(256) if bitmap[k // 8] & (1 << (k % 8))],
            'buttons': [b for b in range(1, 6) if mask & (1 << (7 + b))]}


def native_display(child_pid):
    """Identify only the Xvfb directly spawned by this owned native session."""
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            status = (directory / 'status').read_text()
            ppid = next(line for line in status.splitlines() if line.startswith('PPid:'))
            command = (directory / 'cmdline').read_bytes().split(b'\0')
        except (OSError, StopIteration):
            continue
        if int(ppid.split()[1]) == child_pid and command[0] == b'Xvfb':
            name = command[1].decode('ascii')
            if not name.startswith(':') or not name[1:].isdigit():
                raise ValueError('unexpected private Xvfb command')
            return name
    raise ValueError('owned Xvfb not found')


def run_cell(root, source, output, case):
    from Xlib import display as xd, XK
    cell = output / case; cell.mkdir()
    process = observer = injection_observer = reader_thread = drain_thread = None
    rows = []; wire = queue.Queue(); inject = threading.Event()
    stream = InjectionStream(wire, inject)
    result = {'case': case, 'id': 'e05-' + case, 'cleanup_faults': [], 'fatal': None,
              'start_ns': time.perf_counter_ns(), 'scope': 'controlled text-iterator injection; native stdout independently drained'}
    hook = threading.excepthook
    unhandled = []
    threads = []
    try:
        stderr = (cell / 'session.stderr.log').open('w')
        threads.append(stderr)
        command = [sys.executable, '-B', str(root / 'session_entry.py'),
                   '--source', str(source), '--receipt', str(cell / 'imports.json'),
                   '--out', str(cell / 'session'), '--seed', '20261004',
                   '--timeout-seconds', '20', '--skill', '1']
        result['command'] = command
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=stderr, text=True, encoding='utf-8', errors='strict', bufsize=1)
        result['pid'] = process.pid
        result['proc_status'] = Path('/proc', str(process.pid), 'status').read_text()
        def drain():
            with (cell / 'native-stdout.jsonl').open('w') as raw:
                for line in process.stdout:
                    raw.write(line); raw.flush()
                    rows.append(json.loads(line))
                    wire.put(line)
                wire.put(None)
        drain_thread = threading.Thread(target=drain, daemon=True, name='native-evidence-drain')
        drain_thread.start()
        def note(args):
            unhandled.append({'thread': args.thread.name, 'type': args.exc_type.__name__,
                              'traceback': ''.join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))})
        threading.excepthook = note
        snapshot = source / E02 / ('v39-original.py.txt' if case == 'original_fault' else 'v39-candidate.py.txt')
        result['reader_sha256'] = hashlib.sha256(snapshot.read_bytes()).hexdigest()
        reader, wait, received = factory(snapshot.read_bytes())(
            SimpleNamespace(stdout=stream, poll=process.poll), queue.Queue())
        reader_thread = threading.Thread(target=reader, daemon=True, name='selected-v39-reader')
        reader_thread.start()
        ready = wait(lambda r: r['event'] == 'ready', timeout=10)
        initial = wait(lambda r: r['event'] == 'observation', timeout=2)
        result['ready'] = ready; result['initial'] = initial
        environment = json.loads((cell / 'session/environment.json').read_text())
        result['environment'] = environment
        display_name = native_display(process.pid)
        result['display'] = display_name
        observer = xd.Display(display_name)
        injection_observer = xd.Display(display_name)
        stream.observe = lambda: state(injection_observer)
        result['right_code'] = observer.keysym_to_keycode(XK.string_to_keysym('Right'))
        result['before'] = state(observer)
        if result['before'] != {'keys': [], 'buttons': []}:
            raise ValueError('nonneutral isolated display before action')
        def send(command):
            started = time.perf_counter_ns()
            process.stdin.write(json.dumps(command) + '\n'); process.stdin.flush()
            return {'command': command, 'start_ns': started, 'return_ns': time.perf_counter_ns()}
        result['submit'] = send({'op': 'submit', 'id': result['id'],
            'expected_sequence': initial['sequence'], 'valid_until_ns': time.perf_counter_ns() + 5_000_000_000,
            'steps': [{'op': 'hold', 'keys': ['Right'], 'duration_ms': 3000}]})
        result['accepted'] = wait(lambda r: r['event'] in ('accepted', 'rejected'), timeout=1)
        if result['accepted']['event'] != 'accepted':
            raise ValueError('action rejected')
        result['expected_token'] = result['accepted']['intent_token']
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            observed = state(observer)
            if observed == {'keys': [result['right_code']], 'buttons': []}:
                result['held'] = observed; result['held_ns'] = time.perf_counter_ns(); break
            time.sleep(.005)
        if 'held' not in result:
            raise ValueError('actual held key not exposed')
        if case != 'candidate_healthy':
            result['fault_requested_ns'] = time.perf_counter_ns(); inject.set()
        result['wait_start_ns'] = time.perf_counter_ns()
        try:
            wait(lambda row: False, timeout=.35)
            result['wait_outcome'] = 'unexpected_return'
        except Exception as exc:
            result['wait_outcome'] = type(exc).__name__
            result['cause'] = None if exc.__cause__ is None else type(exc.__cause__).__name__
        result['wait_end_ns'] = time.perf_counter_ns()
        result['injected_ns'] = stream.injected_ns
        result['injection_state'] = stream.injection_state
        result['reader_alive_at_cancel'] = reader_thread.is_alive()
        result['after_notification'] = state(observer)
        result['notification_sample_ns'] = time.perf_counter_ns()
        result['before_cancel'] = state(observer)
        result['before_cancel_ns'] = time.perf_counter_ns()
        if result['after_notification'] != result['held'] or result['before_cancel'] != result['held']:
            raise ValueError('hold not present after notification/before cancel')
        result['cancel_send'] = send({'op': 'cancel', 'id': result['id']})
        result['cancel'] = wait_native(rows, lambda r: r['event'] == 'cancel_requested' and r.get('id') == result['id'])
        result['released'] = wait_native(rows, lambda r: r['event'] in ('input_released', 'input_release_unverified') and r.get('id') == result['id'])
        result['terminal'] = wait_native(rows, lambda r: r['event'] == 'terminal' and r.get('id') == result['id'])
        result['after'] = state(observer); result['after_ns'] = time.perf_counter_ns()
        # Retire research observers while the owned server still exists.
        close_resources([observer, injection_observer], result)
        observer = injection_observer = None
        result['finish_send'] = send({'op': 'finish'})
        process.wait(timeout=8)
        result['selected_receiver_rows'] = len(received)
    except Exception:
        result['fatal'] = traceback.format_exc()
    finally:
        if process is not None:
            if process.poll() is None:
                for command in ({'op': 'cancel', 'id': result['id']}, {'op': 'finish'}):
                    try:
                        process.stdin.write(json.dumps(command) + '\n'); process.stdin.flush()
                    except Exception as exc:
                        result['cleanup_faults'].append(repr(exc))
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    result['cleanup_faults'].append('owned session did not exit; terminate fallback')
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill(); process.wait(timeout=2)
            result['child_exit'] = process.poll()
            for handle in (process.stdin, process.stdout):
                try:
                    handle.close()
                except Exception as exc:
                    result['cleanup_faults'].append(repr(exc))
        wire.put(None)
        for thread in (reader_thread, drain_thread):
            if thread is not None:
                thread.join(timeout=1)
                if thread.is_alive():
                    result['cleanup_faults'].append('thread not retired: ' + thread.name)
        close_resources([handle for handle in (observer, injection_observer)
                         if handle is not None], result)
        for handle in threads:
            handle.close()
        threading.excepthook = hook
        result['unhandled'] = unhandled
        result['end_ns'] = time.perf_counter_ns()
        result['release_gate'] = release_gate(result) and result['fatal'] is None
        result['outcome_gate'] = fault_gate(result)
        write(cell / 'RESULT.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True); args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parent
    source_count = verify_pins(root / 'SOURCE_PINS.sha256', args.source)
    execution_count = verify_pins(root / 'EXECUTION_PINS.sha256', root)
    limits = {n: Path('/sys/fs/cgroup', n).read_text().strip()
              for n in ('cpu.max', 'memory.max', 'memory.swap.max', 'pids.max')}
    if os.getuid() != 501 or limits != {'cpu.max': '100000 100000', 'memory.max': '1073741824', 'memory.swap.max': '0', 'pids.max': '128'}:
        raise ValueError('runtime allocation mismatch')
    write(args.out / 'RUNTIME.json', {'limits': limits, 'pid': os.getpid(), 'uid': os.getuid(), 'python': sys.version,
                                    'source_pins': source_count, 'execution_pins': execution_count,
                                    'freeze': json.loads((root / 'FREEZE.json').read_text())})
    results = []
    for case in CASES:
        row = run_cell(Path(__file__).resolve().parent, args.source, args.out, case)
        results.append(row)
        if not row['release_gate'] or not row['outcome_gate']:
            break
    passed = len(results) == 3 and all(r['release_gate'] and r['outcome_gate'] for r in results)
    verify_pins(root / 'SOURCE_PINS.sha256', args.source)
    verify_pins(root / 'EXECUTION_PINS.sha256', root)
    write(args.out / 'SUMMARY.json', {'verdict': 'PASS_SCOPED_NATIVE_FAULT_CANCEL_RELEASE' if passed else 'STOP_NATIVE_GATE',
          'cells': len(results), 'cases': [r['case'] for r in results], 'formal_runs': 1, 'retries': 0,
          'model_calls': 0, 'gameplay_success_claim': False})
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
