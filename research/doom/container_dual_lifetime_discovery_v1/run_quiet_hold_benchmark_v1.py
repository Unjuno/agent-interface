from __future__ import annotations
import json,pathlib,shutil,subprocess,time,statistics,os,sys
ROOT=pathlib.Path('/tmp/lab/src');DOOM=ROOT/'research/doom';LIVE=ROOT/'research/live_control'
PYTHON='/tmp/lab/venv/bin/python';DUAL=pathlib.Path('/tmp/lab/dual_lifetime')
FIXTURE=DOOM/'fixtures/map01-threat-contact-v2/fixture.json';OUTROOT=DUAL/'quiet-runs';AUTHORITY_MS=600

def send(p,o):p.stdin.write(json.dumps(o,separators=(',',':'))+'\n');p.stdin.flush()
def read(p,deadline):
    while time.monotonic()<deadline:
        line=p.stdout.readline()
        if not line:
            if p.poll() is not None:return None
            continue
        try:return json.loads(line)
        except json.JSONDecodeError:continue
    return None

def direct_final(out):
    p=out/'scorer-samples.jsonl'
    if not p.exists():return None
    rows=[]
    for line in p.read_text().splitlines():
        try:rows.append(json.loads(line))
        except:pass
    return next((x['payload'] for x in reversed(rows) if x.get('direct_final_sample') is True),None)
def score_ok(out):
    s=json.loads((out/'score.json').read_text());d=direct_final(out)
    return d is not None and all(s[k]==d[k] for k in ('map_exit','episode_finished','player_dead','death_count','kill_count'))

