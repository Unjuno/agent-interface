import json, os, select, subprocess, sys, time
from pathlib import Path
from runtime.cli_v1.golden_v3 import dispatch_golden_v3
from runtime.core_v1.contract import SCHEMA_PROGRAM
def save(p,v): p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def start_fixture(out, display, mode='useful'):
    out.mkdir(parents=True,exist_ok=True)
    p=subprocess.Popen(['/usr/bin/python3','research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py','--mode',mode,'--meta',str(out/'meta.json'),'--effect',str(out/'effect.json'),'--events',str(out/'events.jsonl')],env=dict(os.environ,DISPLAY=display),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    end=time.monotonic()+10
    while not (out/'meta.json').exists():
        if p.poll() is not None: raise RuntimeError('fixture exited')
        if time.monotonic()>end: raise RuntimeError('fixture timeout')
        time.sleep(.02)
    return p,json.loads((out/'meta.json').read_text())['window_id']
def program(name, source):
    return {'schema':SCHEMA_PROGRAM,'program_id':name,'source':source,'authority':{'lease_id':name,'expires_at_ns':time.monotonic_ns()+10_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'fixture'},{'op':'pointer_move','frame':'window_client','x':60,'y':45},{'op':'pointer_button','button':'left','down':True},{'op':'pointer_button','button':'left','down':False},{'op':'text','text':name},{'op':'key_chord','keys':['CTRL','s']},{'op':'wait_update','timeout_ms':100},{'op':'observe','frame':'window_client','x':0,'y':0,'w':400,'h':180},{'op':'release_all'}]}
def main():
    out=Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=False); procs=[]
    xvfb=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','640x360x24','-nolisten','tcp','-ac'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True); procs.append(xvfb)
    if not select.select([xvfb.stdout],[],[],10)[0]: raise RuntimeError('Xvfb timeout')
    display=':'+xvfb.stdout.readline().strip(); os.environ['DISPLAY']=display
    try:
        control_dir=out/'useful-control'; p,xid=start_fixture(control_dir,display); procs.append(p)
        os.environ['AGENT_INTERFACE_XTEST_LOG']=str(control_dir/'xtest.jsonl')
        control=dispatch_golden_v3(program('useful-control',{'observation_seq':1,'binding_revision':1}),{'fixture':xid},current_observation_seq=1,current_binding_revision=1,display_name=display,capture_directory=str(control_dir/'capture'))
        save(control_dir/'adapter.json',control); p.terminate(); p.wait(timeout=5); procs.pop()
        rep_dir=out/'target-replacement'; oldp,oldid=start_fixture(rep_dir/'original',display); procs.append(oldp)
        newp,newid=start_fixture(rep_dir/'replacement',display); procs.append(newp)
        os.environ['AGENT_INTERFACE_XTEST_LOG']=str(rep_dir/'xtest.jsonl')
        distinct_before_destroy = oldid != newid
        oldp.terminate(); oldp.wait(timeout=5); procs.pop()
        try: replacement=dispatch_golden_v3(program('target-replacement',{'observation_seq':1,'binding_revision':1}),{'fixture':oldid},current_observation_seq=1,current_binding_revision=1,display_name=display,capture_directory=str(rep_dir/'capture'))
        except Exception as e: replacement={'runner_exception':repr(e)}
        save(rep_dir/'adapter.json',replacement)
        src_dir=out/'source-mismatch'; sp,sid=start_fixture(src_dir,display); procs.append(sp)
        os.environ['AGENT_INTERFACE_XTEST_LOG']=str(src_dir/'xtest.jsonl')
        try: mismatch=dispatch_golden_v3(program('source-mismatch',{'observation_seq':1,'binding_revision':999}),{'fixture':sid},current_observation_seq=1,current_binding_revision=1,display_name=display,capture_directory=str(src_dir/'capture'))
        except Exception as e: mismatch={'runner_exception':repr(e)}
        save(src_dir/'adapter.json',mismatch)
        summary={'schema':'golden_v3_identity_fail_closed_result_v1','allocation':'golden-v3-identity-20260920-a2','display':display,'rows':{'useful_control':{'window_id':xid,'result':control},'target_replacement':{'old_window_id':oldid,'replacement_window_id':newid,'distinct_before_destroy':distinct_before_destroy,'result':replacement},'source_mismatch':{'window_id':sid,'requested_binding_revision':999,'current_binding_revision':1,'result':mismatch}},'decision':'PASS_GOLDEN_V3_IDENTITY_FAIL_CLOSED_SCOPED' if control.get('status') in ('success','partial') and distinct_before_destroy and replacement.get('status')=='refused' and mismatch.get('status')=='refused' else 'HOLD_IDENTITY_FAIL_CLOSED_NOT_PROVEN'}
        save(out/'summary.json',summary); print(json.dumps(summary,indent=2,sort_keys=True))
    finally:
        for p in reversed(procs):
            if p.poll() is None: p.terminate()
            try: p.wait(timeout=5)
            except subprocess.TimeoutExpired: p.kill()
if __name__=='__main__': main()
