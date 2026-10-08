from __future__ import annotations
import argparse,json,traceback
from pathlib import Path
from run_case import run_case,derive
SCHEDULE=[
 ('p1-immediate','IMMEDIATE'),('p1-preroll','ONE_WINDOW_PREROLL'),
 ('p2-preroll','ONE_WINDOW_PREROLL'),('p2-immediate','IMMEDIATE'),
 ('p3-immediate','IMMEDIATE'),('p3-preroll','ONE_WINDOW_PREROLL'),
 ('p4-preroll','ONE_WINDOW_PREROLL'),('p4-immediate','IMMEDIATE')]
def clean(r):
 p=r.get('physical');return r['physical_down_count']==1 and r['physical_up_count']==1 and isinstance(p,dict) and p.get('confirmed') is True and p.get('lineage_ok') is True and p['release'].get('owner_transition_verified') is True and p['release'].get('owned_keycodes_after_batch')==[] and r.get('seed')==992600
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--v12',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
 rows=[];stop=None
 for cid,arm in SCHEDULE:
  try:
   rt=run_case(a.source,a.v12,a.out/cid,arm,cid,992600);rows.append(derive(rt,arm,cid))
  except BaseException as e:stop={'case_id':cid,'arm':arm,'error':repr(e),'traceback':traceback.format_exc()};break
 physical_clean=len(rows)==8 and all(clean(r) for r in rows)
 pairs=[]
 for n in range(1,5):
  a1=next((r for r in rows if r['case_id']==f'p{n}-immediate'),None);b=next((r for r in rows if r['case_id']==f'p{n}-preroll'),None)
  if a1 and b:
   ie=bool(a1['bound_task_effects']);pe=bool(b['bound_task_effects']);pairs.append({'pair':n,'immediate_effect':ie,'preroll_effect':pe,'different':ie!=pe,'immediate_count':len(a1['bound_task_effects']),'preroll_count':len(b['bound_task_effects'])})
 diff=sum(p['different'] for p in pairs)
 if stop:decision='FAIL_FORMAL_RUNTIME_OR_SCHEMA'
 elif len(rows)!=8:decision='FAIL_FORMAL_DENOMINATOR'
 elif not physical_clean:decision='FAIL_MAP01_V12_PHYSICAL_LINEAGE'
 elif any(len(r['bound_task_effects'])>1 for r in rows):decision='FAIL_DUPLICATE_TASK_EFFECT'
 elif diff>=3:decision='PASS_ATTACK_ONSET_PHASE_DISCRIMINATES_SCOPED'
 else:decision='HOLD_ATTACK_ONSET_PHASE_NOT_DISCRIMINATING'
 out={'schema':'map01-attack-onset-phase-formal-v1','decision':decision,'formal_invocations':1,'reruns':0,'replacements':0,'tuning_after_freeze':0,'rows':rows,'pairs':pairs,'different_pairs':diff,'physical_clean':physical_clean,'stop':stop}
 (a.out/'FORMAL_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps({'decision':decision,'different_pairs':diff,'pairs':pairs,'physical_clean':physical_clean,'rows':len(rows)},sort_keys=True));return 0 if decision.startswith(('PASS_','HOLD_')) else 1
if __name__=='__main__':raise SystemExit(main())
