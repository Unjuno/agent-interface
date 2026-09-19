from __future__ import annotations
import copy,json,os,queue,subprocess,sys,threading,time
from pathlib import Path
ROOT=Path('/mnt/data/runtime-preview-extracted'); DOOM=ROOT/'research/doom'; LIVE=ROOT/'research/live_control'
LOCAL=Path(__file__).resolve().parent/'local'; PYTHON=Path('/mnt/data/ai-exp-venv/bin/python')
sys.path[:0]=[str(LOCAL),str(LIVE)]
from adaptive_acquisition_caller_v3 import run
from two_dispatch_gate_v1 import open_replan_token,current_revalidation,consume_for_execute
FIXTURE=DOOM/'fixtures/map01-threat-contact-v2/fixture.json'

class Session:
    def __init__(self,out:Path,seed:int):
        out.parent.mkdir(parents=True,exist_ok=True)
        env=os.environ.copy(); env['PYTHONPATH']=os.pathsep.join([str(LOCAL),str(DOOM),str(LIVE),env.get('PYTHONPATH','')])
        self.out=out; self.p=subprocess.Popen([str(PYTHON),str(LOCAL/'session_map01_dual_quiet_local.py'),'--out',str(out),'--seed',str(seed),'--timeout-seconds','60','--skill','1','--load-fixture-manifest',str(FIXTURE)],cwd=DOOM,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
        self.q=queue.Queue();self.events=[];self.latest_obs=None
        threading.Thread(target=self._reader,daemon=True).start()
    def _reader(self):
        for line in self.p.stdout:
            try:r=json.loads(line)
            except:continue
            self.events.append(r)
            if r.get('event')=='observation': self.latest_obs=r
            self.q.put(r)
    def send(self,o): self.p.stdin.write(json.dumps(o,separators=(',',':'))+'\n');self.p.stdin.flush()
    def wait(self,pred,timeout=20):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            try:r=self.q.get(timeout=min(.1,max(.01,end-time.monotonic())))
            except queue.Empty:
                if self.p.poll() is not None: raise RuntimeError('session exited: '+self.p.stderr.read())
                continue
            if pred(r):return r
        raise TimeoutError('event timeout')
    def clock(self):
        self.send({'op':'clock'});return int(self.wait(lambda r:r.get('event')=='clock',5)['runtime_ns'])
    def submit(self,id,steps,seq,valid_ms=1500):
        valid=self.clock()+valid_ms*1_000_000
        self.send({'op':'submit','id':id,'expected_sequence':seq,'valid_until_ns':valid,'steps':steps})
        a=self.wait(lambda r:r.get('event') in ('accepted','rejected') and r.get('id')==id,5)
        if a['event']!='accepted': raise RuntimeError('rejected '+repr(a))
        return a
    def finish(self):
        if self.p.poll() is None:
            try:self.send({'op':'finish'})
            except:pass
            try:self.p.wait(8)
            except subprocess.TimeoutExpired:self.p.kill();self.p.wait()
        (self.out/'harness-stderr.txt').write_text(self.p.stderr.read())

def program_terminal(s,id,timeout=10):
    obs=[];terminal=None;auth=None
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        try:
            r=s.wait(lambda x: True,min(.5,max(.01,end-time.monotonic())))
        except TimeoutError:
            continue
        if r.get('event')=='observation' and r.get('id')==id: obs.append(r)
        if r.get('event')=='authority_ended' and r.get('id')==id: auth=r
        if r.get('event')=='terminal' and r.get('id')==id:
            terminal=r;break
    if terminal is None: raise RuntimeError('terminal missing '+id)
    return terminal,obs,auth

def receipt_from(term,source_seq):
    rel=term.get('release') or {};post=term.get('post_authority_observation')
    return {'terminal_status':term.get('status'),'steps_completed':term.get('steps_completed'),
            'release_verified':rel.get('verified'),'keys_down':rel.get('keys_down',[]),'buttons_down':rel.get('buttons_down',[]),
            'post_release_input_admissions':0,
            'post_authority':post}

def caller_spec():
    return {'target':'map01-recovery','route':'reuse','coarse_origin':'caller_provided','provided_coarse':None,
            'cached_target':{'intent':'turn-right-v1'},'local_repair_on':[],'repair_on':[],'session_id':'map01-live-two-dispatch-v1'}

def run_condition(root:Path,condition:str,seed:int):
    out=root/condition.lower();s=Session(out,seed);calls=[];second={}
    try:
        s.wait(lambda r:r.get('event')=='ready',25); initial=s.wait(lambda r:r.get('event')=='observation',10)
        seq=initial['sequence'];clk=s.clock();valid=clk+600_000_000
        id1=f'{condition.lower()}-first'
        s.send({'op':'submit','id':id1,'expected_sequence':seq,'valid_until_ns':valid,'steps':[{'op':'hold','keys':['Shift_L'],'duration_ms':2000}]})
        a=s.wait(lambda r:r.get('event') in ('accepted','rejected') and r.get('id')==id1,5)
        if a['event']!='accepted':raise RuntimeError('first rejected '+repr(a))
        term1,obs1,auth=program_terminal(s,id1,8)
        receipt=receipt_from(term1,seq); token=open_replan_token(receipt)
        post_seq=receipt['post_authority']['sequence']
        post_obs=next((o for o in obs1 if o.get('sequence')==post_seq),None)
        if post_obs is None: raise RuntimeError('post observation event missing')
        if condition=='FRESH':
            idobs=f'{condition.lower()}-current-observe';s.submit(idobs,[{'op':'observe'}],post_seq,1000)
            t_obs,o_obs,_=program_terminal(s,idobs,5)
            if t_obs.get('status')!='completed':raise RuntimeError('observe not completed')
            current=max(o_obs,key=lambda o:o['sequence']);current_seq=current['sequence']
        else:
            current=post_obs;current_seq=post_seq
        def reuse(payload):calls.append('reuse_revalidate');return current_revalidation(token,current_seq)
        def final(payload):calls.append('final_revalidate');return current_revalidation(token,current_seq)
        def execute(payload):
            calls.append('execute');consume_for_execute(token);id2=f'{condition.lower()}-second'
            s.submit(id2,[{'op':'hold','keys':['Right'],'duration_ms':120}],current_seq,1000)
            t2,o2,_=program_terminal(s,id2,5);second.update(id=id2,terminal=t2,observations=o2)
            return {'status':'completed' if t2.get('status')=='completed' else 'failed'}
        def verify(payload):
            calls.append('verify_effect')
            # This gate tests authority/freshness, not semantic task success.
            return {'status':'unavailable'}
        result=run(caller_spec(),{'reuse_revalidate':reuse,'final_revalidate':final,'execute':execute,'verify_effect':verify})
        s.send({'op':'finish'});s.p.wait(timeout=10)
        owner=json.loads((out/'owner-events.json').read_text())
        right_adm=[e for e in s.events if e.get('event')=='input_admission' and e.get('key')=='Right']
        left_adm=[e for e in s.events if e.get('event')=='input_admission' and e.get('key')=='Shift_L']
        expiry=[e for e in owner if e.get('event')=='owner_release' and e.get('reason')=='expired']
        second_term=second.get('terminal') or {}
        audit_out=out/'terminal-score-audit.json'
        cp=subprocess.run([str(PYTHON),str(DOOM/'audit_map01_terminal_score_agreement_v1.py'),str(out),'--out',str(audit_out)],capture_output=True,text=True)
        score=json.loads((out/'score.json').read_text())
        resultrow={'condition':condition,'initial_sequence':seq,'post_sequence':post_seq,'current_sequence':current_seq,
                   'first_status':term1.get('status'),'first_terminal_release':term1.get('release'),'post_authority':receipt['post_authority'],
                   'caller_outcome':result['outcome'],'caller_reason':result['reason'],'calls':calls,
                   'second_id':second.get('id'),'second_terminal_status':second_term.get('status'),
                   'second_terminal_release_verified':(second_term.get('release') or {}).get('verified'),
                   'shift_input_admissions':len(left_adm),'right_input_admissions':len(right_adm),
                   'owner_expiry_releases':len(expiry),'owner_expiry_all_verified':bool(expiry) and all(e.get('verified') is True for e in expiry),
                   'owner_all_verified':all(e.get('verified') is True for e in owner if e.get('event')=='owner_release'),
                   'terminal_score_audit_exit':cp.returncode,'score':score}
        (out/'smoke-summary.json').write_text(json.dumps(resultrow,indent=2)+'\n');return resultrow
    finally:
        if s.p.poll() is None:s.finish()

def main():
    root=Path(sys.argv[1]);
    if root.exists(): raise SystemExit('output exists')
    rows=[run_condition(root,'FRESH',994001),run_condition(root,'STALE',994002)]
    print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
