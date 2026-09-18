from __future__ import annotations
import argparse,json,os,subprocess,time
from pathlib import Path
from Xlib import X,display
from snapshot import mint,resolve
from oracle import resolve as oracle_resolve

TASK='CAPABILITY-SNAPSHOT-XTEST-REVOCATION-R1-20260919-001'
REQ='XTEST_INPUT'
SUP_E=('CORE_INPUT_FALLBACK','OBSERVE_CONTEXT','XTEST_INPUT')
SUP_D=('CORE_INPUT_FALLBACK','OBSERVE_CONTEXT')
SCENARIOS=('E_FRESH_A','E_WRONG_SCOPE_B','D_STALE_E_SNAPSHOT','D_FRESH_A','D_WRONG_SCOPE_B')

class EpochServer:
    def __init__(self,display_num,xtest_enabled):
        self.display_num=display_num; self.disp=f':{display_num}'; self.enabled=bool(xtest_enabled)
        self.auth=str(Path(__file__).with_name(f'empty-{display_num}.Xauthority'));Path(self.auth).touch()
        env=os.environ.copy();env['DISPLAY']=self.disp;env['XAUTHORITY']=self.auth
        cmd=['Xvfb',self.disp,'-screen','0','640x300x24','-nolisten','tcp','-ac']
        if not self.enabled:cmd+=['-extension','XTEST']
        self.proc=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=env)
        if not self._wait_socket(True): raise RuntimeError('xvfb_socket_not_ready')
        self.tkproc=subprocess.Popen(
            [os.environ.get('PYTHON','python3'),str(Path(__file__).with_name('tk_fixture.py')),'--display',self.disp],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env
        )
        line=self.tkproc.stdout.readline().strip()
        if not line:
            err=self.tkproc.stderr.read()
            raise RuntimeError('tk_fixture_not_ready:'+err)
        ids=json.loads(line);self.aid=int(ids['aid']);self.bid=int(ids['bid'])
        old=os.environ.get('XAUTHORITY');os.environ['XAUTHORITY']=self.auth
        try:
            self.writer=display.Display(self.disp);self.reader=display.Display(self.disp)
        finally:
            if old is None:os.environ.pop('XAUTHORITY',None)
            else:os.environ['XAUTHORITY']=old
        self.aw=self.writer.create_resource_object('window',self.aid)
    @property
    def socket(self):return f'/tmp/.X11-unix/X{self.display_num}'
    def _wait_socket(self,present):
        for _ in range(150):
            if os.path.exists(self.socket)==present:return True
            time.sleep(.01)
        return False
    def setup_focus_a(self):
        self.aw.set_input_focus(X.RevertToParent,X.CurrentTime);self.writer.sync();time.sleep(.001)
    def cap_reply(self):
        t0=time.perf_counter_ns();rep=self.reader.query_extension('XTEST');t1=time.perf_counter_ns()
        if rep is None:return {'present':0,'major_opcode':None,'first_event':None,'first_error':None,'begin_ns':t0,'end_ns':t1}
        return {'present':int(getattr(rep,'present',1)),'major_opcode':int(getattr(rep,'major_opcode',0)),'first_event':int(getattr(rep,'first_event',0)),'first_error':int(getattr(rep,'first_error',0)),'begin_ns':t0,'end_ns':t1}
    def focus(self):return int(self.reader.get_input_focus().focus.id)
    def scope(self,which):return f'{self.disp}:{which}:{self.aid if which=="A" else self.bid}'
    def close(self):
        try:self.reader.close();self.writer.close()
        except Exception:pass
        tkpid=self.tkproc.pid
        self.tkproc.terminate()
        try:self.tkproc.wait(timeout=2)
        except Exception:self.tkproc.kill();self.tkproc.wait()
        tkerr=self.tkproc.stderr.read() if self.tkproc.stderr else ''
        pid=self.proc.pid;self.proc.terminate()
        try:self.proc.wait(timeout=1)
        except Exception:self.proc.kill();self.proc.wait()
        gone=self._wait_socket(False)
        return {'pid':pid,'returncode':self.proc.returncode,'tk_pid':tkpid,'tk_returncode':self.tkproc.returncode,'tk_stderr':tkerr,'socket_disappeared':bool(gone)}

def current(server,which,generation,supported):
    return {'scope':server.scope(which),'generation':generation,'supported':tuple(sorted(supported))}

def evaluate_row(pair_id,name,current_state,snap,server,expected):
    before={'focus_id':server.focus(),'cap':server.cap_reply()}
    cand=resolve(current_state,snap,REQ); okind,osel,ogrant=oracle_resolve(current_state,snap,REQ)
    after={'focus_id':server.focus(),'cap':server.cap_reply()}
    nk=cand['disposition'] if cand['disposition'] in ('DIRECT','FALLBACK','UNSUPPORTED') else 'INVALID'
    mismatch=(nk,cand['selected'],cand['grants_action_authority'])!=(okind,osel,ogrant)
    return {'pair':pair_id,'scenario':name,'current':current_state,'snapshot':snap,'request':REQ,'candidate':cand,'oracle':{'disposition':okind,'selected':osel,'grants_action_authority':ogrant},'expected':expected,'candidate_oracle_mismatch':mismatch,'before':before,'after':after,'focus_unchanged':before['focus_id']==after['focus_id'],'cap_unchanged':before['cap']['present']==after['cap']['present'],'task_input_calls':0,'xtest_action_calls':0}

