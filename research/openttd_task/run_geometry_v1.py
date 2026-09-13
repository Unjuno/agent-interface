"""Generate and restore the seed-991002 shifted-viewport task fixture."""
import argparse,hashlib,json,os,shutil,signal,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_gating'))
from gui_suite import Session,base
from PIL import ImageGrab

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    sources=[Path(__file__).resolve(),HERE/'plan_geometry_v1.json',*sorted((HERE/'setup_geometry_v1').glob('*')),*sorted((HERE/'observer_v2').glob('*')),
             HERE.parent/'observation_gating/gui_suite.py',HERE.parent/'real_apps_v1/real_app_suite_v1.py']
    manifest={'sources':{p.relative_to(HERE.parent).as_posix():sha(p) for p in sources},'plan':json.loads((HERE/'plan_geometry_v1.json').read_text())}
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    saved=a.out/'baseline.sav'
    for phase in ['setup','unsaved','restore-1','restore-2']:
        out=a.out/phase;out.mkdir();s=Session();row={'phase':phase};r=a.root/'root/usr'
        try:
            libs=r/'lib/x86_64-linux-gnu';s.env.update(LD_LIBRARY_PATH=f'{libs}:{libs}/pulseaudio',SDL_VIDEODRIVER='x11',SDL_AUDIODRIVER='dummy',LIBGL_ALWAYS_SOFTWARE='1')
            data=Path(s.env['XDG_DATA_HOME'])/'openttd';data.mkdir()
            for f in (r/'share/games/openttd').iterdir():
                if f.name!='game':(data/f.name).symlink_to(f)
            shutil.copytree(r/'share/games/openttd/game',data/'game')
            shutil.copytree(HERE/('setup_geometry_v1' if phase=='setup' else 'observer_v2'),data/'game/interface_task')
            cfg=out/'openttd.cfg';cfg.write_text('[game_creation]\nmap_x = 6\nmap_y = 6\nstarting_year = 1950\n[game_scripts]\nInterfaceTask = \n')
            cmd=[str(r/'games/openttd'),'-c',str(cfg),'-d','script=4','-s','null','-m','null','-r','1024x720','-g']
            cmd+= [str(saved)] if phase.startswith('restore') else ['-G','991002']
            row['command']=cmd
            if saved.exists():row['save_before']=sha(saved)
            with (out/'stdout.txt').open('w') as so,(out/'stderr.txt').open('w') as se:
                p=s.spawn(cmd,cwd=out,stdout=so,stderr=se);deadline=time.monotonic()+40
                while p.poll() is None and time.monotonic()<deadline:
                    log=(out/'stderr.txt').read_text()
                    if any(t in log for t in ['AIT_READY','AIT_ERROR','script died unexpectedly']):break
                    time.sleep(.1)
                row['ready']='AIT_READY' in (out/'stderr.txt').read_text()
                if phase=='setup' and row['ready']:
                    s.focus('OpenTTD');driver=base.Driver(s,settle_ms=20)
                    base.CHAR_GAP_MS=12;driver.key('grave');time.sleep(.2)
                    record=next(json.loads(l.split('AIT ',1)[1]) for l in (out/'stderr.txt').read_text().splitlines() if 'AIT {' in l)
                    row['setup_scroll_command']='scrollto '+str((record['y']+3)*record['width']+record['x']+6)
                    row['target_contract']={'x':record['x'],'y':record['y'],'width':record['width'],'target':[record['y']*record['width']+record['x']+dx for dx in range(3)]}
                    assert row['target_contract']['target'] != [678,679,680]
                    driver.text(row['setup_scroll_command']);driver.key('Return');time.sleep(.3)
                    temporary=s.tmp/'baseline.sav'
                    row['setup_console_command']='save '+str(temporary.with_suffix(''))
                    driver.text(row['setup_console_command']);driver.key('Return')
                    deadline=time.monotonic()+15;last=None;stable=0
                    while time.monotonic()<deadline:
                        if temporary.exists():
                            size=temporary.stat().st_size
                            stable=stable+1 if size==last and size>0 else 0;last=size
                            if stable>=3:break
                        time.sleep(.2)
                    if not temporary.exists() or stable<3:raise RuntimeError('save not completed')
                    shutil.copy2(temporary,saved);row['save_created']=sha(saved)
                    driver.key('grave')
                time.sleep(.4)
                ImageGrab.grab(xdisplay=s.name).save(out/'screen.png');row['screen_sha256']=sha(out/'screen.png')
                if p.poll() is None:
                    os.killpg(p.pid,signal.SIGTERM)
                    try:p.wait(timeout=2)
                    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL)
            if saved.exists():row['save_after']=sha(saved)
        except Exception as e:
            row['error']=repr(e)
            ImageGrab.grab(xdisplay=s.name).save(out/'error-screen.png')
            row['temporary_files']=[str(f.relative_to(s.tmp)) for f in s.tmp.rglob('*') if f.is_file()]

        finally:
            s.close()
            for p in s.procs:p.wait(timeout=5)
            row['all_owned_processes_exited']=all(p.poll() is not None for p in s.procs)
            shutil.rmtree(s.tmp)
            (out/'result.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row),flush=True)
        if phase=='setup' and not saved.exists():break

if __name__=='__main__':main()


