#!/usr/bin/env python3
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); sched=['explicit_address','session_discovery','session_discovery','explicit_address','explicit_address','session_discovery']; errors=[]; rows=[]
for i,arm in enumerate(sched):
 p=root/f'case-{i:02d}'/'result.json'
 if not p.exists(): errors.append(f'missing:{i}'); continue
 r=json.loads(p.read_text()); rows.append(r)
 def req(c,m):
  if not c: errors.append(f'case{i}:{m}')
 req(r.get('task')=='INKSCAPE-ATSPI-SESSION-DISCOVERY-PATH-LIFETIME-20260916-028','task')
 req(r.get('finished') is True,'finished'); req(r.get('arm')==arm,'arm'); req(r.get('registry_owner') is True,'registry')
 req(r.get('address_is_abstract') is True and r.get('address_matches_case_prefix') is True,'abstract_address')
 req(r.get('app_session_getaddress_rc')==0,'session_getaddress')
 req(r.get('reported_address') and r.get('reported_address') in r.get('app_session_getaddress_stdout',''),'session_getaddress_exact')
 req(r.get('app_env_has_at_spi_bus_address') is (arm=='explicit_address'),'mode_env')
 req(r.get('app_bus_resolution')=='unique_private_bus_root_name','resolver')
 req(r.get('pid_attribution_available') is False,'pid_boundary')
 for k,nm in [('A','AI_Target_A'),('B','AI_Target_B')]:
  req(r.get('path_equal',{}).get(k) is True,f'{k}:path_equal')
  req(r.get('old_name_after_reopen',{}).get(k)==nm,f'{k}:old_name')
  for meth in ['props','role','state']:
   req(r.get('probe_closed',{}).get(k,{}).get(meth,{}).get('rc')==0,f'{k}:closed:{meth}')
 req(r.get('final_keymap_empty') is True,'keymap')
if len(rows)!=6: errors.append('row_count')
dec='REJECT_SESSION_DISCOVERY_ALONE_AS_DEFUNCT_CAUSE_SCOPED' if not errors else 'HOLD'
out={'schema':'inkscape-atspi-session-discovery-path-lifetime-audit-v2','pass':not errors,'decision':dec,'cases':len(rows),'errors':errors,'arms':{a:sum(1 for r in rows if r.get('arm')==a) for a in set(sched)}}
print(json.dumps(out,indent=2,sort_keys=True));sys.exit(0 if not errors else 1)
