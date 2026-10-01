"""Visual readiness self-use through unchanged shared session_v9/executor_v3."""
import argparse
import contextlib
import hashlib
import json
from pathlib import Path
import shutil
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'live_control'))
from session_v9 import Backend, suite
from executor_v3 import Executor
from lease import Expired

SAVE = HERE / 'results/mindustry-reset-01/canonical.msav'
SAVE_SHA = '8fff67b0c130ee59a3838c92754b73225a506902bd4838dcc3f1fb5be286cbed'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def dump(p, value):
    p.write_text(json.dumps(value, indent=2) + '\n')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out = a.out.resolve()
    a.out.mkdir(parents=True, exist_ok=False)
    assert sha(SAVE) == SAVE_SHA
    sources = [Path(__file__), *sorted((HERE / 'mindustry_control_mod_v1').rglob('*'))]
    sources += [HERE.parent / 'live_control' / n for n in (
        'session_v9.py','session_v8.py','session_v7.py','session_v6.py','session_v5.py',
        'session_v4.py','input_owner_v5.py','executor_v3.py','lease.py')]
    sources += [HERE.parent / 'observation_gating/gui_suite.py',
                HERE.parent / 'real_apps_v1/real_app_suite_v1.py',
                HERE.parent / 'observation_tiles/tile_transport.py',
                HERE.parent / 'observation_tiles/image_artifact.py']
    dump(a.out / 'manifest.json', {'save_sha256':SAVE_SHA,
         'sources':{str(p.relative_to(HERE.parent)):sha(p) for p in sources if p.is_file()},
         'scope':'assistant GUI readiness self-use; oracle read only after control closes',
         'declared_check':'resume; observe spawned unit; hold d to move right; pause; inspect independent samples',
         'gameplay_task_success':None, 'model_tokens':None})
    lock = threading.Lock()
    s = backend = engine = None
    def emit(record):
        with lock:
            record['emitted_ns'] = time.perf_counter_ns()
            line = json.dumps(record)
            with (a.out / 'events.jsonl').open('a') as f:
                f.write(line + '\n')
            print(line, flush=True)
    try:
        with (a.out / 'setup.txt').open('w') as setup, contextlib.redirect_stdout(setup):
            s = suite.Session()
            r = a.root / 'root/usr'
            libs = r / 'lib/x86_64-linux-gnu'
            s.env.update(LD_LIBRARY_PATH=f'{libs}:{libs}/pulseaudio',
                         LIBGL_ALWAYS_SOFTWARE='1', SDL_VIDEODRIVER='x11',
                         SDL_AUDIODRIVER='dummy', ALSOFT_DRIVERS='null')
            s.env.pop('PULSE_SERVER', None)
            home = Path(s.env['HOME'])
            data = home / 'mindustry'
            shutil.copytree(HERE / 'mindustry_control_mod_v1', data / 'mods/interface-readiness-study')
            shutil.copy2(SAVE, data / 'input.msav')
            s.env['MINDUSTRY_DATA_DIR'] = str(data)
            jar = a.root / 'Mindustry-v160.2-complete.jar'
            dump(a.out / 'assets.json', {'jar_sha256':sha(jar)})
            with (a.out / 'game-stdout.txt').open('w') as so, (a.out / 'game-stderr.txt').open('w') as se:
                p = s.spawn([str(r / 'lib/jvm/java-21-openjdk-amd64/bin/java'),
                    '-Xmx768m',f'-Duser.home={home}','-jar',str(jar)],cwd=a.out,stdout=so,stderr=se)
            s._wait(lambda:(data / 'ready.txt').exists(),60,'saved fixture ready')
            s.wait_window('Mindustry')
            s.focus('Mindustry')
            time.sleep(1)
            backend = Backend(s,a.out,emit)
        engine = Executor(backend,emit)
        emit({'event':'ready','task':'Resume with Space; visually inspect player readiness, move right with d, then pause. No construction score.'})
        backend.snapshot('initial',0)
        for line in sys.stdin:
            try:
                c = json.loads(line)
                emit({'event':'command','command':c})
                if c['op']=='submit':
                    engine.submit(c['id'],c['steps'],c['expected_sequence'],c['valid_until_ns'])
                elif c['op']=='clock':
                    emit({'event':'clock','runtime_ns':time.perf_counter_ns(),'sequence':backend.sequence})
                elif c['op']=='cancel':
                    engine.cancel(c['id'])
                elif c['op']=='finish':
                    engine.close()
                    time.sleep(.3)
                    shutil.copy2(data / 'readiness.jsonl',a.out / 'readiness.jsonl')
                    emit({'event':'oracle_archived','task_success':None});break
                else:
                    raise ValueError('unsupported command')
            except (ValueError,KeyError,TypeError,Expired) as exc:
                emit({'event':'rejected','reason':str(exc)})
    finally:
        if engine:
            engine.close()
        if backend:
            try:
                backend.close()
            finally:
                dump(a.out / 'owner-events.json',backend.owner.records)
        if s:
            # Preserve diagnostic oracle on failures too; never expose it during control.
            if 'data' in locals() and (data / 'readiness.jsonl').exists() and not (a.out / 'readiness.jsonl').exists():
                shutil.copy2(data / 'readiness.jsonl',a.out / 'readiness.jsonl')
            s.close()
            dump(a.out / 'cleanup.json',{'all_owned_processes_exited':all(p.poll() is not None for p in s.procs),
                 'save_unchanged':sha(SAVE)==SAVE_SHA})
            shutil.rmtree(s.tmp)

if __name__=='__main__':
    main()
