#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent/'measured'
P=json.loads((Path(__file__).resolve().parent/'prereg.json').read_text())
errors=[]; rows=[]
for i,arm in enumerate(P['schedule']):
 p=ROOT/f'case-{i:02d}'/'result.json'
 if not p.exists(): errors.append(f'missing {i}'); continue
 r=json.loads(p.read_text()); rows.append(r)
 if not r.get('finished'):errors.append(f'unfinished {i}')
 if r.get('arm')!=arm:errors.append(f'arm {i}')
 if not r.get('registry_owner'):errors.append(f'registry {i}')
 if r.get('path_equal')!={'A':True,'B':True}:errors.append(f'path_equal {i}')
 if r.get('old_name_after_reopen')!={'A':'AI_Target_A','B':'AI_Target_B'}:errors.append(f'names {i}')
 if not r.get('final_keymap_empty'):errors.append(f'keymap {i}')
 for k in ('A','B'):
  for m in ('props','role','state'):
   if r.get('probe_closed',{}).get(k,{}).get(m,{}).get('rc')!=0:errors.append(f'closed {i} {k} {m}')
 if arm=='launcher_bus':
  if r.get('app_bus_resolution')!='unique_private_bus_root_name':errors.append(f'launcher resolution {i}')
  if r.get('pid_attribution_available') is not False:errors.append(f'launcher pid boundary {i}')
  if not r.get('launcher_reported_address') or not r.get('launcher_host_mapped_address'):errors.append(f'launcher addr {i}')
 else:
  if r.get('app_bus_resolution')!='pid':errors.append(f'direct resolution {i}')
dec='REJECT_LAUNCHER_GENERATED_BUS_ALONE_AS_DEFUNCT_CAUSE_SCOPED' if not errors and len(rows)==6 else 'HOLD'
out={'schema':'inkscape-atspi-launcher-bus-path-lifetime-audit-v1','pass':not errors and len(rows)==6,'decision':dec,'cases':len(rows),'errors':errors}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if out['pass'] else 1)
