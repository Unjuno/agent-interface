"""One new bounded focus-ack construction; no automatic retry or key replay."""
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time
from focus_ack import acknowledgement_errors
from ready_guard import pre_input_errors


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        stream.write(json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def planned_rows(fixture):
    rows = [{'mode': mode, 'load': load, 'replicate': replicate}
            for mode in ('NOW_TARGET', 'ACK_TARGET', 'ACK_WRONG_TARGET')
            for load in ('idle', 'cpu_busy')
            for replicate in range(1 if mode == 'ACK_WRONG_TARGET' else fixture['replicates_per_cell'])]
    random.Random(fixture['seed']).shuffle(rows)
    return rows


def read_acknowledgement(root, binding, timeout_ms, max_age_ms):
    started = time.monotonic_ns()
    deadline = started + timeout_ms * 1_000_000
    last_errors = ['receipt_absent']
    while time.monotonic_ns() < deadline:
        try:
            ack = json.loads((Path(root) / 'focus_ack.json').read_bytes())
            state = json.loads((Path(root) / 'focus_state.json').read_bytes())
            seen = time.monotonic_ns()
            last_errors = acknowledgement_errors(ack, state, binding, seen, max_age_ms)
            if not last_errors and seen < deadline:
                return {'status': 'ADMITTED', 'ack': ack, 'state': state,
                        'poll_started_ns': started, 'seen_ns': seen,
                        'decided_ns': time.monotonic_ns(), 'errors': []}
        except (OSError, ValueError):
            last_errors = ['receipt_absent_or_unparseable']
        time.sleep(0.001)
    return {'status': 'REFUSED_NO_FOCUS_ACK', 'ack': None, 'state': None,
            'poll_started_ns': started, 'seen_ns': None,
            'decided_ns': time.monotonic_ns(), 'errors': last_errors}


def send_payload(gate, payload, key, save, gap_ms, save_delay_ms):
    if gate.get('status') != 'ADMITTED':
        return
    for index, char in enumerate(payload):
        if index:
            time.sleep(gap_ms / 1000)
        key(char)
    time.sleep(save_delay_ms / 1000)
    save()


def inject(ready, row, fixture, row_dir):
    errors = pre_input_errors(ready)
    if errors:
        raise RuntimeError('STOP_PRE_INPUT:' + ','.join(errors))
    geometry = ready['geometry']
    click_widget = 'decoy' if row['mode'] == 'ACK_WRONG_TARGET' else 'target'
    if any(type(geometry.get(click_widget + '_' + field)) is not int
           for field in ('root_x','root_y','width','height')) or min(
           geometry[click_widget+'_width'],geometry[click_widget+'_height']) <= 1:
        raise RuntimeError('STOP_CLICK_GEOMETRY')
    from Xlib import X, display
    from Xlib.ext import xtest
    x = geometry[click_widget + '_root_x'] + geometry[click_widget + '_width'] // 2
    y = geometry[click_widget + '_root_y'] + geometry[click_widget + '_height'] // 2
    xd = display.Display()
    record = {'click_widget': click_widget, 'x': x, 'y': y,
              'key_requests': [], 'save_requests': []}
    try:
        record['click_started_ns'] = time.monotonic_ns()
        xtest.fake_input(xd, X.MotionNotify, x=x, y=y)
        xtest.fake_input(xd, X.ButtonPress, detail=1, x=x, y=y)
        xtest.fake_input(xd, X.ButtonRelease, detail=1, x=x, y=y)
        xd.sync()
        record['click_sync_returned_ns'] = time.monotonic_ns()
        if row['mode'] == 'NOW_TARGET':
            gate = {'status': 'ADMITTED', 'ack': None, 'state': None,
                    'decided_ns': time.monotonic_ns(), 'mode': 'NO_ACK_CONTROL'}
        else:
            binding = {key: ready[key] for key in ('token', 'pid', 'ready_ns')}
            binding.update(target_id=geometry['target_id'],
                           click_started_ns=record['click_started_ns'])
            gate = read_acknowledgement(row_dir, binding, fixture['ack_timeout_ms'],
                                        fixture['max_ack_age_ms'])
        record['gate'] = gate

        def key(char):
            started = time.monotonic_ns()
            code = xd.keysym_to_keycode(ord(char))
            xtest.fake_input(xd, X.KeyPress, detail=code)
            xtest.fake_input(xd, X.KeyRelease, detail=code)
            xd.sync()
            record['key_requests'].append({'index': len(record['key_requests']),
                'char': char, 'keycode': code, 'request_started_ns': started,
                'sync_returned_ns': time.monotonic_ns()})

        def save():
            sx = geometry['save_root_x'] + geometry['save_width'] // 2
            sy = geometry['save_root_y'] + geometry['save_height'] // 2
            started = time.monotonic_ns()
            xtest.fake_input(xd, X.MotionNotify, x=sx, y=sy)
            xtest.fake_input(xd, X.ButtonPress, detail=1, x=sx, y=sy)
            xtest.fake_input(xd, X.ButtonRelease, detail=1, x=sx, y=sy)
            xd.sync()
            record['save_requests'].append({'x': sx, 'y': sy, 'request_started_ns': started,
                                            'sync_returned_ns': time.monotonic_ns()})

        send_payload(gate, fixture['payload'], key, save, fixture['inter_key_gap_ms'],
                     fixture['save_delay_after_last_key_ms'])
        return record
    finally:
        xd.close()


def worker_code(duration):
    return ("import json,time; start=time.monotonic_ns(); "
            f"deadline=time.monotonic()+{duration!r}; x=1\n"
            "while time.monotonic()<deadline: x=(x*1664525+1013904223)&0xffffffff\n"
            "print(json.dumps({'start_ns':start,'end_ns':time.monotonic_ns()}),flush=True)")


def run(fixture_path, out_path):
    source = Path(__file__).resolve().parent
    fixture = json.loads(Path(fixture_path).read_bytes())
    freeze = json.loads((source / 'FREEZE.json').read_bytes())
    out = Path(out_path)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('STOP_OUTPUT_OCCUPIED:' + str(out))
    out.mkdir(parents=True, exist_ok=True)
    if os.environ.get('DISPLAY') != fixture['private_display']:
        raise RuntimeError('STOP_DISPLAY_MISMATCH')
    rows, xvfb, wm = [], None, None
    private_exit = {}
    xlog = (out / 'xvfb.log').open('wb')
    wlog = (out / 'openbox.log').open('wb')
    setup = {}
    try:
        xvfb = subprocess.Popen(['Xvfb', fixture['private_display'], '-screen', '0',
            fixture['screen'], '-nolisten', 'tcp', '-ac'], stdout=xlog, stderr=subprocess.STDOUT)
        time.sleep(0.4)
        if xvfb.poll() is not None:
            raise RuntimeError('STOP_XVFB_START')
        wm = subprocess.Popen(['openbox','--sm-disable'], stdout=wlog, stderr=subprocess.STDOUT)
        time.sleep(0.4)
        if wm.poll() is not None:
            raise RuntimeError('STOP_WM_START')
        for name, argv in [('set', ['setxkbmap','-layout','us']),
                           ('query', ['setxkbmap','-query'])]:
            result = subprocess.run(argv, capture_output=True, text=True)
            setup[name] = {'exit':result.returncode, 'stdout':result.stdout, 'stderr':result.stderr}
        if setup['set']['exit'] or setup['query']['exit'] or 'us' not in setup['query']['stdout']:
            raise RuntimeError('STOP_KEYMAP')
        for index, plan in enumerate(planned_rows(fixture)):
            row_dir = out / f'row-{index:03d}'
            row_dir.mkdir()
            token = fixture['allocation'] + f':row-{index:03d}'
            row = {'index':index, **plan, 'token':token}
            worker = None
            app = None
            try:
                if plan['load'] == 'cpu_busy':
                    worker = subprocess.Popen([sys.executable, '-c',
                        worker_code(fixture['busy_worker_duration_ms']/1000)],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                app = subprocess.Popen([sys.executable, str(source/'app.py'), str(row_dir), token],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                row.update(app_pid=app.pid, app_start_ns=time.monotonic_ns())
                deadline = time.monotonic() + 5
                while not (row_dir / 'ready.json').exists():
                    if app.poll() is not None or time.monotonic() >= deadline:
                        raise RuntimeError('STOP_READY_NOT_OBSERVED')
                    time.sleep(0.005)
                ready = json.loads((row_dir/'ready.json').read_bytes())
                if ready['pid'] != app.pid or ready['token'] != token:
                    raise RuntimeError('STOP_APP_IDENTITY')
                row['ready'] = ready
                row['injection'] = inject(ready, plan, fixture, row_dir)
                stdout, stderr = app.communicate(timeout=5)
                row.update(app_stdout=stdout, app_stderr=stderr, app_exit=app.returncode,
                           app_end_ns=time.monotonic_ns(), app=json.loads(stdout.strip()))
                if worker:
                    stdout, stderr = worker.communicate(timeout=3)
                    row['worker'] = {'pid':worker.pid, 'exit':worker.returncode,
                                     'stdout':stdout,'stderr':stderr, **json.loads(stdout)}
                else:
                    row['worker'] = {'pid':None, 'exit':None}
            except Exception as error:
                row['runner_error'] = type(error).__name__ + ':' + str(error)
                if app and app.poll() is None:
                    app.kill()
                    stdout, stderr = app.communicate()
                    row.update(app_stdout=stdout, app_stderr=stderr, app_exit=app.returncode)
                if worker and worker.poll() is None:
                    worker.kill()
                    stdout, stderr = worker.communicate()
                    row['worker'] = {'pid':worker.pid,'exit':worker.returncode,
                                     'stdout':stdout,'stderr':stderr}
            rows.append(row)
            if row.get('runner_error'):
                break
    finally:
        for name, process, stream in (('openbox',wm,wlog),('xvfb',xvfb,xlog)):
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            private_exit[name] = process.returncode if process else None
            stream.close()
    raw = {'schema':fixture['schema'],'allocation':fixture['allocation'],
           'fixture':fixture,'schedule':planned_rows(fixture),'rows':rows,
           'source_sha256':{name:sha(source/name) for name in freeze['sha256']},
           'freeze_sha256':sha(source/'FREEZE.json'),'fixture_sha256':sha(fixture_path),
           'environment':{'python':sys.version,'tk':__import__('tkinter').TkVersion,
             'image_id':os.environ.get('EXPERIMENT_IMAGE_ID'),'display':os.environ.get('DISPLAY'),
             'container_id':os.environ.get('HOSTNAME'),'private_exit':private_exit,'keymap':setup}}
    write_json(out / 'candidate_stdout.json', raw)
    exit_code = 0 if len(rows)==10 and all(r.get('app_exit')==0 and not r.get('runner_error') for r in rows) else 1
    (out/'candidate_exit.txt').write_text(str(exit_code)+'\n',encoding='utf-8')
    print(json.dumps({'rows':len(rows),'exit_code':exit_code}, sort_keys=True))
    return exit_code


if __name__=='__main__':
    raise SystemExit(run(sys.argv[1],sys.argv[2]))
