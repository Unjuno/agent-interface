#!/usr/bin/env python3
"""Audit A01 raw/source/input without rerunning the candidate."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
f=json.loads((HERE/'FREEZE.json').read_text())
raw=json.loads((PARENT/'raw.json').read_text())
readout_path=PARENT/'input/VISUAL_READOUT.json'
readout=json.loads(readout_path.read_text())
repo=PARENT.parents[2]
controller=repo/'research/doom/map01_overlap_controller_v39.py'
guard=repo/'research/live_control/observable_signal_guard_v2.py'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
errors=[]
if sha(readout_path)!=f['input_readout_sha256']:errors.append('input_sha256')
if sha(controller)!=f['controller_source_sha256'] or raw.get('controller_sha256')!=f['controller_source_sha256']:errors.append('controller_source_hash')
if sha(guard)!=f['guard_source_sha256'] or raw.get('guard_sha256')!=f['guard_source_sha256']:errors.append('guard_source_hash')
if raw.get('main_base')!=f['main_base']:errors.append('main_base')
rows={float(x['game_clock'].rstrip('s')):x for x in readout['samples']}
for t,h,a,phase in [(44.6,100,46,'MODEL THINKING + LOCAL COVER'),(46.8,100,44,'MODEL THINKING + LOCAL COVER'),(47.0,96,44,'MODEL THINKING + LOCAL COVER'),(54.8,94,37,'MODEL THINKING + LOCAL COVER'),(56.2,94,37,'MODEL THINKING + LOCAL COVER'),(56.4,87,37,'LOCAL PLAN / FEEDBACK')]:
 x=rows.get(t)
 if x is None or (x['health'],x['ammo'],x['phase'])!=(h,a,phase):errors.append(f'readout_{t}')
x=raw.get('output',{})
expected={'source_admission':'admitted','hard_minimum':97,'invalidation_event':'paired_signal_invalidation','reason':'health:below_hard_minimum','health_outcome':'HARD_INVALIDATED','ammo_outcome':'SOFT_CHANGED','grants_input_authority':False,'final_admission':'REJECTED_POLICY_INVALIDATED','planner_interrupt':'interrupted','cancel_request':{'op':'cancel','id':'cover-4'},'terminal_status':'cancelled','release':{'verified':True,'keys_down':[],'buttons_down':[]},'cancel_helper_returned':True}
for k,v in expected.items():
 if x.get(k)!=v:errors.append(f'raw_{k}')
if raw.get('observation_game_time_s')!=47.0 or raw.get('health')!=96 or raw.get('ammo')!=44:errors.append('candidate_observation')
out={'status':'PASS_AUDIT_SUCCESSOR_A02' if not errors else 'FAIL_AUDIT_SUCCESSOR_A02','errors':errors,'audit_v1_disposition':'FAIL_PRESERVED_KEY_MAPPING_BUG','candidate_rerun':False,'input_sha256':sha(readout_path),'controller_sha256':sha(controller),'guard_sha256':sha(guard),'raw_sha256':sha(PARENT/'raw.json'),'scope':'read-only identity/value/contract reconstruction; test doubles only'}
(HERE/'AUDIT.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
if errors:raise SystemExit(1)
