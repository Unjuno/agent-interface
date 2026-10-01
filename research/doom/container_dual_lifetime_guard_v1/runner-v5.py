from __future__ import annotations
import json, queue, subprocess, sys, threading, time, shutil, statistics
from pathlib import Path

ROOT=Path('/mnt/data/runtime-preview-extracted')
DOOM=ROOT/'research/doom'
FIXTURE=DOOM/'fixtures/map01-threat-contact-v2/fixture.json'
PYTHON=Path('/mnt/data/ai-exp-venv/bin/python')
PAIR_ORDER=(("DEADLINE_ONLY","STRICT_HEALTH_GUARD"),)
SEEDS=(993303,)
WAIT_MS=4500

class S:
    def __init__(self, out:Path, seed:int):
        cmd=[str(PYTHON),str(DOOM/'session_map01_v13.py'),'--out',str(out),'--seed',str(seed),'--timeout-seconds','60','--skill','1','--load-fixture-manifest',str(FIXTURE)]
        self.p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1,
            env={**__import__('os').environ,'PYTHONPATH':f"{ROOT/'research/doom'}:{ROOT/'research/live_control'}"})
        self.q=queue.Queue();self.events=[];self.latest_exact=None;self.typed={}
        threading.Thread(target=self._read,daemon=True).start()
    def _read(self):
        for line in self.p.stdout:
            r=json.loads(line);self.events.append(r)
            if r.get('event')=='observation': self.latest_exact=r
            if r.get('event')=='typed_observation' and type(r.get('sequence')) is int:self.typed[r['sequence']]=r
            self.q.put(r)
    def send(self,r):
        self.p.stdin.write(json.dumps(r,separators=(',',':'))+'\n');self.p.stdin.flush()
    def wait(self,pred,timeout=20):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            try:r=self.q.get(timeout=min(.1,max(.01,end-time.monotonic())))
            except queue.Empty:
                if self.p.poll() is not None: raise RuntimeError(self.p.stderr.read())
                continue
            if pred(r):return r
        raise TimeoutError('event timeout')
    def clock(self):
        self.send({'op':'clock'});r=self.wait(lambda x:x.get('event')=='clock');return int(r['runtime_ns'])
    def stop(self):
        if self.p.poll() is None:
            self.p.terminate()
            try:self.p.wait(3)
            except subprocess.TimeoutExpired:self.p.kill();self.p.wait()

def submit(s:S, id:str, steps:list[dict], valid_until:int):
    seq=s.latest_exact['sequence']
    s.send({'op':'submit','id':id,'expected_sequence':seq,'valid_until_ns':valid_until,'steps':steps})
    r=s.wait(lambda x:x.get('event') in {'accepted','rejected'},10)
    if r.get('event')!='accepted' or r.get('id')!=id:raise RuntimeError(f'rejected {r}')
    return r

def health(r):
    h=r.get('signals',{}).get('health',{})
    return h.get('value') if h.get('status')=='observed' and type(h.get('value')) is int else None

def source_guard(s:S):
    ex=s.latest_exact;seq=ex['sequence'];t=s.typed.get(seq)
    if t is None:t=s.wait(lambda r:r.get('event')=='typed_observation' and r.get('sequence')==seq,5)
    h=health(t)
    if h is None:raise RuntimeError('source health missing')
    return ex,t,h

def verified_empty_for_id(events,id):
    rel=[r for r in events if r.get('event')=='input_released' and r.get('id')==id and r.get('owner_release',{}).get('verified') is True]
    if rel:return int(rel[0]['owner_release']['verified_ns']),rel[0]['owner_release'].get('reason')
    term=[r for r in events if r.get('event')=='terminal' and r.get('id')==id and r.get('release',{}).get('verified') is True]
    if term:return int(term[0]['release']['verified_ns']),term[0]['release'].get('reason')
    return None,None

