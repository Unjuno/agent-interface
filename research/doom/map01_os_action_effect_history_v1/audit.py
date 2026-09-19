from pathlib import Path
import argparse,json,hashlib
import numpy as np
from PIL import Image

def desc(p):
 a=np.asarray(Image.open(p).convert('RGB'));im=Image.fromarray(a[20:340,70:570]).convert('L').resize((32,20),Image.Resampling.BILINEAR);return np.asarray(im,dtype=np.float32).ravel()/255.0,hashlib.sha256(a.tobytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--plan',type=Path,required=True);p.add_argument('--calibration',type=Path,required=True);p.add_argument('--out',type=Path);a=p.parse_args();plan=json.loads(a.plan.read_text());cal=np.load(a.calibration);errors=[];rows=[]
 for c in plan['cases']:
  d=a.root/f"case-{c['case']:02d}"
  if not (d/'score.json').exists():errors.append(f"missing_case_{c['case']}");continue
  s=json.loads((d/'score.json').read_text());t=json.loads((d/'controller'/'trace.json').read_text());e=json.loads((d/'evidence.json').read_text());pd,ph=desc(d/'previous.png');cd,ch=desc(d/'current.png')
  if ph!=e['previous_rgb_sha256'] or ch!=e['current_rgb_sha256']:errors.append(f"hash_{c['case']}")
  feat=cd if c['mode']=='current' else cd-pd;cents=[cal['current_open'],cal['current_close']] if c['mode']=='current' else [cal['history_open'],cal['history_close']];pred=int(np.argmin([np.mean((feat-x)**2) for x in cents]))
  if pred!=s.get('predicted_label') or pred!=t.get('predicted_label'):errors.append(f"prediction_{c['case']}")
  sem=pred==(0 if c['state']=='opening' else 1)
  if sem!=s.get('semantic_action_correct'):errors.append(f"semantic_{c['case']}")
  rels=[r for r in s.get('setup_owner_records',[]) if r.get('event')=='owner_release']+[r for r in t.get('owner_records',[]) if r.get('event')=='owner_release']
  release_ok=all(r.get('verified') and not r.get('keys_down') and not r.get('buttons_down') for r in rels)
  if not release_ok:errors.append(f"release_{c['case']}")
  rows.append({'case':c,'score':s,'trace':t,'cd':cd,'pd':pd,'pred':pred,'semantic':sem,'release_ok':release_ok})
 alias=[]
 for seed in plan['formal_seeds']:
  for mode in ['current','history']:
   o=next((r for r in rows if r['case']['seed']==seed and r['case']['state']=='opening' and r['case']['mode']==mode),None);cl=next((r for r in rows if r['case']['seed']==seed and r['case']['state']=='closing' and r['case']['mode']==mode),None)
   if o and cl:
    rmse=float(np.sqrt(np.mean((o['cd']-cl['cd'])**2)));alias.append({'seed':seed,'mode':mode,'rmse':rmse,'aliased':rmse<=plan['current_alias_rmse_threshold']})
 counts={}
 for mode in ['current','history']:
  rr=[r for r in rows if r['case']['mode']==mode];counts[mode]={'cases':len(rr),'semantic_correct':sum(r['semantic'] for r in rr),'transit_success':sum(bool(r['score'].get('transit_success')) for r in rr),'condition_success':sum(bool(r['score'].get('condition_success')) for r in rr),'stale':sum((r['score'].get('observation_age_ns_at_start') or 10**18)>plan['observation_max_age_ns'] for r in rr),'release_failures':sum(not r['release_ok'] for r in rr)}
 exposure=sum(x['aliased'] for x in alias);hard=len(rows)==16 and counts['history']['semantic_correct']>=8 and counts['history']['transit_success']>=8 and counts['history']['release_failures']==0 and counts['history']['stale']==0 and exposure>=plan['hard_gates']['aliased_state_pairs_min'];diff=counts['history']['semantic_correct']-counts['current']['semantic_correct']
 if exposure<plan['hard_gates']['aliased_state_pairs_min']:decision='UNCERTAIN_EXPOSURE'
 elif not hard or counts['history']['semantic_correct']<counts['current']['semantic_correct']:decision='FAIL_HISTORY_TRANSFER'
 elif diff>=2:decision='PASS_HISTORY_TRANSFER'
 else:decision='HOLD_NO_INCREMENTAL_EFFECT'
 out={'schema':'agent-interface/map01-os-action-effect-history-audit-v1','decision':decision,'errors':errors,'counts':counts,'semantic_correct_difference_history_minus_current':diff,'alias_pairs':alias,'aliased_pairs':exposure,'hard_gate_pass':hard and not errors}
 if errors:out['decision']='FAIL_AUDIT_INTEGRITY'
 text=json.dumps(out,indent=2)+'\n';print(text,end='');
 if a.out:a.out.write_text(text)
 raise SystemExit(0 if out['decision'] in ['PASS_HISTORY_TRANSFER','HOLD_NO_INCREMENTAL_EFFECT'] else 2)
if __name__=='__main__':main()
