"""Native clipboard availability experiment; all displays and signals are private."""
import argparse
import ctypes as c
import hashlib
import json
import os
from pathlib import Path
import platform
import select
import signal
import subprocess
import time

HERE = Path(__file__).resolve().parent
X = c.CDLL('libX11.so.6')
X.XOpenDisplay.argtypes = [c.c_char_p]; X.XOpenDisplay.restype = c.c_void_p
X.XCloseDisplay.argtypes = [c.c_void_p]
X.XInternAtom.argtypes = [c.c_void_p, c.c_char_p, c.c_int]; X.XInternAtom.restype = c.c_ulong
X.XGetSelectionOwner.argtypes = [c.c_void_p, c.c_ulong]; X.XGetSelectionOwner.restype = c.c_ulong
X.XGetInputFocus.argtypes = [c.c_void_p, c.POINTER(c.c_ulong), c.POINTER(c.c_int)]
X.XQueryKeymap.argtypes = [c.c_void_p, c.c_char_p]


def snap(display):
    focus, revert = c.c_ulong(), c.c_int()
    X.XGetInputFocus(display, c.byref(focus), c.byref(revert))
    keys = c.create_string_buffer(32)
    X.XQueryKeymap(display, keys)
    atom = X.XInternAtom(display, b'CLIPBOARD', 0)
    return {'owner': int(X.XGetSelectionOwner(display, atom)), 'focus': int(focus.value),
            'keymap_hex': keys.raw.hex(), 'at_ns': time.monotonic_ns()}


class Lines:
    """A finite byte-framed reader, including partial-line output."""
    def __init__(self, proc):
        self.proc, self.pending = proc, b''

    def read(self, timeout):
        deadline = time.monotonic() + timeout
        while b'\n' not in self.pending:
            left = deadline - time.monotonic()
            if left <= 0 or not select.select([self.proc.stdout], [], [], max(0, left))[0]:
                raise TimeoutError('reply deadline')
            data = os.read(self.proc.stdout.fileno(), 4096)
            if not data:
                raise EOFError('application stdout closed')
            self.pending += data
            if len(self.pending) > 65536:
                raise RuntimeError('reply cap')
        line, self.pending = self.pending.split(b'\n', 1)
        return json.loads(line)

    def send(self, op, **data):
        self.proc.stdin.write((json.dumps({'op': op, **data}) + '\n').encode())
        self.proc.stdin.flush()

    def command(self, op, **data):
        self.send(op, **data)
        result = self.read(3)
        if result.get('op') != op:
            raise RuntimeError('reply association')
        return result


