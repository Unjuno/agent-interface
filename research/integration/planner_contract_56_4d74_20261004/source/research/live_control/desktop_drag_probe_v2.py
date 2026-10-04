"""Paired scripted drag-resolution study; shared backend, real saved SVG oracle."""
import argparse,hashlib,json,shutil,time
from pathlib import Path
from session_v9 import Backend,suite
from executor_v3 import Executor
HERE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    (a.out/'plan.json').write_text(json.dumps({'scope':'scripted drag-resolution comparison, not assistant timing','order':['dense','coarse'],'requested_dx_pixels':24,'duration_ms':200,'seed':991003,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
    for mode in ['dense','coarse']:
        out=a.out/mode;out.mkdir();s=suite.Session();backend=None;engine=None;events=[];output=None
        def emit(r):
            events.append(r)
            with (out/'events.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
        def run(name,steps):
            engine.submit(name,steps,backend.sequence,time.perf_counter_ns()+5_000_000_000)
            until=time.monotonic()+7
            while engine.active is not None and time.monotonic()<until:time.sleep(.01)
            assert engine.active is None
            r=next(e for e in reversed(events) if e['event']=='terminal');assert r['status']=='completed' and r['release']['verified'],r
        try:
            goal,output,_=suite.prepare(s,'inkscape',991003,'unused')
            backend=Backend(s,out,emit);engine=Executor(backend,emit);backend.snapshot('initial',0)
            before=suite.red_bbox(backend.decoder.frame);x=(before[0]+before[2])//2;y=(before[1]+before[3])//2
            run('select',[{'op':'pointer_click','x':x,'y':y},{'op':'settle','quiet_ms':100,'timeout_ms':1200}])
            offsets=[0,12,24] if mode=='coarse' else list(range(25))
            run('drag',[{'op':'pointer_drag','points':[{'x':x+i,'y':y} for i in offsets],'duration_ms':200}])
            run('save',[{'op':'chord','modifier':'Control_L','key':'s'},{'op':'settle','quiet_ms':100,'timeout_ms':1200}])
            after=suite.red_bbox(backend.decoder.frame);result=suite.evaluate('inkscape',output,goal)
            observed_dx=after[0]-before[0]
            row={'mode':mode,'requested_dx_pixels':24,'observed_dx_pixels':observed_dx,'within_one_pixel':abs(observed_dx-24)<=1,'before_bbox':before,'after_bbox':after,'legacy_evaluation':result}
            (out/'result.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row),flush=True)
        finally:
            if engine:engine.close()
            if backend:
                backend.close();(out/'owner-events.json').write_text(json.dumps(backend.owner.records,indent=2)+'\n')
            if output and output.exists():shutil.copy2(output,out/'shape.svg')
            s.close();(out/'cleanup.json').write_text(json.dumps({'all_owned_processes_exited':all(p.poll() is not None for p in s.procs)})+'\n');shutil.rmtree(s.tmp)

if __name__=='__main__':main()
