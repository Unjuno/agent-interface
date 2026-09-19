from __future__ import annotations
import json,subprocess,tempfile,time,threading
from pathlib import Path
from Xlib import display
from common import *

SCENARIOS=('INDEPENDENT','SHARED_GLOBAL_CANDIDATE','SHARED_GLOBAL_SURFACE_ONLY','EXTERNAL_STALE')

def run_case(case_id:str,scenario:str):
    assert scenario in SCENARIOS
    work=Path(tempfile.mkdtemp(prefix='ai1750-'+case_id+'-'))
    xvfb=None; workers=[]; observer=None
    result={'case_id':case_id,'scenario':scenario,'error':None,'owner_commands':[]}
    try:
        xvfb,dname,env=start_xvfb(work)
        ready=[]
        for name,geom in [('A','260x180+80+120'),('B','260x180+520+120')]:
            sock=work/f'{name}.sock'; rdy=work/f'{name}.ready.json'
            p=subprocess.Popen([env.get('PYTHON','python3'),str(Path(__file__).with_name('worker.py')),'--display',dname,'--name',name,'--sock',str(sock),'--ready',str(rdy),'--geom',geom],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
            workers.append(p);ready.append(wait_json(rdy))
        observer=display.Display(dname); root=observer.screen().root
        set_cardinal(observer,root,GLOBAL_ATOM,0)
        a_win=observer.create_resource_object('window',ready[0]['xid']);b_win=observer.create_resource_object('window',ready[1]['xid'])
        receipts=read_receipts(observer,a_win,b_win);result['prepared_receipts']=dict(receipts);result['surface_xids']={'A':ready[0]['xid'],'B':ready[1]['xid']}
        def cmd(idx,payload):
            resp=send_cmd(ready[idx]['socket'],payload); result['owner_commands'].append({'worker':('A','B')[idx],'command':payload,'response':resp});return resp
        if scenario=='INDEPENDENT':
            ra={'A_LOCAL'};wa={'A_EFFECT'};rb={'B_LOCAL'};wb={'B_EFFECT'};changed=set();decision=candidate(ra,wa,rb,wb,changed);result['decision']=decision
            out=[None,None]
            ta=threading.Thread(target=lambda:out.__setitem__(0,cmd(0,{'op':'set_effect','value':'LOCAL1'})))
            tb=threading.Thread(target=lambda:out.__setitem__(1,cmd(1,{'op':'set_effect','value':'LOCAL1'})))
            ta.start();tb.start();ta.join();tb.join()
            result['parallel_owner_responses']=out
        elif scenario=='SHARED_GLOBAL_CANDIDATE':
            ra=set();wa={'GLOBAL'};rb={'GLOBAL'};wb={'B_EFFECT'};changed=set();decision=candidate(ra,wa,rb,wb,changed);result['decision']=decision
            a=cmd(0,{'op':'set_global','value':1}); after_a=read_receipts(observer,a_win,b_win);result['after_a_receipts']=after_a
            stale=(after_a['GLOBAL']!=receipts['GLOBAL']);result['b_receipt_stale_after_a']=stale
            if not stale: raise AssertionError('B receipt unexpectedly current')
            result['b_reprepare_count']=1
            b=cmd(1,{'op':'set_effect','value':'G'+str(after_a['GLOBAL'])});result['serial_owner_responses']=[a,b]
        elif scenario=='SHARED_GLOBAL_SURFACE_ONLY':
            result['decision']='PARALLEL_SURFACE_ONLY' if ready[0]['xid']!=ready[1]['xid'] else 'SERIALIZE_SURFACE_ONLY'
            prepared=receipts['GLOBAL'];out=[None,None]
            ta=threading.Thread(target=lambda:out.__setitem__(0,cmd(0,{'op':'set_global','value':1,'delay_ms':0})))
            tb=threading.Thread(target=lambda:out.__setitem__(1,cmd(1,{'op':'set_effect','value':'G'+str(prepared),'delay_ms':30})))
            ta.start();tb.start();ta.join();tb.join();result['parallel_owner_responses']=out
            result['a_before_b_effect']=out[0]['applied_ns'] < out[1]['applied_ns']
        else:
            rb={'B_LOCAL'};wb={'B_EFFECT'};cmd(1,{'op':'bump_local'});now=read_receipts(observer,a_win,b_win);changed={k for k,v in receipts.items() if now[k]!=v};result['changed_resources']=sorted(changed)
            decision=candidate(set(),set(),rb,wb,changed);result['decision']=decision;result['b_effect_command_count']=0
        final=read_receipts(observer,a_win,b_win);result['final_receipts']=final;result['final_effects']={'A':get_effect(observer,a_win),'B':get_effect(observer,b_win)}
        result['mapped_distinct_xids']=ready[0]['xid']!=ready[1]['xid']
        result['oracle_decision_data']={'scenario':scenario}
        result['pass_case']=True
    except Exception as e:
        result['error']=repr(e);result['pass_case']=False
    finally:
        if observer is not None:
            try:observer.close()
            except Exception:pass
        for idx,p in enumerate(workers):
            if p.poll() is None:
                try:send_cmd(str(work/f'{("A","B")[idx]}.sock'),{'op':'shutdown'},timeout=1)
                except Exception:pass
            stop_proc(p)
        stop_proc(xvfb)
        result['cleanup_workers_exited']=all(p.poll() is not None for p in workers)
        result['cleanup_xvfb_exited']=(xvfb is None or xvfb.poll() is not None)
    return result

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('case_id');ap.add_argument('scenario',choices=SCENARIOS);a=ap.parse_args();print(json.dumps(run_case(a.case_id,a.scenario),sort_keys=True))
