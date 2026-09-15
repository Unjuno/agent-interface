from __future__ import annotations
import json,os,pathlib,shutil,subprocess,time,sys
HERE=pathlib.Path(__file__).resolve().parent
DUAL=pathlib.Path('/tmp/lab/dual_lifetime'); ROOT=pathlib.Path('/tmp/lab/src'); DOOM=ROOT/'research/doom'; LIVE=ROOT/'research/live_control'
PYTHON='/tmp/lab/venv/bin/python'; SESSION=DUAL/'session_map01_dual_quiet_v1.py'; FIXTURE=DOOM/'fixtures/map01-threat-contact-v2/fixture.json'
sys.path.insert(0,str(HERE))
from replan_receipt_ledger_v1 import ReplanReceiptLedger,DuplicateAuthorityEndedReceipt,current_revalidation,consume_for_execute

def send(p,o): p.stdin.write(json.dumps(o,separators=(',',':'))+'\n'); p.stdin.flush()
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
    env=os.environ.copy(); env['PYTHONPATH']=os.pathsep.join([str(HERE),str(DUAL),str(DOOM),str(LIVE),env.get('PYTHONPATH','')])
    return subprocess.Popen([PYTHON,str(SESSION),'--out',str(out),'--seed',str(seed),'--timeout-seconds','60','--skill','1','--load-fixture-manifest',str(FIXTURE)],cwd=DOOM,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
def until(p,pred,events,limit=30):
    end=time.monotonic()+limit
    while time.monotonic()<end:
        r=next_json(p)
        if r is None:break
        events.append(r)
        if pred(r):return r
    raise RuntimeError('event timeout')
def clock(p,events): send(p,{'op':'clock'}); return until(p,lambda r:r.get('event')=='clock',events,5)
def last_seq(events): return max(r['sequence'] for r in events if r.get('event')=='observation')
def direct_final(out):
    p=out/'scorer-samples.jsonl'; rows=[]
    if p.exists():
        for line in p.read_text().splitlines():
            try:rows.append(json.loads(line))
            except:pass
    return next((x['payload'] for x in reversed(rows) if x.get('direct_final_sample') is True),None)
def score_ok(out):
    try:s=json.loads((out/'score.json').read_text());d=direct_final(out)
    except:return False
    return d is not None and all(s[k]==d[k] for k in ('map_exit','episode_finished','player_dead','death_count','kill_count'))
def receipt(term,events):
    intr=term.get('interruption') or {}; rel=intr.get('record') or {}
    if rel.get('reason')!='expired' or rel.get('verified') is not True: raise RuntimeError('bad first expiry receipt')
    v=rel.get('verified_ns') or 0
    return {'terminal_status':term.get('status'),'steps_completed':term.get('steps_completed'),'release_verified':rel.get('verified'),'keys_down':rel.get('keys_down'),'buttons_down':rel.get('buttons_down'),'post_release_input_admissions':sum(e.get('event')=='input_admission' and (e.get('admitted_ns') or 0)>v for e in events),'post_authority':term.get('post_authority_observation'),'authority_end_id':intr.get('intent_token')}, rel

def run(out,seed):
    p=start(out,seed); events=[]
    try:
        until(p,lambda r:r.get('event')=='observation',events,25)
        c=clock(p,events); seq=last_seq(events); valid=int(c['runtime_ns'])+600_000_000
        send(p,{'op':'submit','id':'first','expected_sequence':seq,'valid_until_ns':valid,'steps':[{'op':'hold','keys':['Shift_L'],'duration_ms':2000}]})
        term=until(p,lambda r:r.get('event')=='terminal' and r.get('id')=='first',events,10)
        rec,rel=receipt(term,events); ledger=ReplanReceiptLedger(); token=ledger.issue(rec)
        dup_before=False; dup_before_error=None
        try:ledger.issue(dict(rec))
        except DuplicateAuthorityEndedReceipt as e: dup_before=True; dup_before_error=str(e)
        inputs_after_dup_before=sum(e.get('event')=='input_admission' and (e.get('admitted_ns') or 0)>rel['verified_ns'] for e in events)
        post_seq=token.post_sequence
        c=clock(p,events); send(p,{'op':'submit','id':'observe2','expected_sequence':post_seq,'valid_until_ns':int(c['runtime_ns'])+1_000_000_000,'steps':[{'op':'observe'}]})
        obs_term=until(p,lambda r:r.get('event')=='terminal' and r.get('id')=='observe2',events,8)
        current=last_seq(events); gate=current_revalidation(token,current)
        if gate!={'status':'revalidated'}: raise RuntimeError(('gate',gate,current,post_seq))
        consume_for_execute(token)
        inputs_before_second=sum(e.get('event')=='input_admission' and (e.get('admitted_ns') or 0)>rel['verified_ns'] for e in events)
        c=clock(p,events); send(p,{'op':'submit','id':'second','expected_sequence':current,'valid_until_ns':int(c['runtime_ns'])+1_000_000_000,'steps':[{'op':'hold','keys':['Shift_L'],'duration_ms':80}]})
        second_accept=until(p,lambda r:r.get('event')=='accepted' and r.get('id')=='second',events,5)
        second=until(p,lambda r:r.get('event')=='terminal' and r.get('id')=='second',events,8)
        dup_after=False; dup_after_error=None
        try:ledger.issue(dict(rec))
        except DuplicateAuthorityEndedReceipt as e: dup_after=True; dup_after_error=str(e)
        admissions_after_dup_after_before_finish=sum(e.get('event')=='input_admission' and (e.get('admitted_ns') or 0)>second['release']['verified_ns'] for e in events)
        send(p,{'op':'finish'}); p.wait(timeout=10)
        post_inputs=[e for e in events if e.get('event')=='input_admission' and (e.get('admitted_ns') or 0)>rel['verified_ns']]
        second_inputs=[e for e in post_inputs if (e.get('admitted_ns') or 0)>=second_accept['accepted_ns']]
        third_id_events=[e for e in events if e.get('id')=='third']
        return {'schema':'authority-ended-live-receipt-duplicate-v1-result','seed':seed,'first_status':term.get('status'),'authority_end_id':rec['authority_end_id'],'post_sequence':post_seq,'current_sequence':current,'gate':gate,'duplicate_before_rejected':dup_before,'duplicate_before_error':dup_before_error,'input_admissions_after_duplicate_before':inputs_after_dup_before,'observe2_status':obs_term.get('status'),'input_admissions_before_second_submit':inputs_before_second,'second_status':second.get('status'),'second_release':second.get('release'),'second_input_admissions':len(second_inputs),'duplicate_after_rejected':dup_after,'duplicate_after_error':dup_after_error,'input_admissions_after_duplicate_after_before_finish':admissions_after_dup_after_before_finish,'third_id_events':third_id_events,'total_post_first_release_input_admissions':len(post_inputs),'score_agreement':score_ok(out),'event_count':len(events),'ledger_issued_ids':sorted(ledger.issued_ids)}
    finally:
        if p.poll() is None:
            try:send(p,{'op':'finish'})
            except:pass
            try:p.wait(timeout=3)
            except:p.kill();p.wait()
        try:(out/'harness-stderr.txt').write_text(p.stderr.read())
        except:pass
if __name__=='__main__': print(json.dumps(run(pathlib.Path(sys.argv[1]),int(sys.argv[2])),indent=2,sort_keys=True))
