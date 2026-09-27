"""Development probe: one bounded hold through real session_map01_v13/X11/InputOwner."""
from __future__ import annotations
import argparse,json,queue,subprocess,threading,time
from pathlib import Path

def run_once(repo:Path, python:str, fixture:Path, out:Path, keys:list[str], cutoff_ms:int, seed:int):
    here=repo/'research/doom'; runtime=out/'runtime'; out.mkdir(parents=True,exist_ok=False)
    p=subprocess.Popen([python,str(here/'session_map01_v13.py'),'--out',str(runtime),'--seed',str(seed),'--timeout-seconds','60','--skill','1','--load-fixture-manifest',str(fixture)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1,cwd=here)
    q=queue.Queue(); latest=None
    def reader():
        for line in p.stdout:
            try:q.put(json.loads(line))
            except json.JSONDecodeError:pass
        q.put(None)
    threading.Thread(target=reader,daemon=True).start()
    def take(timeout=20):
        nonlocal latest
        row=q.get(timeout=timeout)
        if row is None: raise RuntimeError(p.stderr.read())
        if row.get('event')=='observation': latest=row
        return row
    def wait(pred,timeout=20):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            row=take(max(.01,end-time.monotonic()))
            if pred(row):return row
        raise TimeoutError('event predicate')
    def send(row):p.stdin.write(json.dumps(row)+'\n');p.stdin.flush()
    try:
        wait(lambda r:r.get('event')=='ready');wait(lambda r:r.get('event')=='observation' and r.get('id')=='initial')
        send({'op':'clock'});clock=wait(lambda r:r.get('event')=='clock')
        ident=f"probe-{cutoff_ms}-{'-'.join(keys)}"
        send({'op':'submit','id':ident,'expected_sequence':latest['sequence'],'valid_until_ns':clock['runtime_ns']+cutoff_ms*1_000_000,'steps':[{'op':'hold','keys':keys,'duration_ms':5000}]})
        terminal=wait(lambda r:r.get('event')=='terminal' and r.get('id')==ident,12)
        send({'op':'finish'});score=wait(lambda r:r.get('event')=='post_control_score',10)
        p.stdin.close();p.wait(timeout=10)
        events=[json.loads(x) for x in (runtime/'events.jsonl').read_text().splitlines() if x.strip()]
        accepted=next(r for r in events if r.get('event')=='accepted' and r.get('id')==ident)
        admissions=[r for r in events if r.get('event')=='input_admission' and r.get('id') in (None,ident)]
        cause=(terminal.get('interruption') or {}).get('record') or terminal.get('release') or {}
        start=min((r['admitted_ns'] for r in admissions if r.get('key') in keys),default=None);verified=cause.get('verified_ns')
        health=[];ammo=[]
        for r in events:
            if r.get('event')!='typed_observation':continue
            sig=r.get('signals') or {};h=sig.get('health') or {};a=sig.get('ammo') or {}
            if h.get('status')=='observed':health.append(h.get('value'))
            if a.get('status')=='observed':ammo.append(a.get('value'))
        return {'cutoff_ms':cutoff_ms,'keys':keys,'seed':seed,'status':terminal.get('status'),'kill_count':score.get('kill_count'),'death_count':score.get('death_count'),'map_exit':score.get('map_exit'),'release_verified':cause.get('verified'),'occupancy_upper_ms':((verified-start)/1e6 if verified and start else None),'deadline_to_empty_ms':((verified-accepted['valid_until_ns'])/1e6 if verified else None),'health_first':health[0] if health else None,'health_last':health[-1] if health else None,'health_min':min(health) if health else None,'ammo_first':ammo[0] if ammo else None,'ammo_last':ammo[-1] if ammo else None}
    finally:
        if p.poll() is None:p.kill();p.wait()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--python',required=True);ap.add_argument('--fixture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--keys',nargs='+',required=True);ap.add_argument('--cutoff-ms',type=int,required=True);ap.add_argument('--seed',type=int,default=996001);ap.add_argument('--reps',type=int,default=1);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False);rows=[]
    for rep in range(1,a.reps+1):
        row=run_once(a.repo,a.python,a.fixture,a.out/f'r{rep}',a.keys,a.cutoff_ms,a.seed);row['rep']=rep;rows.append(row);print(json.dumps(row),flush=True)
    (a.out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()
