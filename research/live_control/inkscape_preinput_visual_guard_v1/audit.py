import argparse,json,hashlib
from pathlib import Path

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit(root,expected=20):
 root=Path(root); rows=[(p,json.loads(p.read_text())) for p in sorted(root.glob('case-*/result.json'))]
 errors=[]; c={'stable':0,'switch':0,'stable_admit_correct':0,'switch_stopped':0,'switch_false_admit':0,'release_ok':0,'revalidation_ok':0}
 if len(rows)!=expected: errors.append(f'row_count:{len(rows)}')
 for p,r in rows:
  ctx=r['context']; c[ctx]+=1; c['revalidation_ok']+=int(r['revalidation']['success']); c['release_ok']+=int(r['all_relevant_keys_empty'] and r['button_empty'])
  if r['policy']!='guard': errors.append(f'{p.parent.name}:policy')
  if ctx=='stable':
   ok=r['decision']=='ADMIT' and r['effect_input_sent'] and r['delta']['A']>.5 and abs(r['delta']['B'])<.5
   c['stable_admit_correct']+=int(ok)
   if not ok: errors.append(f'{p.parent.name}:stable:{r["decision"]}:{r["delta"]}')
  else:
   stop=r['decision']=='DEPENDENCY_UNAVAILABLE' and not r['effect_input_sent'] and abs(r['delta']['A'])<.5 and abs(r['delta']['B'])<.5
   c['switch_stopped']+=int(stop)
   false=r['decision']=='ADMIT' and r['effect_input_sent'] and abs(r['delta']['A'])<.5 and r['delta']['B']>.5
   c['switch_false_admit']+=int(false)
   if not (stop or false): errors.append(f'{p.parent.name}:switch_unclassified:{r["decision"]}:{r["delta"]}')
 gates={'stable_10_of_10':c['stable']==10 and c['stable_admit_correct']==10,'revalidation_20_of_20':c['revalidation_ok']==20,'release_20_of_20':c['release_ok']==20,'switch_guard_perfect':c['switch']==10 and c['switch_stopped']==10 and c['switch_false_admit']==0}
 decision='PASS_VISUAL_SELECTION_GUARD_SCOPED' if all(gates.values()) and not errors else ('REJECT_VISUAL_SELECTION_GUARD' if c['switch_false_admit']>0 and gates['stable_10_of_10'] and gates['revalidation_20_of_20'] and gates['release_20_of_20'] and not errors else 'HOLD_OR_INVALID')
 return {'schema':'inkscape-preinput-visual-guard-audit-v1','decision':decision,'counts':c,'gates':gates,'errors':errors,'passed_integrity':not errors and c['stable']==10 and c['switch']==10 and c['revalidation_ok']==20 and c['release_ok']==20,'result_sha256':{str(p.relative_to(root)):sha(p) for p,_ in rows}}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('root');a=ap.parse_args();o=audit(a.root);print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(0 if o['passed_integrity'] else 1)
