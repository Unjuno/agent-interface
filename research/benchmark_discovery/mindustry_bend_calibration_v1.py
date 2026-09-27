"""Fresh private GUI per authored transport calibration case; no agent control."""
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
sys.path.insert(0,str(HERE.parent/'observation_gating'))
from gui_suite import Session
from PIL import ImageGrab

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def dump(p,value):
    p.write_text(json.dumps(value,indent=2)+'\n')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
    plan=json.loads((HERE/'mindustry_bend_plan_v1.json').read_text())
    save=HERE/'results/mindustry-reset-01/canonical.msav'
    assert sha(save)==plan['save_sha256']
    jar=a.root/'Mindustry-v160.2-complete.jar'
    sources=[Path(__file__),HERE/'mindustry_bend_plan_v1.json',*sorted((HERE/'mindustry_bend_mod_v1').rglob('*')),
             HERE.parent/'observation_gating/gui_suite.py',HERE.parent/'real_apps_v1/real_app_suite_v1.py']
    dump(a.out/'manifest.json',{'plan':plan,'jar_sha256':sha(jar),'sources':{
        str(p.relative_to(HERE.parent)):sha(p) for p in sources if p.is_file()}})
    results=[]
    for case in plan['cases']:
        out=a.out/case;out.mkdir();s=Session();row={'case':case};start=time.monotonic()
        try:
            r=a.root/'root/usr';libs=r/'lib/x86_64-linux-gnu';home=Path(s.env['HOME']);data=home/'mindustry'
            s.env.update(LD_LIBRARY_PATH=f'{libs}:{libs}/pulseaudio',LIBGL_ALWAYS_SOFTWARE='1',
                         SDL_VIDEODRIVER='x11',SDL_AUDIODRIVER='dummy',ALSOFT_DRIVERS='null',MINDUSTRY_DATA_DIR=str(data))
            s.env.pop('PULSE_SERVER',None)
            shutil.copytree(HERE/'mindustry_bend_mod_v1',data/'mods/interface-flow-calibration')
            shutil.copy2(save,data/'input.msav');(data/'variant.txt').write_text(case)
            with (out/'stdout.txt').open('w') as so,(out/'stderr.txt').open('w') as se:
                p=s.spawn([str(r/'lib/jvm/java-21-openjdk-amd64/bin/java'),'-Xmx768m',
                           f'-Duser.home={home}','-jar',str(jar)],cwd=out,stdout=so,stderr=se)
                while p.poll() is None and time.monotonic()-start<60 and not (data/'ready.txt').exists():
                    time.sleep(.1)
                row['ready']=(data/'ready.txt').exists();row['setup_and_simulation_s']=time.monotonic()-start
                row['windows']=s.windows()
                if row['ready']:
                    time.sleep(.3)
                    ImageGrab.grab(xdisplay=s.name).save(out/'screen.png')
                    row['screen_sha256']=sha(out/'screen.png')
                for name in ('before','constructed','after'):
                    if (data/f'{name}.json').exists():shutil.copy2(data/f'{name}.json',out/f'{name}.json')
                if p.poll() is None:
                    os.killpg(p.pid,signal.SIGTERM)
                    try:p.wait(timeout=10);row['forced_kill']=False
                    except subprocess.TimeoutExpired:
                        os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=5);row['forced_kill']=True
                row['returncode']=p.returncode
        except Exception as exc:row['error']=repr(exc)
        finally:
            s.close()
            for proc in s.procs:proc.wait(timeout=5)
            row['all_owned_processes_exited']=all(proc.poll() is not None for proc in s.procs)
            shutil.rmtree(s.tmp);dump(out/'result.json',row);results.append(row)
            print(json.dumps(row),flush=True)
        if not row.get('ready'):break
    dump(a.out/'results.json',results)
    if len(results)!=len(plan['cases']) or not all(r.get('ready') for r in results):raise SystemExit(1)

if __name__=='__main__':main()