def run_one(seed,arm,label):
    out=OUTROOT/label;shutil.rmtree(out,ignore_errors=True)
    script=DUAL/('session_map01_dual_lifetime_v1.py' if arm=='capture_hold' else 'session_map01_dual_quiet_v1.py')
    env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join([str(DUAL),str(DOOM),str(LIVE),env.get('PYTHONPATH','')])
    p=subprocess.Popen([PYTHON,str(script),'--out',str(out),'--seed',str(seed),'--timeout-seconds','60','--skill','1','--load-fixture-manifest',str(FIXTURE)],cwd=DOOM,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    events=[];last_seq=None;clock=None;terminal=None;id=f'{label}-cmp'
    try:
        deadline=time.monotonic()+20
        while time.monotonic()<deadline and last_seq is None:
            r=read(p,deadline)
            if r is None:break
            events.append(r)
            if r.get('event')=='observation':last_seq=r['sequence']
        if last_seq is None:raise RuntimeError('initial observation missing')
        send(p,{'op':'clock'});deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            r=read(p,deadline)
            if r is None:break
            events.append(r)
            if r.get('event')=='observation':last_seq=r['sequence']
            if r.get('event')=='clock':clock=r;break
        if clock is None:raise RuntimeError('clock missing')
        valid=int(clock['runtime_ns'])+AUTHORITY_MS*1_000_000
        send(p,{'op':'submit','id':id,'expected_sequence':last_seq,'valid_until_ns':valid,'steps':[{'op':'hold','keys':['Shift_L'],'duration_ms':2000}]})
        deadline=time.monotonic()+8
        obs=[]
        while time.monotonic()<deadline:
            r=read(p,deadline)
            if r is None:break
            events.append(r)
            if r.get('event')=='observation' and r.get('id')==id:obs.append(r)
            if r.get('event')=='terminal' and r.get('id')==id:terminal=r;break
        if terminal is None:raise RuntimeError('terminal missing')
        send(p,{'op':'finish'})
        try:p.wait(timeout=8)
        except subprocess.TimeoutExpired:p.kill();p.wait()
        (out/'harness-stderr.txt').write_text(p.stderr.read())
        owner=json.loads((out/'owner-events.json').read_text());rel=next((x for x in owner if x.get('event')=='owner_release' and x.get('reason')=='expired'),None)
        if rel is None:raise RuntimeError('expiry release missing')
        v=rel['verified_ns'];post=terminal.get('post_authority_observation') or {};seq=post.get('sequence')
        fresh=next((o for o in obs if o.get('sequence')==seq and isinstance(o.get('capture_ns'),int) and o['capture_ns']>=v),None)
        if fresh is None:raise RuntimeError('post-authority fresh observation missing')
        after=[e for e in events if e.get('event') in ('input_admission','pointer_admission') and (e.get('admitted_ns') or 0)>v]
        return {'seed':seed,'arm':arm,'label':label,'terminal_status':terminal.get('status'),'steps_completed':terminal.get('steps_completed'),
                'release_verified':rel.get('verified'),'keys_down':rel.get('keys_down'),'buttons_down':rel.get('buttons_down'),
                'deadline_to_empty_ms':(v-valid)/1e6,'release_to_fresh_capture_ms':(fresh['capture_ns']-v)/1e6,
                'post_release_input_admissions':len(after),'post_authority':post,'score_agreement':score_ok(out)}
    finally:
        if p.poll() is None:
            try:send(p,{'op':'finish'})
            except:pass
            try:p.wait(timeout=2)
            except:p.kill();p.wait()

def aggregate(rs):
    a=[r for r in rs if r['arm']=='capture_hold'];q=[r for r in rs if r['arm']=='quiet_hold']
    hard=all(r['release_verified'] is True and r['keys_down']==[] and r['buttons_down']==[] and r['post_release_input_admissions']==0 and r['terminal_status']=='authority_ended' and r['score_agreement'] and r['post_authority'].get('captures')==1 and r['post_authority'].get('within_lifecycle_deadline') is True for r in rs)
    pairs=[]
    for seed in (993200,993201,993202):
        x=next(r for r in a if r['seed']==seed);y=next(r for r in q if r['seed']==seed)
        pairs.append({'seed':seed,'capture_hold_ms':x['release_to_fresh_capture_ms'],'quiet_hold_ms':y['release_to_fresh_capture_ms'],'improvement_ms':x['release_to_fresh_capture_ms']-y['release_to_fresh_capture_ms']})
    sm={'capture_hold_release_to_fresh_median_ms':statistics.median(r['release_to_fresh_capture_ms'] for r in a),
        'quiet_hold_release_to_fresh_median_ms':statistics.median(r['release_to_fresh_capture_ms'] for r in q),
        'paired_improvement_median_ms':statistics.median(p['improvement_ms'] for p in pairs),
        'capture_hold_deadline_to_empty_median_ms':statistics.median(r['deadline_to_empty_ms'] for r in a),
        'quiet_hold_deadline_to_empty_median_ms':statistics.median(r['deadline_to_empty_ms'] for r in q)}
    sm['release_regression_ms']=sm['quiet_hold_deadline_to_empty_median_ms']-sm['capture_hold_deadline_to_empty_median_ms']
    dec='REJECT' if not hard else ('PROMOTE_QUIET_HOLD_MECHANISM' if sm['paired_improvement_median_ms']>=10 and sm['release_regression_ms']<=2 else 'HOLD')
    return {'schema':'dual-lifetime-quiet-hold-development-result-v1','results':rs,'pairs':pairs,'hard_gates_pass':hard,'summary':sm,'decision':dec}

def main():
    OUTROOT.mkdir(parents=True,exist_ok=True)
    sched=[(993200,'capture_hold'),(993200,'quiet_hold'),(993201,'quiet_hold'),(993201,'capture_hold'),(993202,'capture_hold'),(993202,'quiet_hold')]
    rs=[]
    for i,(seed,arm) in enumerate(sched,1):
        r=run_one(seed,arm,f'{i:02d}-{seed}-{arm}');rs.append(r);print(json.dumps({k:r[k] for k in ('label','arm','deadline_to_empty_ms','release_to_fresh_capture_ms','post_release_input_admissions','score_agreement')},sort_keys=True),flush=True)
    agg=aggregate(rs);(DUAL/'quiet-result.json').write_text(json.dumps(agg,indent=2)+'\n');print(json.dumps({'decision':agg['decision'],**agg['summary'],'hard_gates_pass':agg['hard_gates_pass']},sort_keys=True))
if __name__=='__main__':main()
