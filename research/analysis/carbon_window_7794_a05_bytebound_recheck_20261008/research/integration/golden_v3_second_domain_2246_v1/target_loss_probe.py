import json, os, select, subprocess, sys, time
from pathlib import Path
REPO_ROOT=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(REPO_ROOT))
from runtime.cli_v1.golden_v3 import dispatch_golden_v3
from runtime.core_v1.contract import SCHEMA_PROGRAM

root=Path('target-loss-probe'); root.mkdir(exist_ok=False)
xvfb=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','640x360x24','-nolisten','tcp','-ac'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
assert select.select([xvfb.stdout],[],[],10)[0]
display=':'+xvfb.stdout.readline().strip(); os.environ['DISPLAY']=display
fixture=subprocess.Popen([sys.executable,'research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py','--meta',str(root/'meta.json'),'--effect',str(root/'effect.json'),'--events',str(root/'events.jsonl')],env=dict(os.environ,DISPLAY=display))
try:
 deadline=time.monotonic()+10
 while not (root/'meta.json').exists():
  assert fixture.poll() is None and time.monotonic()<deadline
  time.sleep(.02)
 target=json.loads((root/'meta.json').read_text())['window_id']; fixture.terminate(); fixture.wait(timeout=5); time.sleep(.05)
 program={'schema':SCHEMA_PROGRAM,'program_id':'target-loss-cleanup-probe','source':{'observation_seq':1,'binding_revision':1},'authority':{'lease_id':'loss-probe','expires_at_ns':time.monotonic_ns()+10_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'fixture'},{'op':'pointer_move','frame':'window_client','x':60,'y':45},{'op':'text','text':'loss'},{'op':'release_all'}]}
 result=dispatch_golden_v3(program,{'fixture':target},current_observation_seq=1,current_binding_revision=1,display_name=display)
 print(json.dumps({'target_destroyed_before_dispatch':True,'adapter_result':result,'success_claim_allowed':False,'scope':'local GTK/X11 target-loss cleanup failure probe; not formal #2606 acceptance'},indent=2,sort_keys=True))
finally:
 if xvfb.poll() is None: xvfb.terminate()
