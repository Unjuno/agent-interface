import json,sys
from pathlib import Path
root=Path(sys.argv[1]); rows=[]; errors=[]
for i in range(6):
 p=root/f'case-{i:02d}'/'result.json'
 if not p.exists(): errors.append(f'missing {p}'); continue
 r=json.loads(p.read_text()); rows.append(r)
 expected='registry' if i%2 else 'no_registry'
 if r.get('task')!='INKSCAPE-ATSPI-REGISTRY-PATH-LIFETIME-20260916-025': errors.append(f'case{i} task')
 if r.get('arm')!=expected: errors.append(f'case{i} arm {r.get("arm")} expected {expected}')
 if r.get('finished') is not True: errors.append(f'case{i} unfinished')
 if r.get('registry_owner') is not (expected=='registry'): errors.append(f'case{i} registry owner')
 if r.get('final_keymap_empty') is not True: errors.append(f'case{i} keymap')
 for t in 'AB':
  if not r.get('first_paths',{}).get(t) or not r.get('second_paths',{}).get(t): errors.append(f'case{i} {t} missing path')
  if r.get('path_equal',{}).get(t) is not True: errors.append(f'case{i} {t} path changed')
  if r.get('old_name_after_reopen',{}).get(t)!=f'AI_Target_{t}': errors.append(f'case{i} {t} old path name after reopen')
  for q in ('props','role','state'):
   if r.get('probe_closed',{}).get(t,{}).get(q,{}).get('rc')!=0: errors.append(f'case{i} {t} closed {q}')
no=[r for r in rows if r.get('arm')=='no_registry']; yes=[r for r in rows if r.get('arm')=='registry']
summary={'rows':len(rows),'no_registry_n':len(no),'registry_n':len(yes),'no_registry_persist':sum(all(r['path_equal'][t] and r['probe_closed'][t]['props']['rc']==0 for t in 'AB') for r in no),'registry_persist':sum(all(r['path_equal'][t] and r['probe_closed'][t]['props']['rc']==0 for t in 'AB') for r in yes),'errors':errors}
summary['decision']='REJECT_REGISTRY_ALONE_AS_DEFUNCT_CAUSE_SCOPED' if not errors and summary['no_registry_persist']==3 and summary['registry_persist']==3 else 'HOLD'
summary['pass']=not errors
print(json.dumps(summary,indent=2,sort_keys=True))
raise SystemExit(0 if not errors else 1)
