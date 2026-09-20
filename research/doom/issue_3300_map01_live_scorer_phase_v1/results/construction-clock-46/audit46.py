from __future__ import annotations
import json, statistics, sys
from pathlib import Path

rows=[json.loads(x) for x in Path(sys.argv[1]).read_text().splitlines() if x]
reports=[]; errors=[]
for r in rows:
    passive=[x['tic'] for x in r.get('passive_reads',[])]
    records=r.get('tic_entry_records',[]); viz=[x[3] for x in records]
    before=[e.get('result') for e in r.get('scorer_before_action',{}).get('getters',[]) if e['name']=='get_episode_time']
    after=[e.get('result') for e in r.get('scorer_after_action',{}).get('getters',[]) if e['name']=='get_episode_time']
    checks={
      'setup':r.get('setup_status')=='ok',
      'passive_api_stale':len(passive)>=100 and set(passive)=={1},
      'pre_action_scorer_stale':before==[1,1],
      'one_empty_action_returned':r.get('advance_action_status')=='returned',
      'api_caught_up_after_action':r.get('api_tic_after_action',1)>1,
      'scorer_caught_up_after_action':len(after)==2 and after[0]>1 and after[0]==after[1],
      'source_viz_contiguous':len(viz)>=2 and all(b-a==1 for a,b in zip(viz,viz[1:])),
      'cleanup':r.get('cleanup',{}).get('game_closed') is True,
    }
    for name,ok in checks.items():
      if not ok: errors.append({'index':r.get('index'),'check':name})
    periods=[b[1]-a[1] for a,b in zip(records,records[1:])]
    reports.append({'index':r.get('index'),'passive_reads':len(passive),'passive_api_tics':sorted(set(passive)),
      'api_tic_before_action':r.get('api_tic_before_action'),'api_tic_after_action':r.get('api_tic_after_action'),
      'scorer_tics_before':before,'scorer_tics_after':after,
      'advance_action_ns':r.get('advance_action_end_ns',0)-r.get('advance_action_start_ns',0),
      'engine_records':len(records),'engine_viz_tic_range':[min(viz),max(viz)] if viz else None,
      'engine_median_hz':1e9/statistics.median(periods) if periods else None,
      'cleanup':r.get('cleanup'),'checks':checks})
result={'schema':'issue3453-construction-clock46-independent-audit-v1','input':str(sys.argv[1]),'rows':len(rows),'errors':errors,
 'decision':'PASS_CONSTRUCTION_ONLY_ACTION_BOUNDARY_CATCHUP' if rows and not errors else 'FAIL_AUDIT',
 'formal_allocation':False,'reports':reports,
 'limitations':['The empty advance_action call is an explicit intervention and is not part of the passive target condition.',
 'Source clock sampling is instrumented; function-entry latency and perturbation are unbounded.',
 'This does not reconstruct the passive scorer phase/span distribution or authorize formal collection.']}
print(json.dumps(result,indent=2,sort_keys=True)); raise SystemExit(bool(errors))
