"""OpenTTD seed-991003 five-tile L-road self-use through session_v22."""
import argparse,contextlib,hashlib,json,shutil,sys,threading,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'live_control'))
from session_v22 import Backend,suite
from executor_v3 import Executor
from lease import Expired
from guarded_l_score_v1 import score
SAVE=HERE/'results/l-geometry-01/baseline.sav'
SAVE_SHA='c91ea76b4dc8c280f98de2e3a4c9b34d6033c833a34fc401bd0c076a15b4bc5b'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--controller',choices=['assistant','scripted'],required=True);a=ap.parse_args()
    a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False);assert sha(SAVE)==SAVE_SHA
    sources=[Path(__file__).resolve(),HERE/'guarded_l_score_v1.py',*sorted((HERE/'observer_l_v1').glob('*.nut'))]
    sources += [HERE.parent/'live_control'/n for n in ['session_v22.py','session_v21.py','session_v20.py','session_v19.py','session_v18.py','session_v17.py','session_v16.py','session_v15.py','session_v14.py','session_v13.py','session_v12.py','session_v11.py','session_v10.py','session_v9.py','session_v8.py','session_v7.py','session_v6.py','session_v5.py','session_v4.py','input_owner_v5.py','executor_v3.py','lease.py']]
    (a.out/'manifest.json').write_text(json.dumps({'scope':a.controller+' controller; seed-991003 five-tile L objective; dynamic guard score; no engine actions during control','save_sha256':SAVE_SHA,'sources':{str(p.relative_to(HERE.parent)):sha(p) for p in sources}},indent=2)+'\n')
    lock=threading.Lock();s=None;backend=None;engine=None
    def emit(record):
        with lock:
            record['emitted_ns']=time.perf_counter_ns();line=json.dumps(record)
            with (a.out/'events.jsonl').open('a') as f:f.write(line+'\n')
            print(line,flush=True)
    try:
        with (a.out/'setup.txt').open('w') as setup,contextlib.redirect_stdout(setup):
            s=suite.Session();r=a.root/'root/usr';libs=r/'lib/x86_64-linux-gnu'
            s.env.update(LD_LIBRARY_PATH=f'{libs}:{libs}/pulseaudio',SDL_VIDEODRIVER='x11',SDL_AUDIODRIVER='dummy',LIBGL_ALWAYS_SOFTWARE='1')
            data=Path(s.env['XDG_DATA_HOME'])/'openttd';data.mkdir()
            for f in (r/'share/games/openttd').iterdir():
                if f.name!='game':(data/f.name).symlink_to(f)
            shutil.copytree(r/'share/games/openttd/game',data/'game');shutil.copytree(HERE/'observer_l_v1',data/'game/interface_task')
            cfg=a.out/'openttd.cfg';cfg.write_text('[game_scripts]\nInterfaceTask = \n')
            with (a.out/'game-stdout.txt').open('w') as so,(a.out/'game-stderr.txt').open('w') as se:
                s.spawn([str(r/'games/openttd'),'-c',str(cfg),'-d','script=4','-s','null','-m','null','-r','1024x720','-g',str(SAVE)],cwd=a.out,stdout=so,stderr=se)
            s._wait(lambda:'AIT_READY' in (a.out/'game-stderr.txt').read_text(),40,'saved L observer task ready')
            s.wait_window('OpenTTD');s.focus('OpenTTD');backend=Backend(s,a.out,emit)
        engine=Executor(backend,emit)
        emit({'event':'ready','task':'Build one connected L-shaped road from A through B to C, using only the five path tiles: three tiles across from A to B and three tiles down from B to C, sharing B. Keep the four other tiles in that 3x3 square, marked by X, free of roads and preserve surrounding roads/ownership. Use visual GUI controls.'})
        backend.snapshot('initial',0)
        for line in sys.stdin:
            try:
                command=json.loads(line);emit({'event':'command','command':command})
                if command['op']=='submit':engine.submit(command['id'],command['steps'],command['expected_sequence'],command['valid_until_ns'])
                elif command['op']=='clock':emit({'event':'clock','runtime_ns':time.perf_counter_ns(),'sequence':backend.sequence})
                elif command['op']=='cancel':engine.cancel(command['id'])
                elif command['op']=='finish':
                    engine.close()
                    def records():return [json.loads(l.split('AIT ',1)[1]) for l in (a.out/'game-stderr.txt').read_text().splitlines() if 'AIT {' in l]
                    count=len(records());s._wait(lambda:len(records())>count,5,'post-control independent L sample')
                    observation=records()[-1];baseline=records()[0];result=score(observation,baseline)
                    (a.out/'evaluation.json').write_text(json.dumps({'baseline':baseline,'observation':observation,**result},indent=2)+'\n')
                    emit({'event':'independent_evaluation',**result});break
                else:raise ValueError('unsupported command')
            except (ValueError,KeyError,TypeError,Expired) as e:emit({'event':'rejected','reason':str(e)})
    finally:
        if engine:engine.close()
        if backend:
            try:backend.close()
            finally:(a.out/'owner-events.json').write_text(json.dumps(backend.owner.records,indent=2)+'\n')
        if s:
            s.close();(a.out/'cleanup.json').write_text(json.dumps({'all_owned_processes_exited':all(p.poll() is not None for p in s.procs),'save_unchanged':sha(SAVE)==SAVE_SHA})+'\n');shutil.rmtree(s.tmp)

if __name__=='__main__':main()
