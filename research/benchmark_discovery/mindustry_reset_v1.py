#!/usr/bin/env python3
"""One canonical save creation, then two fresh paused GUI reloads; setup only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'observation_gating'))
from gui_suite import Session
from PIL import ImageGrab

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out = a.out.resolve()
    a.out.mkdir(parents=True, exist_ok=False)
    jar = a.root / 'Mindustry-v160.2-complete.jar'
    r = a.root / 'root/usr'
    sources = [Path(__file__), *sorted((HERE / 'mindustry_reset_mod_v1').rglob('*')),
               HERE.parent / 'observation_gating/gui_suite.py',
               HERE.parent / 'real_apps_v1/real_app_suite_v1.py']
    dump(a.out / 'manifest.json', {'sources': {str(p.relative_to(HERE.parent)): sha(p)
         for p in sources if p.is_file()}, 'jar_sha256': sha(jar),
         'scope': 'setup projection, not controller or performance evaluation',
         'timeout_s': 60, 'reloads': 2, 'rendering': 'software GL',
         'kernel': os.uname().release})
    results = []
    for label in ('create', 'reload-1', 'reload-2'):
        out = a.out / label
        out.mkdir()
        s = Session()
        row = {'label': label}
        started = time.monotonic()
        try:
            libs = r / 'lib/x86_64-linux-gnu'
            s.env.update(LD_LIBRARY_PATH=f'{libs}:{libs}/pulseaudio',
                         LIBGL_ALWAYS_SOFTWARE='1', SDL_VIDEODRIVER='x11',
                         SDL_AUDIODRIVER='dummy', ALSOFT_DRIVERS='null')
            s.env.pop('PULSE_SERVER', None)
            home = Path(s.env['HOME'])
            data = home / 'mindustry'
            shutil.copytree(HERE / 'mindustry_reset_mod_v1', data / 'mods/interface-reset-study')
            s.env['MINDUSTRY_DATA_DIR'] = str(data)
            if label != 'create':
                shutil.copy2(a.out / 'canonical.msav', data / 'input.msav')
                row['input_sha256'] = sha(data / 'input.msav')
            cmd = [str(r / 'lib/jvm/java-21-openjdk-amd64/bin/java'), '-Xmx768m',
                   f'-Duser.home={home}', '-jar', str(jar)]
            row['command'] = cmd
            with (out / 'stdout.txt').open('w') as stdout, (out / 'stderr.txt').open('w') as stderr:
                p = s.spawn(cmd, cwd=out, stdout=stdout, stderr=stderr)
                while p.poll() is None and time.monotonic() - started < 60:
                    if (data / 'ready.txt').exists():
                        break
                    time.sleep(.1)
                row['ready'] = (data / 'ready.txt').exists()
                row['setup_s'] = time.monotonic() - started
                row['windows'] = s.windows()
                if row['ready']:
                    shutil.copy2(data / 'oracle.json', out / 'oracle.json')
                    if label == 'create':
                        shutil.copy2(data / 'canonical.msav', a.out / 'canonical.msav')
                    time.sleep(1)  # allow a paint; not a timed feedback measurement
                    ImageGrab.grab(xdisplay=s.name).save(out / 'screen.png')
                    row['screen_sha256'] = sha(out / 'screen.png')
                if p.poll() is None:
                    os.killpg(p.pid, signal.SIGTERM)
                    try:
                        p.wait(timeout=10)
                        row['forced_kill'] = False
                    except subprocess.TimeoutExpired:
                        os.killpg(p.pid, signal.SIGKILL)
                        p.wait(timeout=5)
                        row['forced_kill'] = True
                row['returncode'] = p.returncode
        except Exception as exc:
            row['error'] = repr(exc)
        finally:
            s.close()
            for proc in s.procs:
                proc.wait(timeout=5)
            row['all_owned_processes_exited'] = all(proc.poll() is not None for proc in s.procs)
            shutil.rmtree(s.tmp)
            dump(out / 'result.json', row)
            results.append(row)
            print(json.dumps(row), flush=True)
        if not row.get('ready'):
            break
    dump(a.out / 'results.json', results)
    if len(results) != 3 or not all(row.get('ready') for row in results):
        raise SystemExit(1)

if __name__ == '__main__':
    main()
