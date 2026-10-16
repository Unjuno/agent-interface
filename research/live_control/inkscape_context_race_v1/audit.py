import argparse,json,hashlib
from pathlib import Path
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit(root,expected=20):
 root=Path(root);rows=[(p,json.loads(p.read_text())) for p in sorted(root.glob('case-*/result.json'))];errors=[];c={k:0 for k in ['stable','switch','stable_correct','switch_wrong_target','release_ok','revalidation_ok']}
 if len(rows)!=expected:errors.append(f'row_count:{len(rows)}')
 for p,r in rows:
  a=r['arm'];c[a]+=1;c['revalidation_ok']+=int(r['revalidation']['success']);c['release_ok']+=int(r['all_relevant_keys_empty'] and r['button_empty']);d=r['delta']
  if a=='stable':
   ok=d['A']>.5 and abs(d['B'])<.5;c['stable_correct']+=int(ok)
   if not ok:errors.append(f'{p.parent.name}:stable:{d}')
  else:
   ok=abs(d['A'])<.5 and d['B']>.5;c['switch_wrong_target']+=int(ok)
   if not ok:errors.append(f'{p.parent.name}:switch:{d}')
 g={'stable_10_of_10':c['stable']==10 and c['stable_correct']==10,'switch_wrong_target_10_of_10':c['switch']==10 and c['switch_wrong_target']==10,'revalidation_20_of_20':c['revalidation_ok']==20,'release_20_of_20':c['release_ok']==20};return {'schema':'inkscape-context-race-audit-v1','passed':all(g.values()) and not errors,'counts':c,'gates':g,'errors':errors,'result_sha256':{str(p.relative_to(root)):sha(p) for p,_ in rows}}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('root');a=ap.parse_args();o=audit(a.root);print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(0 if o['passed'] else 1)
