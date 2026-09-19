import json, os, signal, subprocess, tempfile, time, sys
from pathlib import Path
sys.path.insert(0, '/workspace')
from runtime.cli_v1.golden_v3 import dispatch_golden_v3

display=':149'; env=os.environ.copy(); env['DISPLAY']=display; os.environ['DISPLAY']=display
root=Path(tempfile.mkdtemp(prefix='replacement-')); procs=[]
try:
    xv=subprocess.Popen(['Xvfb',display,'-screen','0','1024x480x24','-nolisten','tcp','-ac'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); procs.append(xv); time.sleep(.5)
    def start(name,mode):
        d=root/name; d.mkdir(); p=subprocess.Popen(['/usr/bin/python3','/workspace/research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py','--mode',mode,'--meta',str(d/'meta.json'),'--effect',str(d/'effect.json'),'--events',str(d/'events.jsonl')],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True); procs.append(p)
        deadline=time.monotonic()+10
        while not (d/'meta.json').exists() and time.monotonic()<deadline: time.sleep(.02)
        return p,d,str(json.loads((d/'meta.json').read_text())['window_id'])
    old,od,old_xid=start('old','useful'); new,nd,new_xid=start('replacement','useful')
    distinct=old_xid != new_xid
    old.terminate(); old.wait(timeout=3); time.sleep(.1)
    program={'schema':'agent-interface/program-v1','program_id':'replacement-old-target','source':{'observation_seq':1,'binding_revision':1},'authority':{'lease_id':'replacement','expires_at_ns':time.monotonic_ns()+5_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'old'},{'op':'key_chord','keys':['CTRL','s']},{'op':'release_all'}]}
    stale=dispatch_golden_v3(program,{'old':int(old_xid)},current_observation_seq=1,current_binding_revision=1,display_name=display)
    control=dispatch_golden_v3({**program,'program_id':'replacement-control','ops':[{'op':'focus','target':'replacement'},{'op':'key_chord','keys':['CTRL','s']},{'op':'release_all'}]}, {'replacement':int(new_xid)},current_observation_seq=1,current_binding_revision=1,display_name=display)
    time.sleep(.2)
    result={'decision':'PASS_TARGET_REPLACEMENT_DISTINCT_SCOPED' if distinct and stale.get('native_status')=='execution_failed' and stale.get('raw_dispatch',{}).get('result',{}).get('execution',{}).get('program_emissions')==0 and control.get('native_status')=='completed' and nd.joinpath('effect.json').exists() else 'FAIL_TARGET_REPLACEMENT','old_xid':old_xid,'new_xid':new_xid,'distinct':distinct,'stale':stale,'control':control,'old_effect':od.joinpath('effect.json').exists(),'new_effect':nd.joinpath('effect.json').exists(),'model_calls':0,'network_calls':0}
    print(json.dumps(result,sort_keys=True))
finally:
    for p in reversed(procs):
        if p.poll() is None: p.terminate()
