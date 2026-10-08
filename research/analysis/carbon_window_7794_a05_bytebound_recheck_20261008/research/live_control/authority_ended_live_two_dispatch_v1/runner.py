from __future__ import annotations
import json,os,pathlib,shutil,subprocess,time,sys
HERE=pathlib.Path(__file__).resolve().parent
DUAL=pathlib.Path('/tmp/lab/dual_lifetime'); ROOT=pathlib.Path('/tmp/lab/src'); DOOM=ROOT/'research/doom'; LIVE=ROOT/'research/live_control'
PYTHON='/tmp/lab/venv/bin/python'; SESSION=DUAL/'session_map01_dual_quiet_v1.py'; FIXTURE=DOOM/'fixtures/map01-threat-contact-v2/fixture.json'
sys.path.insert(0,str(HERE)); from two_dispatch_gate_v1 import open_replan_token,current_revalidation,consume_for_execute

def send(p,o): p.stdin.write(json.dumps(o,separators=(',',':'))+'\n');p.stdin.flush()
def next_json(p):
    while True:
        line=p.stdout.readline()
        if not line:
            if p.poll() is not None:return None
            continue
        try:return json.loads(line)
        except json.JSONDecodeError:continue

def start(out,seed):
    shutil.rmtree(out,ignore_errors=True)
    env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join([str(HERE),str(DUAL),str(DOOM),str(LIVE),env.get('PYTHONPATH','')])
    return subprocess.Popen([PYTHON,str(SESSION),'--out',str(out),'--seed',str(seed),'--timeout-seconds','60','--skill','1','--load-fixture-manifest',str(FIXTURE)],cwd=DOOM,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
def until(p,pred,events,limit=30):
    end=time.monotonic()+limit
    while time.monotonic()<end:
        r=next_json(p)
        if r is None:break
        events.append(r)
        if pred(r):return r
    raise RuntimeError('event timeout')
def clock(p,events):
    send(p,{'op':'clock'});return until(p,lambda r:r.get('event')=='clock',events,5)
def last_seq(events): return max(r['sequence'] for r in events if r.get('event')=='observation')
def direct_final(out):
    p=out/'scorer-samples.jsonl'
    if not p.exists(): return None
    rows=[]
    for line in p.read_text().splitlines():
        try: rows.append(json.loads(line))
        except: pass
    return next((x['payload'] for x in reversed(rows) if x.get('direct_final_sample') is True),None)
def score_ok(out):
    try: s=json.loads((out/'score.json').read_text()); d=direct_final(out)
    except: return False
    return d is not None and all(s[k]==d[k] for k in ('map_exit','episode_finished','player_dead','death_count','kill_count'))
def first_authority_receipt(term,events):
    rel=(term.get('interruption') or {}).get('record') or {}
    if rel.get('event')!='owner_release' or rel.get('reason')!='expired': raise RuntimeError('expiry interruption receipt missing')
    v=rel.get('verified_ns') or 0
    post_inputs=sum(e.get('event')=='input_admission' and (e.get('admitted_ns') or 0)>v for e in events)
    post=term.get('post_authority_observation')
    return {'terminal_status':term.get('status'),'steps_completed':term.get('steps_completed'),'release_verified':rel.get('verified'),
            'keys_down':rel.get('keys_down'),'buttons_down':rel.get('buttons_down'),'post_release_input_admissions':post_inputs,'post_authority':post}, rel

def run(out,seed,arm):
    p=start(out,seed);events=[]
    try:
        until(p,lambda r:r.get('event')=='observation',events,25)
        c=clock(p,events);seq=last_seq(events);valid=int(c['runtime_ns'])+600_000_000
        send(p,{'op':'submit','id':'first','expected_sequence':seq,'valid_until_ns':valid,'steps':[{'op':'hold','keys':['Shift_L'],'duration_ms':2000}]})
        term1=until(p,lambda r:r.get('event')=='terminal' and r.get('id')=='first',events,10)
        rec,rel=first_authority_receipt(term1,events);token=open_replan_token(rec);post_seq=token.post_sequence
        second_sent=False; second_term=None; current_seq=post_seq; gate=None; observe2_status=None; inputs_before_second=None
        if arm=='valid':
            c=clock(p,events)
            send(p,{'op':'submit','id':'observe2','expected_sequence':post_seq,'valid_until_ns':int(c['runtime_ns'])+1_000_000_000,'steps':[{'op':'observe'}]})
            obs_term=until(p,lambda r:r.get('event')=='terminal' and r.get('id')=='observe2',events,8)
            observe2_status=obs_term.get('status')
            current_seq=last_seq(events);gate=current_revalidation(token,current_seq)
            if gate!={'status':'revalidated'}:raise RuntimeError(('unexpected gate',gate,current_seq,post_seq))
            consume_for_execute(token)
            inputs_before_second=sum(e.get('event')=='input_admission' and (e.get('admitted_ns') or 0)>rel['verified_ns'] for e in events)
            c=clock(p,events)
            send(p,{'op':'submit','id':'second','expected_sequence':current_seq,'valid_until_ns':int(c['runtime_ns'])+1_000_000_000,'steps':[{'op':'hold','keys':['Shift_L'],'duration_ms':80}]});second_sent=True
            second_term=until(p,lambda r:r.get('event')=='terminal' and r.get('id')=='second',events,8)
        else:
            gate=current_revalidation(token,post_seq)
            inputs_before_second=sum(e.get('event')=='input_admission' and (e.get('admitted_ns') or 0)>rel['verified_ns'] for e in events)
        send(p,{'op':'finish'});p.wait(timeout=10)
        after_release=[e for e in events if e.get('event')=='input_admission' and (e.get('admitted_ns') or 0)>rel['verified_ns']]
        second_started=next((i for i,e in enumerate(events) if e.get('event')=='step_started' and e.get('id')=='second'),None)
        second_input=0
        if second_started is not None:
            terminal_idx=next(i for i,e in enumerate(events[second_started:],second_started) if e.get('event')=='terminal' and e.get('id')=='second')
            second_input=sum(e.get('event')=='input_admission' for e in events[second_started:terminal_idx+1])
        return {'arm':arm,'seed':seed,'first_status':term1.get('status'),'post_sequence':post_seq,'current_sequence':current_seq,'gate':gate,
                'second_sent':second_sent,'second_status':None if second_term is None else second_term.get('status'),'second_release':None if second_term is None else second_term.get('release'),
                'post_first_release_input_admissions_observed':len(after_release),'input_admissions_before_second_submit':inputs_before_second,'second_input_admissions':second_input,'observe2_status':observe2_status,'score_agreement':score_ok(out),'event_count':len(events)}
    finally:
        if p.poll() is None:
            try:send(p,{'op':'finish'})
            except:pass
            try:p.wait(timeout=3)
            except: p.kill();p.wait()
        try:(out/'harness-stderr.txt').write_text(p.stderr.read())
        except:pass
if __name__=='__main__':
    out=pathlib.Path(sys.argv[1]);seed=int(sys.argv[2]);arm=sys.argv[3];print(json.dumps(run(out,seed,arm),indent=2))