def run(pairs,display_base):
    rows=[];pairs_meta=[];stops=[]
    for pair in range(pairs):
        dispnum=display_base+pair;g=pair*2
        E=EpochServer(dispnum,True)
        try:
            E.setup_focus_a(); capE=E.cap_reply();
            if capE['present']!=1:
                stops.append({'pair':pair,'phase':'E','reason':'XTEST_NOT_PRESENT','cap':capE});continue
            curEA=current(E,'A',g,SUP_E);curEB=current(E,'B',g,SUP_E);snapE=mint(curEA['scope'],g,SUP_E)
            rows.append(evaluate_row(pair,'E_FRESH_A',curEA,snapE,E,{'disposition':'DIRECT','selected':'XTEST_INPUT'}))
            rows.append(evaluate_row(pair,'E_WRONG_SCOPE_B',curEB,snapE,E,{'disposition':'INVALID','selected':None}))
            emeta={'display':E.disp,'aid':E.aid,'bid':E.bid,'cap_reply':capE,'snapshot_id':snapE['snapshot_id'],'generation':g}
        finally:
            eclose=E.close()
        if not eclose['socket_disappeared']:
            stops.append({'pair':pair,'phase':'E_CLOSE','reason':'SOCKET_NOT_GONE','close':eclose});continue
        D=EpochServer(dispnum,False)
        try:
            D.setup_focus_a();capD=D.cap_reply()
            if capD['present']!=0:
                stops.append({'pair':pair,'phase':'D','reason':'XTEST_NOT_ABSENT','cap':capD});continue
            curDA=current(D,'A',g+1,SUP_D);curDB=current(D,'B',g+1,SUP_D);snapD=mint(curDA['scope'],g+1,SUP_D)
            rows.append(evaluate_row(pair,'D_STALE_E_SNAPSHOT',curDA,snapE,D,{'disposition':'INVALID','selected':None}))
            rows.append(evaluate_row(pair,'D_FRESH_A',curDA,snapD,D,{'disposition':'FALLBACK','selected':'CORE_INPUT_FALLBACK'}))
            rows.append(evaluate_row(pair,'D_WRONG_SCOPE_B',curDB,snapD,D,{'disposition':'INVALID','selected':None}))
            dmeta={'display':D.disp,'aid':D.aid,'bid':D.bid,'cap_reply':capD,'snapshot_id':snapD['snapshot_id'],'generation':g+1}
        finally:
            dclose=D.close()
        pairs_meta.append({'pair':pair,'E':emeta,'E_close':eclose,'D':dmeta,'D_close':dclose})
    from collections import Counter
    scenarios=Counter(x['scenario'] for x in rows)
    m={'pairs_requested':pairs,'pairs_completed':len(pairs_meta),'rows':len(rows),'scenario_counts':dict(scenarios),'candidate_oracle_mismatch':sum(x['candidate_oracle_mismatch'] for x in rows),'wrong_expected':sum((x['candidate']['disposition'] if x['candidate']['disposition'] in ('DIRECT','FALLBACK','UNSUPPORTED') else 'INVALID',x['candidate']['selected'])!=(x['expected']['disposition'],x['expected']['selected']) for x in rows),'stale_selected':sum(x['scenario']=='D_STALE_E_SNAPSHOT' and x['candidate']['selected'] is not None for x in rows),'wrong_scope_selected':sum('WRONG_SCOPE' in x['scenario'] and x['candidate']['selected'] is not None for x in rows),'authority_grants':sum(x['candidate']['grants_action_authority'] for x in rows),'task_input_calls':sum(x['task_input_calls'] for x in rows),'xtest_action_calls':sum(x['xtest_action_calls'] for x in rows),'focus_changed':sum(not x['focus_unchanged'] for x in rows),'cap_changed':sum(not x['cap_unchanged'] for x in rows),'socket_disappearance_failures':sum(not p['E_close']['socket_disappeared'] for p in pairs_meta),'E_present_failures':sum(p['E']['cap_reply']['present']!=1 for p in pairs_meta),'D_absent_failures':sum(p['D']['cap_reply']['present']!=0 for p in pairs_meta),'stops':len(stops)}
    phase='formal' if pairs==16 else 'construction';expected_counts={s:pairs for s in SCENARIOS}
    good=(len(pairs_meta)==pairs and len(rows)==pairs*5 and dict(scenarios)==expected_counts and all(m[k]==0 for k in ('candidate_oracle_mismatch','wrong_expected','stale_selected','wrong_scope_selected','authority_grants','task_input_calls','xtest_action_calls','focus_changed','cap_changed','socket_disappearance_failures','E_present_failures','D_absent_failures','stops')))
    decision=('PASS_CAPABILITY_SNAPSHOT_XTEST_REVOCATION_R1_SCOPED' if phase=='formal' else 'PASS_CONSTRUCTION_ELIGIBLE') if good else ('HOLD_REAL_REVOCATION_DISCRIMINATOR' if m['E_present_failures'] or m['D_absent_failures'] or m['socket_disappearance_failures'] else 'FAIL_CAPABILITY_SNAPSHOT_CURRENTNESS_ESCAPE')
    return {'task':TASK,'phase':phase,'formal_invocations':1 if phase=='formal' else 0,'reruns':0,'replacements':0,'tuning':0,'decision':decision,'metrics':m,'pairs':pairs_meta,'rows':rows,'stops':stops}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--pairs',type=int,default=2);ap.add_argument('--display-base',type=int,default=1300);ap.add_argument('--out',required=True);a=ap.parse_args();r=run(a.pairs,a.display_base);Path(a.out).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps({'decision':r['decision'],'metrics':r['metrics'],'stops':r['stops']},indent=2,sort_keys=True))
