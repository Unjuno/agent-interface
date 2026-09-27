"""Issue 3953: private-display capture-to-consumption experiment, no input."""
from __future__ import annotations
import argparse
import base64
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time
import traceback
import zlib

ROOT = Path(__file__).resolve().parent
AGE_NS = 100_000_000
HOLD_NS = 150_000_000
KINDS = ('prompt', 'delayed_same', 'delayed_changed', 'missing', 'boolean',
         'reversed', 'future', 'stale_identity')


def clock_namespace() -> str:
    try:
        return os.readlink('/proc/self/ns/time')
    except FileNotFoundError:
        return 'UNAVAILABLE_PROC_ENTRY'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode(data: bytes) -> str:
    return base64.b64encode(zlib.compress(data, 9)).decode('ascii')


def pixels(packet: dict) -> bytes:
    raw = zlib.decompress(base64.b64decode(packet['pixels_z64'], validate=True))
    if len(raw) != 4096 or sha(raw) != packet['pixels_sha256']:
        raise ValueError('pixel integrity')
    return raw


def decide(packet: dict, request_id: str, session: str, now: int, source_age: bool) -> dict:
    """Only age/identity admission, NOT authority or semantic currentness."""
    try:
        if packet['request_id'] != request_id or packet['session'] != session:
            return {'admit': False, 'reason': 'IDENTITY'}
        pixels(packet)
        if not source_age:
            return {'admit': True, 'reason': 'ARRIVAL_RESTAMPED'}
        bracket = packet.get('capture')
        if not isinstance(bracket, list) or len(bracket) != 2:
            return {'admit': False, 'reason': 'CAPTURE_TYPE'}
        start, end = bracket
        if type(start) is not int or type(end) is not int:
            return {'admit': False, 'reason': 'CAPTURE_TYPE'}
        if not 0 < start <= end <= now:
            return {'admit': False, 'reason': 'CAPTURE_ORDER'}
        if now - start > AGE_NS:
            return {'admit': False, 'reason': 'STALE'}
        return {'admit': True, 'reason': 'CAPTURE_AGE_VALID'}
    except (KeyError, ValueError, TypeError, zlib.error):
        return {'admit': False, 'reason': 'PACKET_INVALID'}


class Native:
    def __init__(self, display: str):
        self.lib = C.CDLL(str(ROOT / 'native.so'))
        self.lib.q_open.argtypes = [C.c_char_p]
        self.lib.q_open.restype = C.c_void_p
        self.lib.q_close.argtypes = [C.c_void_p]
        self.lib.q_paint.argtypes = [C.c_void_p, C.c_int]
        self.lib.q_read.argtypes = [C.c_void_p, C.POINTER(C.c_ubyte), C.c_size_t,
                                   C.POINTER(C.c_uint64)]
        if not self.lib.q_init():
            raise RuntimeError('XInitThreads failed')
        self.handle = self.lib.q_open(display.encode())
        if not self.handle:
            raise RuntimeError('native display unavailable')

    def paint(self, count: int) -> None:
        if self.lib.q_paint(self.handle, count) != 0:
            raise RuntimeError('paint failed')

    def read(self) -> dict:
        data = (C.c_ubyte * 4096)()
        times = (C.c_uint64 * 6)()
        before = time.monotonic_ns()
        rc = self.lib.q_read(self.handle, data, len(data), times)
        after = time.monotonic_ns()
        if rc != 0:
            raise RuntimeError(f'native capture error {rc}')
        b = bytes(data)
        return {'python_before': before, 'native': list(times), 'python_after': after,
                'pixels_z64': encode(b), 'pixels_sha256': sha(b), 'bytes': len(b)}

    def close(self) -> None:
        if self.handle:
            self.lib.q_close(self.handle)
            self.handle = None


def emit(data: dict) -> None:
    print(json.dumps(data, sort_keys=True, separators=(',', ':')), flush=True)


