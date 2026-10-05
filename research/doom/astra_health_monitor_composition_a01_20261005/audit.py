#!/usr/bin/env python3
"""Read-only literal-contract audit of the retained composition output."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
f=json.loads((HERE/'FREEZE.json').read_text()); r=json.loads((HERE/'raw.json').read_text()); x=r['output']
expected={'source_admission':'admitted','hard_minimum':97,'invalidation_event':'paired_signal_invalidation','reason':'health:below_hard_minimum','health_outcome':'HARD_INVALIDATED','ammo_outcome':'SOFT_CHANGED','grants_input_authority':False,'final_admission':'REJECTED_POLICY_INVALIDATED','planner_interrupt':'interrupted','cancel_request':{'op':'cancel','id':'cover-4'},'terminal_status':'cancelled','release':{'verified':True,'keys_down':[],'buttons_down':[]},'cancel_helper_returned':True}
errors=[]
for k,v in expected.items():
 if x.get(k)!=v: errors.append(k)
for key in ('controller_sha256','guard_sha256','input_readout_sha256'):
 if r.get(key)!=f.get(key): errors.append(key)
if r.get('main_base')!=f.get('main_base'): errors.append('main_base')
out={'status':'PASS_SOFTWARE_COMPOSITION_RECONSTRUCTION' if not errors else 'FAIL_SOFTWARE_COMPOSITION_RECONSTRUCTION','errors':errors,'raw_sha256':hashlib.sha256((HERE/'raw.json').read_bytes()).hexdigest(),'scope':'audit of constructed output only; no claim about real OS/application release'}
(HERE/'AUDIT.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
if errors: raise SystemExit(1)
