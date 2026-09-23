import json, os, select, subprocess, sys, time
from pathlib import Path
REPO_ROOT=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(REPO_ROOT))
import runtime.cli_v1.golden_v3 as golden
from runtime.core_v1.contract import SCHEMA_PROGRAM

root=Path('ambiguous-fault-probe'); root.mkdir(exist_ok=False)
xvfb=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','640x360x24','-nolisten','tcp','-ac'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
assert select.select([xvfb.stdout],[],[],10)[0]; display=':'+xvfb.stdout.readline().strip(); os.environ['DISPLAY']=display
fixture=subprocess.Popen([sys.executable,'research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py','--meta',str(root/'meta.json'),'--effect',str(root/'effect.json'),'--events',str(root/'events.jsonl')],env=dict(os.environ,DISPLAY=display))
try:
 deadline=time.monotonic()+10
 while not (root/'meta.json').exists():
  assert fixture.poll() is None and time.monotonic()<deadline; time.sleep(.02)
 target=json.loads((root/'meta.json').read_text())['window_id']
 original=golden.dispatch
 def faulted(*args,**kwargs):
  raw=original(*args,**kwargs); raw['delivery']='ambiguous'; raw['fault_injector']='post-dispatch-transport-ambiguity-v1'; return raw
 golden.dispatch=faulted
 program={'schema':SCHEMA_PROGRAM,'program_id':'ambiguous-fault-probe','source':{'observation_seq':1,'binding_revision':1},'authority':{'lease_id':'ambiguous-probe','expires_at_ns':time.monotonic_ns()+10_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'fixture'},{'op':'text','text':'ambiguous'},{'op':'key_chord','keys':['CTRL','s']},{'op':'release_all'}]}
 result=golden.dispatch_golden_v3(program,{'fixture':target},current_observation_seq=1,current_binding_revision=1,display_name=display)
 print(json.dumps({'fault_injected_after_real_dispatch':True,'adapter_result':result,'replay_allowed':False,'success_claim_allowed':False,'effect_exists':(root/'effect.json').exists(),'scope':'local GTK/X11 post-dispatch ambiguity fault-injection preflight; not formal #2606 acceptance'},indent=2,sort_keys=True))
finally:
 if fixture.poll() is None: fixture.terminate()
 if xvfb.poll() is None: xvfb.terminate()
