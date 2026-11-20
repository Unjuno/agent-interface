from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];PKG=ROOT/'research/doom/v39_v15_keymap_after_batch_a05_20261005'
REL=[
'research/doom/map01_overlap_controller_v39.py','research/doom/session_map01_v15.py',
'research/doom/doom_owner_thread_release_batch_backend_v1.py','research/doom/doom_typed_release_backend_v2.py','research/doom/doom_typed_release_backend_v1.py',
'research/live_control/input_transition_owner_v4.py','research/live_control/input_transition_owner_v3.py','research/live_control/input_owner_v12.py','research/live_control/input_owner_v10.py',
'research/live_control/executor_v13.py','research/live_control/executor_v12.py',
'research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/test_input_owner_v12.py',
'research/doom/map01_v39_perkey_bridge_a01/test_bridge.py',
'research/doom/v39_v15_keymap_after_batch_a05_20261005/PLAN.md',
'research/doom/v39_v15_keymap_after_batch_a05_20261005/candidate.py']
def sha(b):return hashlib.sha256(b.replace(b'\r\n',b'\n')).hexdigest()
head=subprocess.run(['git','-C',str(ROOT),'rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip()
freeze={'schema':'v39-v15-keymap-after-batch-a05-freeze-v1','run_id':'V39-V15-KEYMAP-AFTER-BATCH-A05-20261005','base_commit':head,'source_sha256':{x:sha((ROOT/x).read_bytes()) for x in REL},'cases':['normal-two-key-release','dropped-space-keyup-injection','post-batch-query-unavailable'],'sequence':['DOWN F8','DOWN SPACE','UP SPACE','UP F8'],'authority_claimed':False,'formal_live_allocation':False,'environment':{'fake_x_display':True,'os_input':False,'gui_capture':False,'doomgame':False,'model_calls':0,'docker':False}}
(PKG/'FREEZE.json').write_text(json.dumps(freeze,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'base_commit':head,'sources':len(REL),'freeze_sha256':sha((PKG/'FREEZE.json').read_bytes())}))