def worker(display: str) -> None:
    n = Native(display)
    try:
        emit({'event': 'ready', 'pid': os.getpid(),
              'time_namespace': clock_namespace()})
        req = json.loads(sys.stdin.readline())
        captured = n.read()
        emit({'event': 'captured', 'capture': captured})
        release = json.loads(sys.stdin.readline())
        if release != {'op': 'deliver'}:
            raise ValueError('delivery protocol')
        packet = {'request_id': req['request_id'], 'session': req['session'],
                  'capture': captured['native'][1:3],
                  'pixels_z64': captured['pixels_z64'],
                  'pixels_sha256': captured['pixels_sha256']}
        kind = req['kind']
        if kind == 'missing':
            del packet['capture']
        elif kind == 'boolean':
            packet['capture'] = [True, True]
        elif kind == 'reversed':
            packet['capture'] = [captured['native'][2] + 1, captured['native'][1]]
        elif kind == 'future':
            packet['capture'] = [captured['native'][2] + 60_000_000_000] * 2
        elif kind == 'stale_identity':
            packet['request_id'] = 'predecessor-request'
        emit({'event': 'delivered', 'packet': packet, 'publish_ns': time.monotonic_ns()})
    finally:
        n.close()


class Peer:
    def __init__(self, display: str, stderr_path: Path):
        self.err = stderr_path.open('xb')
        self.proc = subprocess.Popen([sys.executable, '-B', str(ROOT / 'study.py'),
                                      '--worker', display], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=self.err, bufsize=0)
        self.buf = b''
        self.log: list[dict] = []

    def receive(self) -> dict:
        deadline = time.monotonic() + 3
        while b'\n' not in self.buf:
            if len(self.buf) > 100_000:
                raise RuntimeError('oversized worker frame')
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([self.proc.stdout], [], [], remaining)[0]:
                raise TimeoutError('worker frame')
            chunk = os.read(self.proc.stdout.fileno(), 65536)
            if not chunk:
                raise EOFError('worker frame')
            self.buf += chunk
        line, self.buf = self.buf.split(b'\n', 1)
        now = time.monotonic_ns()
        self.log.append({'direction': 'recv', 'ns': now, 'line': line.decode()})
        return json.loads(line)

    def send(self, data: dict) -> int:
        line = json.dumps(data, sort_keys=True, separators=(',', ':'))
        now = time.monotonic_ns()
        self.proc.stdin.write((line + '\n').encode())
        self.proc.stdin.flush()
        self.log.append({'direction': 'send', 'ns': now, 'line': line})
        return now

    def close(self) -> int:
        if self.proc.stdin:
            self.proc.stdin.close()
        try:
            rc = self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=2)
            raise
        finally:
            self.err.close()
        return rc


def oracle(d) -> dict:
    from Xlib import X
    start = time.monotonic_ns()
    image = d.screen().root.get_image(48, 48, 32, 32, X.ZPixmap, 0xffffffff)
    end = time.monotonic_ns()
    b = image.data.encode('utf-8') if isinstance(image.data, str) else bytes(image.data)
    return {'start': start, 'end': end, 'depth': image.depth,
            'pixels_z64': encode(b), 'pixels_sha256': sha(b), 'bytes': len(b)}


def neutral(d) -> dict:
    return {'keys': list(d.query_keymap()), 'mask': d.screen().root.query_pointer().mask,
            'sample_ns': time.monotonic_ns()}


def run_case(display: str, d, painter: Native, index: int, kind: str,
             session: str, out: Path) -> dict:
    reqid = f'{session}/{index:02d}'
    painter.paint(1024)
    before = oracle(d)
    peer = Peer(display, out / f'{index:02d}.stderr')
    row = {'index': index, 'kind': kind, 'request_id': reqid, 'session': session,
           'before': before, 'protocol': peer.log, 'input_events': 0, 'model_calls': 0}
    try:
        ready = peer.receive()
        row['worker_ready'] = ready
        row['request_send_ns'] = peer.send({'op': 'capture', 'request_id': reqid,
                                          'session': session, 'kind': kind})
        source = peer.receive()
        if source['event'] != 'captured':
            raise RuntimeError('capture protocol')
        row['source'] = source['capture']
        if kind == 'delayed_changed':
            painter.paint(0)
        row['display_ready_ns'] = time.monotonic_ns()
        if kind.startswith('delayed'):
            due = row['source']['native'][2] + HOLD_NS
            while True:
                remaining = due - time.monotonic_ns()
                if remaining <= 0:
                    break
                time.sleep(remaining / 1e9)
        row['release_send_ns'] = peer.send({'op': 'deliver'})
        message = peer.receive()
        if message['event'] != 'delivered':
            raise RuntimeError('delivery protocol')
        row['packet'] = message['packet']
        row['publish_ns'] = message['publish_ns']
        row['consume_ns'] = time.monotonic_ns()
        row['capture_age'] = decide(row['packet'], reqid, session, row['consume_ns'], True)
        row['arrival_age'] = decide(row['packet'], reqid, session, row['consume_ns'], False)
        row['current'] = oracle(d)
        row['neutral'] = neutral(d)
    finally:
        try:
            row['worker_exit'] = peer.close()
        finally:
            row['protocol'] = peer.log
            (out / f'{index:02d}.partial.json').write_text(json.dumps(row, sort_keys=True) + '\n')
    return row


