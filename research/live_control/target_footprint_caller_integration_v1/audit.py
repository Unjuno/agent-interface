from pathlib import Path
import json,statistics,sys
root=Path(sys.argv[1])
rows=[]
for d in sorted(p for p in root.iterdir() if p.is_dir() and (p/'score.json').exists()):
 s=json.loads((d/'score.json').read_text()); c=json.loads((d/'caller-result.json').read_text())
 rec=[]
 for key in ['reference_owner_records','setup_owner_records','controller_owner_records']:rec.extend(s.get(key,[]) or [])
 rel=[r for r in rec if isinstance(r,dict) and 'verified' in r]
 rows.append(dict(case=d.name,scenario=s['scenario'],mode=s['mode'],independent_success=s['independent_success'],expected_edit=s['expected_edit'],bytes_unchanged=s['bytes_unchanged'],task_input_count=s['task_input_count'],caller_outcome=s['caller_outcome'],caller_reason=s['caller_reason'],repair_path=s['repair_path'],attempted_model_calls=s['attempted_model_calls'],wrong_target_deleted=s['wrong_target_deleted'],race_mutation_exposed=s.get('race_mutation_exposed',False),release_records=len(rel),release_failures=sum(1 for r in rel if not r.get('verified') or r.get('keys_down') or r.get('buttons_down')),phase_timings=c['phase_timings']))
assert len(rows)==14 and all(r['independent_success'] for r in rows)
assert all(r['attempted_model_calls']==0 and not r['wrong_target_deleted'] and r['release_failures']==0 for r in rows)
for mode in ['baseline','candidate']:
 r=next(x for x in rows if x['scenario']=='stable_static' and x['mode']==mode);assert r['caller_outcome']=='TASK_SUCCEEDED' and r['repair_path']=='none'
for sc in ['stable_pan','moved_decoy']:
 b=next(x for x in rows if x['scenario']==sc and x['mode']=='baseline');c=next(x for x in rows if x['scenario']==sc and x['mode']=='candidate')
 assert b['caller_outcome']=='SAFE_STOP' and b['task_input_count']==0
 assert c['caller_outcome']=='TASK_SUCCEEDED' and c['repair_path']=='local' and c['task_input_count']==3
for sc in ['replaced_square','missing','duplicate']:
 for mode in ['baseline','candidate']:
  r=next(x for x in rows if x['scenario']==sc and x['mode']==mode);assert r['caller_outcome']=='SAFE_STOP' and r['task_input_count']==0 and r['bytes_unchanged']
r=next(x for x in rows if x['scenario']=='post_repair_pan' and x['mode']=='candidate');assert r['race_mutation_exposed'] and r['repair_path']=='local' and r['caller_outcome']=='SAFE_STOP' and r['caller_reason']=='association_changed' and r['task_input_count']==0
local=[p['elapsed_ns']/1e6 for r in rows for p in r['phase_timings'] if p['stage']=='local_repair'];final=[p['elapsed_ns']/1e6 for r in rows for p in r['phase_timings'] if p['stage']=='final_revalidate']
out={'schema':'target-footprint-adaptive-caller-integration-v4-audit','decision':'PASS_INTEGRATION_MECHANICS','cases':14,'condition_correct':14,'wrong_target_edits':0,'model_calls':0,'release_failures':0,'candidate_local_successes':2,'candidate_local_safe_stops':1,'local_repair_stage_ms':{'n':len(local),'median':statistics.median(local),'range':[min(local),max(local)]},'final_revalidate_stage_ms':{'n':len(final),'median':statistics.median(final),'range':[min(final),max(final)]}}
print(json.dumps(out,indent=2,sort_keys=True))
