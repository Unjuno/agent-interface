"""Finite local X11 experiment; immutable v13 runtime; no engine action API."""
from __future__ import annotations
import argparse, hashlib, json, os, queue, subprocess, sys, threading, time, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUNTIME = ROOT / 'runtime'
FIXTURE = RUNTIME / 'research/doom/fixtures/map01-threat-contact-v2/fixture.json'
POLICIES = {
    'attack': [{'op':'hold','keys':['space'],'duration_ms':5000}],
    'back_left': [{'op':'hold','keys':['s','a','space'],'duration_ms':5000}],
    'back_right': [{'op':'hold','keys':['s','d','space'],'duration_ms':5000}],
    'back_sweep': [{'op':'hold','keys':['s','a','space'],'duration_ms':1400},
                   {'op':'hold','keys':['s','d','space'],'duration_ms':5000}],
}

def dump(path: Path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')

def rows(path: Path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()] if path.exists() else []

def sha(path: Path):return hashlib.sha256(path.read_bytes()).hexdigest()

class Session:
    def __init__(self,out:Path,fixture:Path,seed:int,save:Path|None=None):
        out.mkdir(parents=True,exist_ok=False)
        self.out=out;self.q=queue.Queue();self.latest=None;self.received=[]
        self.stderr=(out/'stderr.txt').open('w')
        cmd=[sys.executable,str(RUNTIME/'research/doom/session_map01_v13.py'),
             '--out',str(out/'runtime'),'--seed',str(seed),'--timeout-seconds','60',
             '--skill','1','--load-fixture-manifest',str(fixture)]
        if save:cmd+=['--fixture-out',str(save)]
        dump(out/'launch.json',{'command':cmd,'fixture_sha256':sha(fixture)})
        auth=ROOT/'bootstrap.Xauthority';auth.touch(exist_ok=True)
        env=os.environ.copy();env['XAUTHORITY']=str(auth)
        self.p=subprocess.Popen(cmd,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.stderr,
             text=True,bufsize=1,cwd=RUNTIME/'research/doom',start_new_session=True)
        def read():
            for line in self.p.stdout:
                try:row=json.loads(line)
                except json.JSONDecodeError:
                    self.q.put({'event':'unparsed','line':line});continue
                self.q.put(row)
            self.q.put(None)
        self.thread=threading.Thread(target=read,daemon=True);self.thread.start()
    def wait(self,predicate,timeout=25):
        deadline=time.monotonic()+timeout
        while True:
            r=self.q.get(timeout=max(.001,deadline-time.monotonic()))
            if r is None:raise RuntimeError(f'session exited rc={self.p.poll()}: '+(self.out/'stderr.txt').read_text()[-2000:])
            self.received.append(r)
            if r.get('event')=='observation':self.latest=r
            if predicate(r):return r
            if time.monotonic()>deadline:raise TimeoutError('event predicate')
    def ready(self):
        self.wait(lambda r:r.get('event')=='ready')
        return self.wait(lambda r:r.get('event')=='observation' and r.get('id')=='initial')
    def send(self,row):
        self.p.stdin.write(json.dumps(row)+'\n');self.p.stdin.flush()
    def submit(self,steps,identifier,cutoff_ms):
        self.send({'op':'clock'});clock=self.wait(lambda r:r.get('event')=='clock')
        self.send({'op':'submit','id':identifier,'expected_sequence':self.latest['sequence'],
                   'valid_until_ns':clock['runtime_ns']+cutoff_ms*1_000_000,'steps':steps})
        return self.wait(lambda r:r.get('event')=='terminal' and r.get('id')==identifier,15)
    def finish(self):
        self.send({'op':'finish'})
        score=self.wait(lambda r:r.get('event')=='post_control_score')
        self.p.stdin.close();self.p.wait(timeout=15);return score
    def close(self):
        if self.p.poll() is None:
            try:
                self.send({'op':'finish'});self.p.stdin.close();self.p.wait(timeout=5)
            except Exception:
                import signal
                os.killpg(self.p.pid,signal.SIGTERM)
                try:self.p.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(self.p.pid,signal.SIGKILL);self.p.wait()
        self.stderr.close();dump(self.out/'received.json',self.received)

def analyze(out:Path,identifier:str):
    rt=out/'runtime';events=rows(rt/'events.jsonl');samples=rows(rt/'scorer-samples.jsonl')
    score=json.loads((rt/'score.json').read_text());summary=json.loads((rt/'scorer-summary.json').read_text())
    accepted=next(r for r in events if r.get('event')=='accepted' and r['id']==identifier)
    terminal=next(r for r in events if r.get('event')=='terminal' and r['id']==identifier)
    cause=(terminal.get('interruption') or {}).get('record') or terminal.get('release') or {}
    admissions=[r for r in events if r.get('event')=='input_admission']
    first_down=min((r['admitted_ns'] for r in admissions),default=None)
    last=next(r['payload'] for r in reversed(samples) if r.get('direct_final_sample') is True)
    eq=all(type(last[k]) is type(score[k]) and last[k]==score[k] for k in ('map_exit','episode_finished','player_dead','death_count','kill_count'))
    runtime_sources=json.loads((rt/'sources.json').read_text())
    source_ok=all(sha(RUNTIME/'research'/n)==h for n,h in runtime_sources.items())
    signals={k:[] for k in ['health','ammo']}
    for r in events:
        if r.get('event')!='typed_observation':continue
        for k in signals:
            v=(r.get('signals') or {}).get(k) or {}
            if v.get('status')=='observed' and type(v.get('value')) is int:signals[k].append(v['value'])
    scored=rows(rt/'scorer-events.jsonl')
    useful=[r['observed_ns'] for r in scored if r.get('useful') is True]
    deadline=accepted['valid_until_ns'];verified=cause.get('verified_ns')
    # An empty release certifies the latest possible end, not exact interrupted occupancy.
    gates={'terminal_agreement':eq,'source_hashes':source_ok,
        'delivery_exact':(rt/'events.jsonl').read_bytes()==(rt/'delivered.jsonl').read_bytes(),
        'release_empty':cause.get('verified') is True and cause.get('keys_down')==[] and cause.get('buttons_down',[])==[],
        'scorer_not_controller_visible':not any(str(r.get('schema','')).startswith('independent-progress-') for r in events)}
    result={'id':identifier,'score':{k:score[k] for k in ('kill_count','death_count','map_exit','player_dead')},
        'terminal_status':terminal['status'],'admitted_keys':[r['key'] for r in admissions],
        'accepted_ns':accepted['accepted_ns'],'deadline_ns':deadline,'first_admitted_ns':first_down,
        'verified_empty_ns':verified,'first_useful_observed_ns':min(useful,default=None),
        'useful_observed_before_deadline':any(t<=deadline for t in useful),
        'scorer_kill_values':sorted({s['payload']['kill_count'] for s in samples}),
        'scorer_sample_count':len(samples),'missed_periods':summary['scheduler']['missed_sample_periods'],
        'deadline_to_empty_ms':(verified-deadline)/1e6 if verified else None,
        'first_admission_to_empty_upper_ms':(verified-first_down)/1e6 if verified and first_down else None,
        'health':{'first':signals['health'][0],'last':signals['health'][-1],'min':min(signals['health'])} if signals['health'] else None,
        'ammo':{'first':signals['ammo'][0],'last':signals['ammo'][-1]} if signals['ammo'] else None,
        'gates':gates,'pass_hard_gates':all(gates.values())}
    dump(out/'analysis.json',result);return result

def run_case(spec,out):
    s=Session(out,Path(spec['fixture']),spec['seed'])
    try:
        s.ready();s.submit(POLICIES[spec['policy']],spec['id'],spec['cutoff_ms']);s.finish()
        result=analyze(out,spec['id']);result.update({k:spec[k] for k in ('state','policy','rep','seed')})
        dump(out/'analysis.json',result)
        if not result['pass_hard_gates']:raise RuntimeError('hard gate failed; preserve and stop')
        return result
    except Exception as e:
        dump(out/'failure.json',{'error':repr(e),'traceback':traceback.format_exc()});raise
    finally:s.close()

def make_fixture(state,key):
    out=ROOT/'evidence/setup'/state;save=out/'save.png'
    s=Session(out,FIXTURE,997200,save=save)
    try:
        s.ready()
        term=s.submit([{'op':'hold','keys':[key],'duration_ms':650},
                       {'op':'coast','duration_ms':350,'sample_ms':100}],f'setup-{state}',10000)
        if term['status']!='completed' or not term['release']['verified']:raise RuntimeError('setup did not complete')
        s.send({'op':'save_fixture'});s.wait(lambda r:r.get('event')=='fixture_saved')
        s.p.stdin.close();s.p.wait(timeout=15)
        return save.with_suffix('.json')
    finally:s.close()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--setup',choices=['left','right']);ap.add_argument('--plan',type=Path);ap.add_argument('--block',type=int);ap.add_argument('--preflight',action='store_true');a=ap.parse_args()
    if a.setup:print(make_fixture(a.setup,'a' if a.setup=='left' else 'd'));return
    if a.preflight:
        spec={'id':'preflight','fixture':str(FIXTURE),'seed':997199,'policy':'attack','cutoff_ms':250,'state':'original','rep':0}
        print(json.dumps(run_case(spec,ROOT/'evidence/preflight02')));return
    plan=json.loads(a.plan.read_text())
    for n,h in plan['source_sha256'].items():
        if sha(HERE/n)!=h:raise RuntimeError('source changed after freeze '+n)
    specs=[s for s in plan['cases'] if s['rep']==a.block]
    if not specs:raise ValueError('empty block')
    for spec in specs:
        if sha(Path(spec['fixture']))!=spec['fixture_sha256']:raise RuntimeError('fixture changed')
        result=run_case(spec,ROOT/'evidence'/plan['allocation']/spec['id'])
        print(json.dumps(result),flush=True)
if __name__=='__main__':main()
