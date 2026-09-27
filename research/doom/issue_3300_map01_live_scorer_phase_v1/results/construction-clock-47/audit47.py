from __future__ import annotations
import json,sys
from pathlib import Path
rows=[json.loads(x) for x in Path(sys.argv[1]).read_text().splitlines() if x]
errors=[]; reports=[]
for r in rows:
 p=[x['tic'] for x in r.get('passive_reads',[])]; rec=r.get('tic_entry_records',[]); v=[x[3] for x in rec]
 b=[e.get('result') for e in r.get('scorer_before_zero',{}).get('getters',[]) if e['name']=='get_episode_time']
 a=[e.get('result') for e in r.get('scorer_after_zero',{}).get('getters',[]) if e['name']=='get_episode_time']
 c={'setup':r.get('setup_status')=='ok','passive_api_stays_1':len(p)>=100 and set(p)=={1},'pre_scorer_stays_1':b==[1,1],
    'zero_call_returns':r.get('zero_call_status')=='returned','zero_call_does_not_refresh_api':r.get('api_tic_after_zero')==1,
    'zero_call_does_not_refresh_scorer':a==[1,1],'engine_trace_contiguous':len(v)>=2 and all(y-x==1 for x,y in zip(v,v[1:])),
    'cleanup':r.get('cleanup',{}).get('game_closed') is True}
 for k,ok in c.items():
  if not ok: errors.append({'index':r.get('index'),'check':k})
 reports.append({'index':r.get('index'),'passive_reads':len(p),'passive_tics':sorted(set(p)),
  'scorer_tics_before':b,'zero_status':r.get('zero_call_status'),'zero_duration_ns':r.get('zero_call_end_ns',0)-r.get('zero_call_start_ns',0),
  'api_tic_after_zero':r.get('api_tic_after_zero'),'scorer_tics_after':a,'engine_trace_count':len(v),
  'engine_trace_viz_range':[min(v),max(v)] if v else None,'checks':c,'cleanup':r.get('cleanup')})
out={'schema':'issue3453-construction-clock47-independent-audit-v1','input':str(sys.argv[1]),'rows':len(rows),'errors':errors,
 'decision':'HOLD_ZERO_TIC_ACTION_DID_NOT_REFRESH_SNAPSHOT' if rows and not errors else 'FAIL_AUDIT','formal_allocation':False,'reports':reports,
 'limitations':['The zero-tic API call is still an intervention.','Internal source-clock instrumentation is unbounded/perturbative.',
 'This rejects only the zero-tic refresh hypothesis and does not identify passive scorer phase or authorize formal allocation.']}
print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(bool(errors))
