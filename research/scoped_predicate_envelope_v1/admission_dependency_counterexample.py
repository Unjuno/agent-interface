import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
scenarios=['healthy','damage','no_ammo','binding_change','stale','unknown_health']
expected={'healthy':('TASK_SUCCEEDED',2,'method_complete'),'damage':('SAFE_YIELD',1,'health_predicate'),'no_ammo':('SAFE_YIELD',0,'ammo_predicate'),'binding_change':('SAFE_YIELD',0,'binding_changed'),'stale':('SAFE_YIELD',0,'stale'),'unknown_health':('SAFE_YIELD',0,'signal_unknown')}
def fresh(scenario,action,after_first=False,read_extra_ammo=False):
 reads=['health']
 if action=='retreat' or read_extra_ammo:reads.append('ammo')
 reads+=['binding','age'];health=None if scenario=='unknown_health' else (65 if scenario=='damage' and after_first else 73);ammo=0 if scenario=='no_ammo' else 45
 if scenario=='binding_change':return False,'binding_changed',reads
 if scenario=='stale':return False,'stale',reads
 if health is None:return False,'signal_unknown',reads
 if health<67:return False,'health_predicate',reads
 if action=='retreat' and ammo<1:return False,'ammo_predicate',reads
 return True,'ok',reads
def run(scenario,mode):
 actions=0;reads=[]
 for action in ('retreat','strafe'):
  if mode=='interface_only_fail_closed':return ('SAFE_YIELD',actions,'dependency_unavailable'),reads
  if mode=='interface_only_cached':ok,reason,r=True,'ok',[]
  elif mode=='full_fresh':ok,reason,r=fresh(scenario,action,after_first=actions==1,read_extra_ammo=True)
  elif mode=='typed_action':ok,reason,r=fresh(scenario,action,after_first=actions==1,read_extra_ammo=False)
  else:raise ValueError(mode)
  reads+=r
  if not ok:return ('SAFE_YIELD',actions,reason),reads
  actions+=1
 return ('TASK_SUCCEEDED',actions,'method_complete'),reads
rows=[]
for mode in ('full_fresh','interface_only_fail_closed','interface_only_cached','typed_action'):
 for scenario in scenarios:
  outcome,reads=run(scenario,mode);rows.append({'mode':mode,'scenario':scenario,'outcome':outcome,'expected':expected[scenario],'matches_baseline':outcome==expected[scenario],'semantic_reads':reads})
summary={}
for mode in {r['mode'] for r in rows}:
 rs=[r for r in rows if r['mode']==mode];summary[mode]={'matches':sum(r['matches_baseline'] for r in rs),'unsafe_successes':sum(r['outcome'][0]=='TASK_SUCCEEDED' and r['expected'][0]!='TASK_SUCCEEDED' for r in rs),'healthy_false_stop':sum(r['scenario']=='healthy' and r['outcome'][0]!='TASK_SUCCEEDED' for r in rs),'healthy_reads':len(next(r['semantic_reads'] for r in rs if r['scenario']=='healthy'))}
assert summary['full_fresh']['matches']==6 and summary['typed_action']['matches']==6
assert summary['interface_only_cached']['unsafe_successes']==5
assert summary['interface_only_fail_closed']['healthy_false_stop']==1
assert summary['full_fresh']['healthy_reads']==8 and summary['typed_action']['healthy_reads']==7
result={'rows':rows,'summary':summary}
(OUT/'admission_dependency_results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
