#!/usr/bin/env python3
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); sched=json.loads((Path(__file__).resolve().parent/'schedule.json').read_text()); errors=[]; rows=[]
def path_ok(r):
    if not r.get('finished') or not r.get('registry_owner') or not r.get('final_keymap_empty'): return False
    for k,nm in [('A','AI_Target_A'),('B','AI_Target_B')]:
        if r.get('path_equal',{}).get(k) is not True:return False
        if r.get('old_name_after_reopen',{}).get(k)!=nm:return False
        for meth in ['props','role','state']:
            if r.get('probe_closed',{}).get(k,{}).get(meth,{}).get('rc')!=0:return False
    return True
for i,arm in enumerate(sched):
    p=root/f'case-{i:02d}'/'result.json'
    if not p.exists(): errors.append(f'missing:{i}'); continue
    r=json.loads(p.read_text());rows.append(r)
    def req(c,m):
        if not c: errors.append(f'case{i}:{m}')
    req(r.get('task')=='INKSCAPE-ATSPI-DISCOVERY-LISTENER-INTERACTION-20260916-030','task')
    req(r.get('arm')==arm,'arm');req(r.get('finished') is True,'finished');req(r.get('registry_owner') is True,'registry')
    session=arm.startswith('session_'); listener=arm.endswith('_listener') and not arm.endswith('_no_listener')
    req(r.get('app_env_has_at_spi_bus_address') is (not session),'env_mode')
    req(r.get('app_session_getaddress_rc')==0,'getaddress_rc')
    req(r.get('reported_address') and r.get('reported_address') in r.get('app_session_getaddress_stdout',''),'getaddress_exact')
    req(r.get('listener_registration_count')==(2 if listener else 0),'listener_count')
    if listener:
        req(len(r.get('listeners',[]))==2 and all(x.get('registered') for x in r.get('listeners',[])),'listeners_registered')
    req(r.get('address_is_abstract') is True and r.get('address_matches_case_prefix') is True,'address')
    req(r.get('app_bus_resolution')=='unique_private_bus_root_name','resolver');req(r.get('pid_attribution_available') is False,'pid_boundary')
    req(path_ok(r),'path_gate')
if len(rows)!=len(sched):errors.append('row_count')
by={a:[r for r in rows if r.get('arm')==a] for a in sorted(set(sched))}
all_pass=not errors and all(len(v)==3 and all(path_ok(r) for r in v) for v in by.values())
others=['explicit_no_listener','explicit_listener','session_no_listener']
interaction=(len(by.get('session_listener',[]))==3 and all(not path_ok(r) for r in by['session_listener']) and all(len(by.get(a,[]))==3 and all(path_ok(r) for r in by[a]) for a in others))
if all_pass:dec='REJECT_SESSION_DISCOVERY_X_LISTENER_INTERACTION_AS_DEFUNCT_CAUSE_SCOPED'
elif interaction:dec='SESSION_DISCOVERY_X_LISTENER_INTERACTION_DEFUNCT_OBSERVED_SCOPED'
else:dec='HOLD'
out={'schema':'atspi-discovery-listener-interaction-audit-v1','pass':not errors,'decision':dec,'cases':len(rows),'errors':errors,'arm_path_pass_counts':{a:sum(path_ok(r) for r in v) for a,v in by.items()},'arm_counts':{a:len(v) for a,v in by.items()}}
print(json.dumps(out,indent=2,sort_keys=True));sys.exit(0 if not errors else 1)