def run(out: Path, construction: bool) -> None:
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    authority = out / 'Xauthority'
    authority.touch(exist_ok=False)
    os.environ['XAUTHORITY'] = str(authority)
    freeze = None
    if not construction:
        freeze = json.loads((ROOT / 'FREEZE.json').read_text())
        for name, digest in freeze['files'].items():
            if sha((ROOT / name).read_bytes()) != digest:
                raise RuntimeError(f'source mismatch {name}')
    session = ('construction' if construction else 'observation-consumption-age-20260922-01')
    header = {'event': 'header', 'session': session, 'mode': 'construction' if construction else 'formal',
              'age_ns': AGE_NS, 'hold_ns': HOLD_NS, 'repetitions': 1 if construction else 3,
              'pid': os.getpid(), 'time_namespace': clock_namespace(),
              'freeze_sha256': None if construction else sha((ROOT / 'FREEZE.json').read_bytes()),
              'argv': sys.argv, 'input_events': 0, 'model_calls': 0}
    rawfile = (out / 'raw.jsonl').open('x', encoding='utf-8')
    def record(data):
        rawfile.write(json.dumps(data, sort_keys=True, separators=(',', ':')) + '\n')
        rawfile.flush()
    record(header)
    xr, xw = os.pipe()
    xerr = (out / 'xvfb.stderr').open('xb')
    xvfb = subprocess.Popen(['Xvfb', '-displayfd', str(xw), '-screen', '0', '128x128x24',
                             '-nolisten', 'tcp', '-noreset'], pass_fds=(xw,),
                            stdout=subprocess.DEVNULL, stderr=xerr)
    os.close(xw)
    d = painter = None
    disposition = 'COMPLETED_UNSCORED'
    try:
        if not select.select([xr], [], [], 3)[0]:
            raise TimeoutError('Xvfb readiness')
        display = ':' + os.read(xr, 128).decode().strip()
        os.close(xr)
        from Xlib.display import Display
        d = Display(display)
        painter = Native(display)
        record({'event': 'display', 'display': display, 'pid': xvfb.pid,
                'argv': xvfb.args, 'initial_neutral': neutral(d)})
        for rep in range(header['repetitions']):
            for j, kind in enumerate(KINDS):
                row = run_case(display, d, painter, rep * len(KINDS) + j, kind, session, out)
                row['event'] = 'case'
                record(row)
    except Exception as e:
        disposition = 'STOP_SOURCE_OR_INFRASTRUCTURE'
        record({'event': 'stop', 'error': repr(e), 'traceback': traceback.format_exc()})
    finally:
        try:
            if painter:
                painter.paint(0)
                record({'event': 'cleanup', 'frame': oracle(d), 'neutral': neutral(d)})
        except Exception as e:
            disposition = 'STOP_SOURCE_OR_INFRASTRUCTURE'
            record({'event': 'cleanup_error', 'error': repr(e)})
        finally:
            if painter:
                painter.close()
            if d:
                d.close()
            xvfb.terminate()
            try:
                xvfb.wait(timeout=3)
            except subprocess.TimeoutExpired:
                xvfb.kill()
                xvfb.wait(timeout=3)
            xerr.close()
            record({'event': 'exit', 'xvfb_exit': xvfb.returncode, 'status': disposition})
            rawfile.close()
    print(disposition, flush=True)
    if disposition != 'COMPLETED_UNSCORED':
        raise SystemExit(2)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--worker')
    p.add_argument('--out', type=Path)
    p.add_argument('--construction', action='store_true')
    a = p.parse_args()
    if a.worker:
        worker(a.worker)
    elif a.out:
        run(a.out, a.construction)
    else:
        p.error('--worker or --out required')
