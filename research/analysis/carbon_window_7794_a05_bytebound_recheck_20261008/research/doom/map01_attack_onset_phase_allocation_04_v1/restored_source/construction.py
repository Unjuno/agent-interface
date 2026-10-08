from pathlib import Path
import argparse,json,traceback
from run_case import run_case,derive
S=[('construction-immediate','IMMEDIATE'),('construction-preroll','ONE_WINDOW_PREROLL')]
def clean(r):
 p=r.get('physical');return r['physical_down_count']==1 and r['physical_up_count']==1 and isinstance(p,dict) and p.get('confirmed') is True and p.get('lineage_ok') is True and p['release'].get('owner_transition_verified') is True and p['release'].get('owned_keycodes_after_batch')==[]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--v12',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
 rows=[];stop=None
 for cid,arm in S:
  try:
   rt=run_case(a.source,a.v12,a.out/cid,arm,cid);rows.append(derive(rt,arm,cid))
  except BaseException as e:stop={'case':cid,'error':repr(e),'traceback':traceback.format_exc()};break
 eligible=stop is None and len(rows)==2 and all(clean(r) for r in rows) and [r['pre_roll_ms'] for r in rows]==[0,600]
 out={'schema':'map01-attack-onset-phase-construction-v1','excluded':True,'rows':rows,'stop':stop,'eligible_for_freeze':eligible}
 (a.out/'CONSTRUCTION_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps({'eligible':eligible,'effects':[len(r['bound_task_effects']) for r in rows],'scores':[r['score'] for r in rows]},default=str));return 0 if eligible else 1
if __name__=='__main__':raise SystemExit(main())