def journal_prefix(folder):
    path = folder / 'consumer.events.jsonl'
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def cell(case, folder, number):
    folder.mkdir()
    (folder / 'case.json').write_text(json.dumps(case) + '\n')
    os.environ['DISPLAY'] = ':' + str(100 + number)
    procs, streams, channels, commands = {}, [], {}, []
    display, stopped = None, False
    row = {'id': case['id'], 'case': case, 'display': os.environ['DISPLAY'],
           'commands': commands, 'signals': [], 'exits': {}}
    def native(argv, timeout=3):
        start = time.monotonic_ns()
        proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        timed_out = False
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True; proc.kill(); out, err = proc.communicate(timeout=3)
        result = {'argv': argv, 'pid': proc.pid, 'timeout_s': timeout,
                  'timeout': timed_out, 'exit': proc.returncode, 'stdout_hex': out.hex(),
                  'stderr_hex': err.hex(), 'start_ns': start, 'end_ns': time.monotonic_ns()}
        commands.append(result)
        return result
    def owner_signal(sig):
        os.kill(procs['owner'].pid, sig)
        item = {'signal': int(sig), 'pid': procs['owner'].pid, 'at_ns': time.monotonic_ns()}
        row['signals'].append(item)
        return item
    try:
        stream = (folder / 'xvfb.stderr').open('w'); streams.append(stream)
        procs['xvfb'] = subprocess.Popen(['Xvfb', os.environ['DISPLAY'], '-screen', '0', '640x480x24', '-nolisten', 'tcp'], stderr=stream, stdout=stream)
        end = time.monotonic() + 3
        while display is None and time.monotonic() < end:
            display = X.XOpenDisplay(None) or None
            if display is None: time.sleep(.02)
        if display is None: raise RuntimeError('X server unavailable')
        for role in ['owner', 'consumer']:
            stream = (folder / (role + '.stderr')).open('w'); streams.append(stream)
            proc = subprocess.Popen(['python3', '-B', str(HERE / 'app.py'), role, str(folder / 'case.json'), str(folder)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stream)
            procs[role] = proc; channels[role] = Lines(proc)
            row[role + '_ready'] = channels[role].read(3)
        row['pids'] = {role: proc.pid for role, proc in procs.items()}
        focused = native(['xdotool', 'windowfocus', '--sync', str(row['consumer_ready']['window'])])
        if focused['exit'] != 0: raise RuntimeError('focus command failed')
        row['baseline_dump'] = channels['consumer'].command('dump')
        row['baseline'] = snap(display)
        if row['baseline_dump']['text'] != '' or row['baseline']['owner'] <= 0 or row['baseline']['focus'] != row['consumer_ready']['window'] or row['baseline']['keymap_hex'] != '00' * 32:
            raise RuntimeError('baseline absent')
        channels['consumer'].command('phase', phase='paste')
        channels['owner'].command('phase', phase='paste')
        if case['owner_state'] == 'absent':
            channels['owner'].command('stop'); row['exits']['owner'] = procs['owner'].wait(timeout=3)
        elif case['owner_state'] == 'stopped':
            owner_signal(signal.SIGSTOP); stopped = True
            deadline = time.monotonic() + 1
            while time.monotonic() < deadline:
                status = Path('/proc/' + str(procs['owner'].pid) + '/status').read_text()
                state = next(line for line in status.splitlines() if line.startswith('State:'))
                if 'T' in state: break
                time.sleep(.005)
            row['stopped_state'] = state
            if 'T' not in state: raise RuntimeError('owner stop not observed')
        row['admission'] = snap(display)
        admit = True
        if case['policy'] == 'read_before_input':
            row['preflight'] = native(['xclip', '-selection', 'clipboard', '-target', 'text/plain', '-out'], .5)
            admit = not row['preflight']['timeout'] and row['preflight']['exit'] == 0 and bytes.fromhex(row['preflight']['stdout_hex']) == case['plain'].encode() and row['admission']['owner'] > 0
        row['admitted'] = admit
        row['before_input'] = snap(display)
        if admit:
            row['paste'] = native(['xdotool', 'key', '--clearmodifiers', 'ctrl+v'])
            if row['paste']['exit'] != 0: raise RuntimeError('native paste command failed')
            channels['consumer'].send('dump')
            row['reply_start_ns'] = time.monotonic_ns()
            try:
                row['deadline_dump'] = channels['consumer'].read(.5)
                row['deadline_outcome'] = 'REPLY'
            except TimeoutError:
                row['deadline_outcome'] = 'UNKNOWN_PENDING_EFFECT'
            row['deadline_ns'] = time.monotonic_ns()
        else:
            row['deadline_outcome'] = 'REFUSED_BEFORE_INPUT'
            row['deadline_ns'] = time.monotonic_ns()
        row['deadline_events'] = journal_prefix(folder)
        row['deadline_server'] = snap(display)
        if stopped:
            owner_signal(signal.SIGCONT); stopped = False
        if admit and row['deadline_outcome'] == 'UNKNOWN_PENDING_EFFECT':
            row['late_dump'] = channels['consumer'].read(3)
            row['late_reply_ns'] = time.monotonic_ns()
        row['final_dump'] = channels['consumer'].command('dump')
        row['probe'] = channels['consumer'].command('probe')
        row['effect_server'] = snap(display)
        row['status'] = 'RECORDED'
    except Exception as error:
        row['status'] = 'STOP_INFRA_OR_RECORDER'; row['error'] = type(error).__name__ + ': ' + str(error)
    finally:
        if stopped:
            owner_signal(signal.SIGCONT)
        for role in ['consumer', 'owner']:
            proc = procs.get(role)
            if proc:
                try:
                    if proc.poll() is None: channels[role].command('stop')
                    row['exits'][role] = proc.wait(timeout=3)
                except Exception:
                    proc.kill(); row['exits'][role] = proc.wait(timeout=3)
        if display:
            row['cleanup_server'] = snap(display); X.XCloseDisplay(display)
        if 'xvfb' in procs:
            proc = procs['xvfb']; proc.terminate()
            try: row['exits']['xvfb'] = proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill(); row['exits']['xvfb'] = proc.wait(timeout=3)
        for stream in streams: stream.close()
    row['artifact_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.iterdir()) if p.is_file()}
    (folder / 'row.json').write_text(json.dumps(row, indent=2) + '\n')
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--construction', action='store_true')
    args = parser.parse_args(); args.output.mkdir()
    cases = json.loads(args.cases.read_text())['cases']
    if len(cases) != (1 if args.construction else 6): raise RuntimeError('fixed denominator')
    rows = []
    for number, case in enumerate(cases):
        rows.append(cell(case, args.output / case['id'], number))
        if rows[-1]['status'] != 'RECORDED': break
    raw = {'schema': 'clipboard36-availability-v1', 'construction': args.construction,
           'status': 'RECORDED' if len(rows) == len(cases) and all(r['status'] == 'RECORDED' for r in rows) else 'STOP_FIRST_CELL',
           'rows': rows, 'environment': {'python': platform.python_version(), 'machine': platform.machine(),
           'kernel': platform.release(), 'cgroup': {n: (Path('/sys/fs/cgroup') / n).read_text().strip() for n in ['cpu.max', 'memory.max', 'pids.max']}}}
    (args.output / 'raw.json').write_text(json.dumps(raw, indent=2) + '\n')
    print(json.dumps({'status': raw['status'], 'rows': len(rows)}))
    raise SystemExit(0 if raw['status'] == 'RECORDED' else 1)


if __name__ == '__main__': main()
