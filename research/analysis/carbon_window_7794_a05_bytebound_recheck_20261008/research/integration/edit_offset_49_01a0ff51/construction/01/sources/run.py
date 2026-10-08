"""Frozen first-outcome native cells using unchanged main X11Backend source."""
import argparse
import dataclasses
import hashlib
import json
import os
import platform
import select
import subprocess
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'vendor'))
from runtime.backends.x11_v1.backend import X11Backend
from runtime.core_v1.contract import admit_program
from policy import lower


class Lines:
    def __init__(self, pipe):
        self.pipe, self.buffer = pipe, b''
    def read(self, timeout=3):
        deadline = time.monotonic() + timeout
        while b'\n' not in self.buffer:
            left = deadline - time.monotonic()
            if left <= 0 or not select.select([self.pipe], [], [], left)[0]:
                raise TimeoutError('fixture complete frame deadline')
            chunk = os.read(self.pipe.fileno(), 65536)
            if not chunk:
                raise EOFError('fixture EOF')
            self.buffer += chunk
        line, self.buffer = self.buffer.split(b'\n', 1)
        return json.loads(line)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--cases', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir()
    cases = json.loads(a.cases.read_text())
    raw = dict(schema='edit49-native-v1', cases_sha256=hashlib.sha256(a.cases.read_bytes()).hexdigest(),
               python=sys.version, platform=platform.platform(), backend_module=sys.modules[X11Backend.__module__].__file__,
               rows=[])
    def retain():
        (a.output / 'raw.json').write_text(json.dumps(raw, ensure_ascii=False, indent=2) + '\n')
    retain()
    n = 0
    for case in cases:
        for widget in ['plain', 'rich']:
            for arm in ['untyped', 'typed']:
                n += 1
                cell_id = case['id'] + '-' + widget + '-' + arm
                cell = dict(case, widget=widget, arm=arm, cell_id=cell_id)
                out = a.output / cell_id
                out.mkdir()
                row = dict(cell_id=cell_id, display=':' + str(120 + n), cell=cell, outcome='STARTED')
                raw['rows'].append(row)
                retain()
                env = dict(os.environ, DISPLAY=row['display'], QT_QPA_PLATFORM='xcb')
                xvfb = app = backend = None
                xf = (out / 'xvfb.stderr').open('xb')
                af = (out / 'app.stderr').open('xb')
                try:
                    xvfb = subprocess.Popen(['Xvfb', row['display'], '-screen', '0', '640x240x24', '-nolisten', 'tcp'], env=env, stdout=subprocess.DEVNULL, stderr=xf)
                    deadline = time.monotonic() + 3
                    while not Path('/tmp/.X11-unix/X' + row['display'][1:]).exists():
                        if xvfb.poll() is not None or time.monotonic() > deadline:
                            raise TimeoutError('Xvfb startup')
                        time.sleep(.01)
                    app = subprocess.Popen([sys.executable, '-B', str(Path(__file__).with_name('app.py')), '--cell', json.dumps(cell), '--output', str(out)], env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=af)
                    lines = Lines(app.stdout)
                    def command(data):
                        app.stdin.write((json.dumps(data) + '\n').encode()); app.stdin.flush()
                    row['ready'] = lines.read()
                    before = row['ready']['text']
                    refusal = None
                    if arm == 'untyped':
                        span = list(case['span'])
                    else:
                        try:
                            span = lower(case['context'], before, case['span'], case['unit'])
                        except ValueError as e:
                            refusal = str(e)
                    backend = X11Backend(row['display'], {'fixture': row['ready']['xid']})
                    row['manifest'] = backend.manifest()
                    if refusal:
                        row['refusal'] = refusal
                        row['execution'] = None
                        row['outcome'] = 'REFUSED_BEFORE_INPUT'
                    else:
                        row['lowered_span'] = span
                        command(dict(op='select', span=span))
                        row['selection'] = lines.read()
                        now = time.monotonic_ns()
                        program = {'schema': 'agent-interface/program-v1', 'program_id': 'edit49-' + str(n),
                                   'source': {'observation_seq': 1, 'binding_revision': 1},
                                   'authority': {'lease_id': 'private-fixture', 'expires_at_ns': now + 3_000_000_000},
                                   'terminal': {'release_all_required': True},
                                   'ops': [{'op': 'focus', 'target': 'fixture'}, {'op': 'text', 'text': 'X'}, {'op': 'release_all'}]}
                        row['program'] = program
                        admission = admit_program(program, row['manifest'], current_observation_seq=1,
                                                  current_binding_revision=1, now_ns=now)
                        row['admission'] = dataclasses.asdict(admission)
                        if not admission.accepted:
                            raise ValueError('main contract refused fixture program')
                        row['execution'] = backend.execute(program)
                        row['outcome'] = 'INPUT_PROGRAM_RETURNED'
                    row['keymap_hex'] = bytes(backend.d.query_keymap()).hex()
                    row['focus_xid'] = backend.d.get_input_focus().focus.id
                    row['final_release'] = backend.release_all()
                    command(dict(op='save'))
                    row['saved_reply'] = lines.read()
                    command(dict(op='quit'))
                    row['app_exit'] = app.wait(timeout=3)
                except Exception as e:
                    row['outcome'] = 'STOP_FIRST_CELL_ERROR'
                    row['error'] = type(e).__name__ + ': ' + str(e)
                finally:
                    if backend:
                        backend.close()
                    if app and app.poll() is None:
                        app.terminate()
                        try: app.wait(timeout=1)
                        except subprocess.TimeoutExpired: app.kill(); app.wait(timeout=1)
                        row['forced_app_cleanup'] = True
                        row['app_exit'] = app.returncode
                    if xvfb:
                        xvfb.terminate()
                        try: xvfb.wait(timeout=2)
                        except subprocess.TimeoutExpired: xvfb.kill(); xvfb.wait(timeout=1)
                        row['xvfb_exit'] = xvfb.returncode
                    xf.close(); af.close()
                    row['artifacts'] = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file()}
                    retain()
                if row['outcome'] == 'STOP_FIRST_CELL_ERROR':
                    raise SystemExit(1)
    print(json.dumps({'rows': len(raw['rows']), 'raw_sha256': hashlib.sha256((a.output / 'raw.json').read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
