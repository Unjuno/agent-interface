from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
PKG=ROOT/'research/doom/map01_v39_startup_release_order_a01_20261005'
REL=[
 'research/doom/map01_overlap_controller_v39.py','research/doom/session_map01_v15.py',
 'research/doom/doom_owner_thread_release_batch_backend_v1.py','research/doom/doom_typed_release_backend_v2.py',
 'research/doom/doom_typed_release_backend_v1.py','research/live_control/input_transition_owner_v4.py',
 'research/live_control/input_transition_owner_v3.py','research/live_control/input_owner_v12.py',
 'research/live_control/input_owner_v10.py',
 'research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/test_input_owner_v12.py',
 'research/doom/map01_v39_perkey_bridge_a01/test_bridge.py',
 'research/doom/map01_v39_startup_release_order_a01_20261005/candidate.py',
 'research/doom/map01_v39_startup_release_order_a01_20261005/PLAN.md']
def sha_bytes(b):return hashlib.sha256(b.replace(b'\r\n',b'\n')).hexdigest()
commit=json.loads((PKG/'FREEZE.json').read_text(encoding='utf-8-sig'))['base_commit']
freeze={'schema':'map01-v39-startup-release-order-freeze-v1','run_id':'MAP01-V39-STARTUP-RELEASE-ORDER-A01-20261005','base_commit':commit,'source_sha256':{r:sha_bytes((ROOT/r).read_bytes()) for r in REL},'source_closure_note':'V39 selector and V15 telemetry class are exact main sources; backend execution and release/owner sources are exact. Typed command interpreter/capture parent and DoomGame are deterministic seams. Fake X instance is supplied by retained harness with exact runtime live_control/input_owner_v12.py.','sequence':['DOWN F8','DOWN SPACE','UP SPACE','UP F8'],'candidate_attempts':{'preflight_no_input':2,'wrong_harness_stops':2,'successful_corrected_candidate':1},'formal_live_allocation':False,'environment':{'fake_x_display':True,'os_input':False,'gui_capture':False,'vizdoom':False,'model_calls':0,'docker':False}}
(PKG/'FREEZE.json').write_text(json.dumps(freeze,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'base_commit':commit,'sources':len(REL),'freeze_sha256':sha_bytes((PKG/'FREEZE.json').read_bytes())}))
