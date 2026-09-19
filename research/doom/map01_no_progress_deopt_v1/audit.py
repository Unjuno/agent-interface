from pathlib import Path
import argparse,json,math,statistics
import numpy as np
MOTION_THRESHOLD=0.055

def release_ok(rows):
    rel=[r for r in rows if r.get('event')=='owner_release']
    return bool(rel) and all(r.get('verified') and not r.get('keys_down') and not r.get('buttons_down') for r in rel)
def main():
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--plan',type=Path,required=True);p.add_argument('--out',type=Path);a=p.parse_args();plan=json.loads(a.plan.read_text());errs=[];rows=[]
 for c in plan['cases']:
  d=a.root/f"case-{c['case']:02d}";req=['score.json','trajectory.json','owner-records.json','descriptors.npz']
  miss=[x for x in req if not (d/x).exists()]
  if miss:errs.extend([f"missing_{c['case']}_{x}" for x in miss]);continue
  s=json.loads((d/'score.json').read_text());tr=json.loads((d/'trajectory.json').read_text());own=json.loads((d/'owner-records.json').read_text());z=np.load(d/'descriptors.npz');b=z['before'];af=z['after']
  if s.get('arm')!=c['arm'] or s.get('seed')!=c['seed'] or s.get('nomonsters') is not True:errs.append(f"identity_{c['case']}")
  if len(tr)!=len(b) or len(tr)!=len(af) or len(tr)!=s.get('decisions'):errs.append(f"length_{c['case']}")
  np_events=0;repeated=0;esc=0
  for i,r in enumerate(tr):
   mse=float(np.mean((af[i]-b[i])**2));npflag=mse<MOTION_THRESHOLD
   if abs(mse-r['motion_mse'])>1e-6 or npflag!=r['no_progress']:errs.append(f"motion_{c['case']}_{i}")
   if npflag:np_events+=1
   rep=bool(r.get('repair') and r['repair'].get('repeated'));repeated+=rep
   if c['arm']=='repeat_small' and r.get('repair') and r['repair'].get('pulses')!=1:errs.append(f"baseline_repair_{c['case']}_{i}")
   if c['arm']=='escalate' and rep:
    if r['repair'].get('pulses')!=6:errs.append(f"candidate_escalation_{c['case']}_{i}")
    esc+=1
  rel=release_ok(own)
  if not rel:errs.append(f"release_{c['case']}")
  cells={(math.floor(r['x']/64),math.floor(r['y']/64)) for r in tr};path=sum(math.hypot(tr[i]['x']-tr[i-1]['x'],tr[i]['y']-tr[i-1]['y']) for i in range(1,len(tr)))
  row={'case':c,'coverage64':len(cells),'revisit_fraction':1-len(cells)/max(1,len(tr)),'path_length':path,'no_progress_events':np_events,'repeated_no_progress':repeated,'deopt_escalations':esc,'map_exit':bool(s.get('map_exit')),'player_dead':bool(s.get('player_dead')),'release_ok':rel};rows.append(row)
 pair=[]
 for seed in plan['formal_seeds']:
  base=next((r for r in rows if r['case']['seed']==seed and r['case']['arm']=='repeat_small'),None);cand=next((r for r in rows if r['case']['seed']==seed and r['case']['arm']=='escalate'),None)
  if not base or not cand:errs.append(f"pair_missing_{seed}");continue
  pair.append({'seed':seed,'baseline_coverage':base['coverage64'],'candidate_coverage':cand['coverage64'],'coverage_delta':cand['coverage64']-base['coverage64'],'baseline_revisit':base['revisit_fraction'],'candidate_revisit':cand['revisit_fraction'],'revisit_improved':cand['revisit_fraction']<=base['revisit_fraction']})
 cand=[r for r in rows if r['case']['arm']=='escalate'];allrows=rows;deltas=[r['coverage_delta'] for r in pair];med=statistics.median(deltas) if deltas else None
 exposure=sum(r['deopt_escalations']>=1 for r in cand);covwins=sum(r['coverage_delta']>=0 for r in pair);revwins=sum(r['revisit_improved'] for r in pair);safe=all(r['release_ok'] and not r['player_dead'] for r in allrows)
 if not safe or (med is not None and med<0):decision='FAIL_DEOPT_NAVIGATION'
 elif exposure>=3 and covwins>=3 and med is not None and med>=2 and revwins>=3:decision='PASS_BOUNDED_DEOPT_COVERAGE'
 else:decision='HOLD_INSUFFICIENT_NAVIGATION_EVIDENCE'
 out={'schema':'agent-interface/map01-no-progress-deopt-audit-v1','status':'PASS_AUDIT' if not errs else 'FAIL_AUDIT_INTEGRITY','scientific_decision':decision,'errors':errs,'exposure_runs':exposure,'coverage_nonworse_pairs':covwins,'revisit_nonworse_pairs':revwins,'paired_median_coverage_delta':med,'pairs':pair,'rows':rows}
 txt=json.dumps(out,indent=2,sort_keys=True)+'\n';print(txt,end='');
 if a.out:a.out.write_text(txt)
 raise SystemExit(0 if not errs else 2)
if __name__=='__main__':main()