def run_arm(root:Path,pair:int,seed:int,arm:str):
    out=root/f'pair-{pair:02d}'/arm.lower()/'runtime';out.parent.mkdir(parents=True,exist_ok=False)
    s=S(out,seed);rid=f'p{pair}-{arm.lower()}-recovery';guard={}
    try:
        s.wait(lambda r:r.get('event')=='ready',25);s.wait(lambda r:r.get('event')=='observation',15)
        ex,t,h0=source_guard(s)
        if h0 != 97:
            raise RuntimeError(f'frozen source health mismatch: {h0}')
        planner_start=s.clock();wall_end=time.monotonic()+WAIT_MS/1000
        submit(s,rid,[{'op':'hold','keys':['Up','space'],'duration_ms':1000},{'op':'hold','keys':['space'],'duration_ms':5000}],planner_start+WAIT_MS*1_000_000)
        terminal=None
        while time.monotonic()<wall_end:
            try:r=s.q.get(timeout=min(.02,max(.001,wall_end-time.monotonic())))
            except queue.Empty:continue
            if r.get('event')=='terminal' and r.get('id')==rid:terminal=r
            if arm=='STRICT_HEALTH_GUARD' and not guard and r.get('event')=='typed_observation' and type(r.get('sequence')) is int and r['sequence']>ex['sequence']:
                hv=health(r)
                if hv is not None and hv<h0:
                    guard={'sequence':r['sequence'],'health':hv,'capture_ns':r.get('capture_ns'),'typed_emit_ns':r.get('emit_ns')}
                    s.send({'op':'cancel','id':rid})
        planner_end=s.clock()
        if terminal is None:
            # expiry may publish just after the nominal planner boundary
            try:terminal=s.wait(lambda r:r.get('event')=='terminal' and r.get('id')==rid,5)
            except TimeoutError:
                s.send({'op':'cancel','id':rid});terminal=s.wait(lambda r:r.get('event')=='terminal' and r.get('id')==rid,5)
        s.send({'op':'finish'});s.wait(lambda r:r.get('event')=='post_control_score',10);s.p.wait(timeout=15)
        ve,reason=verified_empty_for_id(s.events,rid)
        cancel=[r for r in s.events if r.get('event')=='cancel_requested' and r.get('id')==rid]
        score=json.loads((out/'score.json').read_text());summary=json.loads((out/'scorer-summary.json').read_text())
        sp=out/'scorer-events.jsonl';scorer=[json.loads(x) for x in sp.read_text().splitlines() if x.strip()] if sp.exists() else []
        audit_out=out.parent/'terminal-score-audit.json'
        cp=subprocess.run([str(PYTHON),str(DOOM/'audit_map01_terminal_score_agreement_v1.py'),str(out),'--out',str(audit_out)],capture_output=True,text=True)
        result={'pair':pair,'seed':seed,'arm':arm,'source_sequence':ex['sequence'],'source_health':h0,'planner_start_ns':planner_start,'planner_end_ns':planner_end,
          'planner_window_ms':(planner_end-planner_start)/1e6,'valid_until_ns':planner_start+WAIT_MS*1_000_000,
          'guard':guard or None,'cancel_requested_ns':cancel[0].get('requested_ns') if cancel else None,'verified_empty_ns':ve,'release_reason':reason,
          'authority_end_after_planner_start_ms':(ve-planner_start)/1e6 if ve else None,'terminal_status':terminal.get('status') if terminal else None,
          'score':score,'scorer_events':scorer,'scorer_summary':summary,'terminal_audit_exit':cp.returncode,'terminal_audit_stdout':cp.stdout.strip(),'terminal_audit_stderr':cp.stderr.strip()}
        (out.parent/'arm-summary.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        return result
    finally:s.stop()

def classify(arms):
    pairs=[];hard=[];lower_kill=0;exposed=0;all_earlier=True;worse_death=False;earlier_negative=False
    by={}
    for a in arms:by.setdefault(a['pair'],{})[a['arm']]=a
    for i in sorted(by):
        d=by[i]['DEADLINE_ONLY'];g=by[i]['STRICT_HEALTH_GUARD']
        if not d['verified_empty_ns'] or not g['verified_empty_ns']:hard.append(f'p{i}:release')
        if d['terminal_audit_exit']!=0 or g['terminal_audit_exit']!=0:hard.append(f'p{i}:terminal_audit')
        for a in (d,g):
            if a['scorer_summary'].get('scheduler',{}).get('missed_sample_periods')!=0:hard.append(f"p{i}:{a['arm']}:missed")
        exp=g['guard'] is not None; exposed+=int(exp)
        earlier=exp and g['authority_end_after_planner_start_ms']<d['authority_end_after_planner_start_ms'];all_earlier=all_earlier and (earlier if exp else True)
        dk=d['score'].get('kill_count',0);gk=g['score'].get('kill_count',0);dd=d['score'].get('death_count',0);gd=g['score'].get('death_count',0)
        lower_kill+=int(gk<dk);worse_death=worse_death or gd>dd
        dn=[e for e in d['scorer_events'] if e.get('polarity')=='negative'];gn=[e for e in g['scorer_events'] if e.get('polarity')=='negative']
        if gn:
            gt=min(e['observed_ns']-g['planner_start_ns'] for e in gn);dt=min((e['observed_ns']-d['planner_start_ns'] for e in dn),default=10**30);earlier_negative=earlier_negative or gt<dt
        pairs.append({'pair':i,'guard_exposed':exp,'guard_earlier_release':earlier,'deadline_kills':dk,'guard_kills':gk,'deadline_deaths':dd,'guard_deaths':gd,
          'deadline_positive_events':[e.get('kind') for e in d['scorer_events'] if e.get('useful') is True],
          'guard_positive_events':[e.get('kind') for e in g['scorer_events'] if e.get('useful') is True],
          'deadline_authority_end_ms':d['authority_end_after_planner_start_ms'],'guard_authority_end_ms':g['authority_end_after_planner_start_ms']})
    if hard:decision='FAIL'
    elif lower_kill==1 or worse_death or earlier_negative:decision='REJECT_SINGLE_PAIR_STRICT_GUARD'
    elif exposed==1 and all_earlier and lower_kill==0 and not worse_death and not earlier_negative:decision='PASS_SINGLE_PAIR_CANDIDATE'
    else:decision='HOLD'
    return {'schema':'container-map01-dual-lifetime-guard-tradeoff-v1-result','decision':decision,'hard_failures':hard,'guard_exposed_pairs':exposed,'lower_kill_pairs':lower_kill,'pairs':pairs}

def main():
    root=Path(sys.argv[1]);
    if root.exists():raise SystemExit('output exists')
    root.mkdir(parents=True)
    arms=[]
    for i,(seed,order) in enumerate(zip(SEEDS,PAIR_ORDER),1):
        for arm in order:arms.append(run_arm(root,i,seed,arm))
    res=classify(arms);(root/'result.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');print(json.dumps(res,indent=2))
if __name__=='__main__':main()
