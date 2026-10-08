"""Four native stable-payload transfer cells; no shared X socket or host clipboard."""
import argparse
import ctypes as c
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import platform
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
    return {'clipboard_owner': int(X.XGetSelectionOwner(display, atom)),
            'focus': int(focus.value), 'keymap_hex': keys.raw.hex(),
            'monotonic_ns': time.monotonic_ns()}


def reply(proc):
    if not select.select([proc.stdout], [], [], 5)[0]:
        raise TimeoutError('application reply absent')
    return json.loads(proc.stdout.readline())


def command(proc, op, **data):
    proc.stdin.write(json.dumps({'op': op, **data}) + '\n'); proc.stdin.flush()
    response = reply(proc)
    if response.get('op') != op:
        raise RuntimeError('command echo mismatch')
    return response


def cell(case, folder, number):
    folder.mkdir()
    (folder / 'case.json').write_text(json.dumps(case) + '\n')
    processes, streams, commands = {}, [], []
    display = None
    os.environ['DISPLAY'] = ':' + str(80 + number)
    row = {'id': case['id'], 'display': os.environ['DISPLAY'], 'commands': commands, 'pids': {}, 'exits': {}}
    def run(argv):
        result = subprocess.run(argv, capture_output=True, timeout=5)
        commands.append({'argv': argv, 'exit_code': result.returncode,
                         'stdout_hex': result.stdout.hex(), 'stderr': result.stderr.decode()})
        if result.returncode:
            raise RuntimeError('native command failed: ' + argv[0])
        return result.stdout
    try:
        stream = (folder / 'xvfb.stderr').open('w'); streams.append(stream)
        processes['xvfb'] = subprocess.Popen(['Xvfb', os.environ['DISPLAY'], '-screen', '0', '640x480x24', '-nolisten', 'tcp'], stderr=stream, stdout=stream)
        deadline = time.monotonic() + 5
        while display is None and time.monotonic() < deadline:
            display = X.XOpenDisplay(None) or None
            if display is None:
                time.sleep(.02)
        if display is None:
            raise RuntimeError('private X server unavailable')
        for role in ['owner', 'consumer']:
            stream = (folder / (role + '.stderr')).open('w'); streams.append(stream)
            proc = subprocess.Popen(['python3', '-B', str(HERE / 'app.py'), role, str(folder / 'case.json'), str(folder)],
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stream, text=True)
            processes[role] = proc
            row[role + '_ready'] = reply(proc)
        row['pids'] = {role: proc.pid for role, proc in processes.items()}
        run(['xdotool', 'windowfocus', '--sync', str(row['consumer_ready']['window'])])
        row['before'] = snap(display)
        if row['before']['focus'] != row['consumer_ready']['window'] or row['before']['keymap_hex'] != '00' * 32 or not row['before']['clipboard_owner']:
            raise RuntimeError('focus, owner or neutral-input setup absent')
        command(processes['owner'], 'phase', phase='snapshot')
        transferred = {}
        for mime in ['text/plain', 'text/html']:
            data = run(['xclip', '-selection', 'clipboard', '-target', mime, '-out'])
            name = 'transport-' + mime.split('/')[1] + '.txt'
            (folder / name).write_bytes(data)
            transferred[mime] = hashlib.sha256(data).hexdigest()
        row['transport_sha256'] = transferred
        command(processes['owner'], 'phase', phase='paste')
        command(processes['consumer'], 'phase', phase='paste')
        run(['xdotool', 'key', '--clearmodifiers', 'ctrl+v'])
        deadline = time.monotonic() + 5
        releases = []
        while time.monotonic() < deadline:
            releases = command(processes['consumer'], 'probe')['key_releases']
            if 86 in releases and 16777249 in releases:
                break
            time.sleep(.02)
        row['key_releases'] = releases
        row['dump'] = command(processes['consumer'], 'dump')
        row['after'] = snap(display)
        row['saved_sha256'] = {name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
                               for name in ['text.txt', 'document.html', 'window.png']}
        row['status'] = 'RECORDED'
    except Exception as error:
        row['status'] = 'STOP_INFRA_OR_RECORDER'
        row['error'] = type(error).__name__ + ': ' + str(error)
    finally:
        for role in ['consumer', 'owner']:
            proc = processes.get(role)
            if proc is not None:
                try:
                    if proc.poll() is None:
                        command(proc, 'stop')
                    row['exits'][role] = proc.wait(timeout=5)
                except Exception:
                    proc.kill(); row['exits'][role] = proc.wait(timeout=5)
        if display is not None:
            row['final'] = snap(display)
            X.XCloseDisplay(display)
        if 'xvfb' in processes:
            proc = processes['xvfb']
            if proc.poll() is None:
                proc.terminate()
            try:
                row['exits']['xvfb'] = proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill(); row['exits']['xvfb'] = proc.wait(timeout=5)
        for stream in streams:
            stream.close()
    row['artifact_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted(folder.iterdir()) if p.is_file()}
    (folder / 'row.json').write_text(json.dumps(row, indent=2) + '\n')
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--construction', action='store_true')
    args = parser.parse_args()
    args.output.mkdir()
    environment = {'python': platform.python_version(), 'machine': platform.machine(), 'kernel': platform.release(),
                   'cgroup': {name: (Path('/sys/fs/cgroup') / name).read_text().strip()
                              for name in ('cpu.max', 'memory.max', 'pids.max')}}
    rows = []
    cases = json.loads(args.cases.read_text())['cases']
    if len(cases) != (1 if args.construction else 4):
        raise RuntimeError('fixed case denominator required')
    for number, case in enumerate(cases):
        rows.append(cell(case, args.output / case['id'], number))
        if rows[-1]['status'] != 'RECORDED':
            break
    result = {'schema': 'clipboard36-x11-transfer-v1', 'rows': rows,
              'status': 'RECORDED' if len(rows) == len(cases) and all(x['status'] == 'RECORDED' for x in rows) else 'STOP_FIRST_CELL',
              'construction': args.construction, 'environment': environment,
              'qt_platform_required': 'xcb', 'host_clipboard_used': False}
    (args.output / 'raw.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'rows': len(rows)}))
    raise SystemExit(0 if result['status'] == 'RECORDED' else 1)


if __name__ == '__main__':
    main()
