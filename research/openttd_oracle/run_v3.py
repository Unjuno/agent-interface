"""Private X11 oracle calibration, deliberately not an agent/controller runner."""
import argparse, hashlib, json, os, signal, shutil, sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_gating'))
from gui_suite import Session
from PIL import ImageGrab

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    sources=[Path(__file__).resolve(),HERE/'score.py',HERE/'plan.json',*sorted((HERE/'script_v3').glob('*')),
             HERE.parent/'observation_gating/gui_suite.py',HERE.parent/'real_apps_v1/real_app_suite_v1.py']
    manifest={'sources':{str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
              'plan':json.loads((HERE/'plan.json').read_text()),'assets_manifest_sha256':hashlib.sha256((HERE.parent/'benchmark_discovery/assets.json').read_bytes()).hexdigest()}
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    for seed in manifest['plan']['seeds']:
        out=a.out/str(seed);out.mkdir();s=Session();r=a.root/'root/usr';row={'seed':seed}
        try:
            libs=r/'lib/x86_64-linux-gnu';s.env.update(LD_LIBRARY_PATH=f'{libs}:{libs}/pulseaudio',SDL_VIDEODRIVER='x11',SDL_AUDIODRIVER='dummy',LIBGL_ALWAYS_SOFTWARE='1')
            data=Path(s.env['XDG_DATA_HOME'])/'openttd';data.mkdir()
            for f in (r/'share/games/openttd').iterdir():
                if f.name!='game': (data/f.name).symlink_to(f)
            shutil.copytree(r/'share/games/openttd/game',data/'game');shutil.copytree(HERE/'script_v3',data/'game/interface_oracle')
            cfg=out/'openttd.cfg';cfg.write_text(f'[game_creation]\nmap_x = 6\nmap_y = 6\nstarting_year = 1950\ngeneration_seed = {seed}\n[game_scripts]\nInterfaceOracle = \n')
            cmd=[str(r/'games/openttd'),'-c',str(cfg),'-g','-G',str(seed),'-d','script=4','-s','null','-m','null']
            row['command']=cmd
            with (out/'stdout.txt').open('w') as so,(out/'stderr.txt').open('w') as se:
                p=s.spawn(cmd,cwd=out,stdout=so,stderr=se);end=time.monotonic()+60
                while p.poll() is None and time.monotonic()<end:
                    log=(out/'stderr.txt').read_text()
                    if 'AIO_DONE' in log or 'AIO_FIXTURE_ERROR' in log or 'script died unexpectedly' in log:break
                    time.sleep(.2)
                row['completed']='AIO_DONE' in (out/'stderr.txt').read_text()
                ImageGrab.grab(xdisplay=s.name).save(out/'screen.png')
                row['screen_sha256']=hashlib.sha256((out/'screen.png').read_bytes()).hexdigest()
                row['alive_before_cleanup']=p.poll() is None
                if p.poll() is None:
                    os.killpg(p.pid,signal.SIGTERM)
                    try:p.wait(timeout=2)
                    except TimeoutError:pass
                    except __import__('subprocess').TimeoutExpired:os.killpg(p.pid,signal.SIGKILL)
        finally:
            s.close()
            for p in s.procs:p.wait(timeout=5)
            row['all_owned_processes_exited']=all(p.poll() is not None for p in s.procs)
            shutil.rmtree(s.tmp)
            (out/'result.json').write_text(json.dumps(row,indent=2)+'\n')
            print(json.dumps(row),flush=True)

if __name__=='__main__':main()
