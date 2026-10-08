import argparse,json,statistics,traceback
from pathlib import Path
from run_session import run_one
from evaluate import evaluate
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--v12',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
rows=[];stop=None
for i,seed in enumerate((192811,192812,192813),1):
 try:
  pid=f'r1-physical-occupancy-{i}';runtime=run_one(a.source,a.v12,a.out/f'session{i}',seed,pid);rows.append(evaluate(runtime,pid))
 except BaseException as exc:
  stop={'session':i,'error':repr(exc),'traceback':traceback.format_exc()};break
widths=[x['censor_width_ms'] for r in rows for x in r['actuations']]
summary={'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,'sessions':rows,'sessions_completed':len(rows),'sessions_pass':sum(r['pass'] for r in rows),'actuations':len(widths),'max_censor_width_ms':max(widths) if widths else None,'median_censor_width_ms':statistics.median(widths) if widths else None,'stop':stop}
if stop: decision='FAIL_FORMAL_RUNTIME_OR_SCHEMA'
elif any(r['v3_physical_promotions'] for r in rows):decision='FAIL_PHYSICAL_EVIDENCE_LAUNDERING'
elif any(r['bridge_status']!='BOUND_MAP01_PHYSICAL_BATCH' for r in rows):
 decision='HOLD_MAP01_PHYSICAL_SAMPLE_NOT_CONFIRMED' if any(r['confirmed_down']<2 or r['confirmed_up']<2 for r in rows) else 'FAIL_MAP01_PHYSICAL_LINEAGE'
elif any(not x['precision_pass'] for r in rows for x in r['actuations']):decision='FAIL_PHYSICAL_PRECISION_TRANSFER'
elif len(rows)==3 and all(r['pass'] for r in rows) and len(widths)==6:decision='PASS_MAP01_V12_PHYSICAL_OCCUPANCY_R1_SCOPED'
else:decision='FAIL_MAP01_PHYSICAL_OCCUPANCY_R1_GATE'
summary['decision']=decision
(a.out/'FORMAL_RESULT.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,sort_keys=True));raise SystemExit(0 if decision.startswith('PASS_') else 1)
