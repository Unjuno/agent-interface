"""A11 preparation: fresh private GUI post-admission drift; never key replay."""
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time
from ready_guard import pre_input_errors
from private_cache import PrivateCache
from pipe_transport import PipeSession
from pipe_gate import wait_for_target
from drift import wait_for_drift,dispatch


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
    rows = [{'mode': mode, 'instrumentation_mode': 'MEMORY_ONLY',
             'load': load, 'replicate': replicate}
            for mode in ('STABLE','DRIFT_STALE_CONTROL','DRIFT_REFUSE')
            for load in ('idle',)
            for replicate in range(fixture['replicates_per_cell'])]
    random.Random(fixture['seed']).shuffle(rows)
    return rows


def send_payload(gate, payload, key, save, gap_ms, save_delay_ms):
    if gate.get('status') != 'ADMITTED':
        return
    for index, char in enumerate(payload):
        if index:
            time.sleep(gap_ms / 1000)
        key(char)
    time.sleep(save_delay_ms / 1000)
    save()


def click_geometry(ready,row):
    if row.get('mode') not in ('STABLE','DRIFT_STALE_CONTROL','DRIFT_REFUSE') or row.get('instrumentation_mode')!='MEMORY_ONLY':
        raise RuntimeError('STOP_TREATMENT')
    geometry = ready['geometry']
    click_widget = 'target'
    if (any(type(geometry.get(widget+'_'+field)) is not int
           for widget in ('target','decoy','save') for field in ('root_x','root_y','width','height')) or
           min(geometry[widget+'_'+field] for widget in ('target','decoy','save')
               for field in ('width','height'))<=1):
        raise RuntimeError('STOP_CLICK_GEOMETRY')
    return click_widget


def post_admission(gate,mode,session,binding,intervene,key,save,fixture):
    record={'intervention':None,'drift':None}
    if gate.get('status')=='ADMITTED' and mode in ('DRIFT_STALE_CONTROL','DRIFT_REFUSE'):
        record['intervention']=intervene()
        record['drift']=wait_for_drift(session,binding,gate['ack']['sequence'],
            record['intervention']['started_ns'],
            timeout_ns=fixture['drift_timeout_ms']*1_000_000,
            poll_ns=fixture['ack_poll_ms']*1_000_000,
            max_age_ns=fixture['ack_max_age_ms']*1_000_000)
    record['dispatch_started_ns']=time.monotonic_ns()
    record['dispatch']=dispatch(gate,mode,record['drift'],fixture['payload'],key,save)
    record['dispatch_completed_ns']=time.monotonic_ns()
    return record


