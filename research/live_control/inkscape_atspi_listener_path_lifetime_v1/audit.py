import json,sys
from pathlib import Path
root=Path(sys.argv[1]); rows=[]; errors=[]
for i in range(6):
 p=root/f'case-{i:02d}'/'result.json'
 if not p.exists(): errors.append(f'missing case{i}'); continue
 r=json.loads(p.read_text()); rows.append(r); expected='listener' if i%2 else 'no_listener'
 if r.get('task')!='INKSCAPE-ATSPI-LISTENER-PATH-LIFETIME-20260916-026': errors.append(f'case{i} task')
 if r.get('arm')!=expected: errors.append(f'case{i} arm')
 if r.get('finished') is not True: errors.append(f'case{i} unfinished')
 if r.get('registry_owner') is not True: errors.append(f'case{i} registry')
 if r.get('listener_registration_count') != (2 if expected=='listener' else 0): errors.append(f'case{i} listener count')
 if expected=='listener' and any(x.get('registered') is not True for x in r.get('listeners',[])): errors.append(f'case{i} listener registration')
 if r.get('final_keymap_empty') is not True: errors.append(f'case{i} keymap')
 for t in 'AB':
  if r.get('path_equal',{}).get(t) is not True: errors.append(f'case{i} {t} path')
  if r.get('old_name_after_reopen',{}).get(t)!=f'AI_Target_{t}': errors.append(f'case{i} {t} name')
  for q in ('props','role','state'):
   if r.get('probe_closed',{}).get(t,{}).get(q,{}).get('rc')!=0: errors.append(f'case{i} {t} closed {q}')
base=[r for r in rows if r.get('arm')=='no_listener']; cand=[r for r in rows if r.get('arm')=='listener']
def persist(r): return all(r['path_equal'][t] and r['probe_closed'][t]['props']['rc']==0 and r['old_name_after_reopen'][t]==f'AI_Target_{t}' for t in 'AB')
out={'rows':len(rows),'no_listener_n':len(base),'listener_n':len(cand),'no_listener_persist':sum(map(persist,base)),'listener_persist':sum(map(persist,cand)),'errors':errors}
out['decision']='REJECT_LISTENER_REGISTRATION_ALONE_AS_DEFUNCT_CAUSE_SCOPED' if not errors and out['no_listener_persist']==3 and out['listener_persist']==3 else 'HOLD'
out['pass']=not errors
print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(0 if not errors else 1)