def inject(ready, row, fixture, pipe_session, binding):
    errors = pre_input_errors(ready)
    if errors:
        raise RuntimeError('STOP_PRE_INPUT:' + ','.join(errors))
    click_widget=click_geometry(ready,row)
    geometry=ready['geometry']
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
        gate=wait_for_target(pipe_session,binding,record['click_started_ns'],
            timeout_ns=fixture['ack_timeout_ms']*1_000_000,
            poll_ns=fixture['ack_poll_ms']*1_000_000,
            max_age_ns=fixture['ack_max_age_ms']*1_000_000)
        record['gate'] = gate

        def key(char):
            if record['key_requests']:
                time.sleep(fixture['inter_key_gap_ms']/1000)
            started = time.monotonic_ns()
            code = xd.keysym_to_keycode(ord(char))
            xtest.fake_input(xd, X.KeyPress, detail=code)
            xtest.fake_input(xd, X.KeyRelease, detail=code)
            xd.sync()
            record['key_requests'].append({'index': len(record['key_requests']),
                'char': char, 'keycode': code, 'request_started_ns': started,
                'sync_returned_ns': time.monotonic_ns()})

        def save():
            time.sleep(fixture['save_delay_after_last_key_ms']/1000)
            sx = geometry['save_root_x'] + geometry['save_width'] // 2
            sy = geometry['save_root_y'] + geometry['save_height'] // 2
            started = time.monotonic_ns()
            xtest.fake_input(xd, X.MotionNotify, x=sx, y=sy)
            xtest.fake_input(xd, X.ButtonPress, detail=1, x=sx, y=sy)
            xtest.fake_input(xd, X.ButtonRelease, detail=1, x=sx, y=sy)
            xd.sync()
            record['save_requests'].append({'x': sx, 'y': sy, 'request_started_ns': started,
                                            'sync_returned_ns': time.monotonic_ns()})

        def intervene():
            dx=geometry['decoy_root_x']+geometry['decoy_width']//2
            dy=geometry['decoy_root_y']+geometry['decoy_height']//2
            trace={'started_ns':time.monotonic_ns(),'x':dx,'y':dy,'widget':'decoy'}
            xtest.fake_input(xd,X.MotionNotify,x=dx,y=dy)
            xtest.fake_input(xd,X.ButtonPress,detail=1,x=dx,y=dy)
            xtest.fake_input(xd,X.ButtonRelease,detail=1,x=dx,y=dy)
            xd.sync()
            trace['completed_ns']=time.monotonic_ns()
            return trace
        record['post_admission']=post_admission(gate,row['mode'],pipe_session,
            binding,intervene,key,save,fixture)
        if record['post_admission']['dispatch']['status']=='STOP':
            record['method_stop']='STOP_POST_ADMISSION'
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
            cache = None
            pipe_session = None
            try:
                if plan['load'] == 'cpu_busy':
                    worker = subprocess.Popen([sys.executable, '-c',
                        worker_code(fixture['busy_worker_duration_ms']/1000)],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                cache = PrivateCache(token)
                pipe_session=PipeSession()
                if pipe_session.identity['pipe_buf'] is None:
                    raise RuntimeError('STOP_PIPE_BUF_UNPROVEN')
                app = subprocess.Popen([sys.executable, str(source/'app.py'), str(row_dir), token,
                    plan['instrumentation_mode'],str(pipe_session.write_fd)],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                    pass_fds=(pipe_session.write_fd,),
                    env=cache.environment(os.environ))
                pipe_session.release_parent_writer()
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
                binding={'token':token,'pid':app.pid,'target_id':ready['geometry']['target_id'],
                         'freeze_sha256':sha(source/'FREEZE.json')}
                row['injection'] = inject(ready, plan, fixture, pipe_session,binding)
                stdout, stderr = app.communicate(timeout=5)
                pipe_session.drain()
                pipe_session.finish()
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
            finally:
                if pipe_session is not None:
                    try:pipe_session.close()
                    except Exception as error:
                        row.setdefault('runner_error','STOP_PIPE_CLEANUP:'+type(error).__name__+':'+str(error))
                    row['pipe']={'identity':pipe_session.identity,'reads':pipe_session.reads,
                        'frames':pipe_session.frames,'eof':pipe_session.eof,'closes':pipe_session.closes}
                if cache is not None:
                    try:
                        cache.cleanup()
                    except Exception as error:
                        row.setdefault('runner_error','STOP_CACHE_CLEANUP:'+type(error).__name__+':'+str(error))
                    row['cache']=cache.snapshot()
            rows.append(row)
            if row.get('runner_error') or row.get('injection',{}).get('method_stop'):
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
    exit_code = 0 if len(rows)==6 and all(r.get('app_exit')==0 and not r.get('runner_error') and
        not r.get('injection',{}).get('method_stop') for r in rows) else 1
    (out/'candidate_exit.txt').write_text(str(exit_code)+'\n',encoding='utf-8')
    print(json.dumps({'rows':len(rows),'exit_code':exit_code}, sort_keys=True))
    return exit_code


if __name__=='__main__':
    raise SystemExit(run(sys.argv[1],sys.argv[2]))
