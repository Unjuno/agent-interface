from pathlib import Path
import json
r=Path(__file__).resolve().parent/'controller-visual-04'
report=json.loads((r/'episode/report.json').read_bytes())
host=[json.loads(x) for x in (r/'host.stdout.jsonl').read_bytes().splitlines()]
usage={}
for row in host:
 if row.get('method')=='thread/tokenUsage/updated':
  p=row['params'];usage[p['turnId']]=p['tokenUsage']
turns=[]
for d in report['decisions']:
 t=d['final_action_admission']['planner_terminal'];u=usage.get(t['turn_id'])
 turns.append({'iteration':d['iteration'],'turn_id':t['turn_id'],'status':t['status'],'id_bound_usage':u,'report_has_usage':d.get('usage') is not None,'reported_usage_matches_bound':d.get('usage')==u})
rows=[json.loads(x) for x in (r/'episode/runtime/events.jsonl').read_bytes().splitlines()]
assert rows==[json.loads(x) for x in (r/'episode/runtime/delivered.jsonl').read_bytes().splitlines()]
cancel=next(x for x in rows if x.get('event')=='terminal' and x.get('id')=='cover-1')
assert cancel['status']=='cancelled' and cancel['release']['verified'] and cancel['release']['keys_down']==[]
accepted=next(x for x in rows if x.get('event')=='accepted' and x.get('id')=='plan-3-primary-0-0')
terminal=next(x for x in rows if x.get('event')=='terminal' and x.get('id')=='plan-3-primary-0-0')
assert accepted['emit_ns']>cancel['emit_ns'] and terminal['status']=='completed' and terminal['release']['verified']
refused=report['decisions'][2]['final_action_admission'];assert refused['executor_admission'] is None
assert not any(x.get('event')=='accepted' and x.get('id','').startswith('plan-2-') for x in rows)
result={'disposition':'PASS_POST_REFUSAL_READMISSION_COMPOSITION_SCOPED; HOLD_USEFUL_RECOVERY','turn_usage':turns,'known_completed_input':sum(t['id_bound_usage']['last']['inputTokens'] for t in turns if t['id_bound_usage']),'known_completed_output':sum(t['id_bound_usage']['last']['outputTokens'] for t in turns if t['id_bound_usage']),'unknown_usage_turns':[t['turn_id'] for t in turns if t['id_bound_usage'] is None],'cancelled_cover_terminal':cancel,'later_accepted':accepted,'later_terminal':terminal,'scope':'identity/time joins only; zero independent useful events; no causal/task/physical per-key timing certificate'}
(r/'SAVED_READMISSION_AUDIT.json').write_bytes(json.dumps(result,indent=2).encode())
print(json.dumps({'turn_usage':turns,'known_input':result['known_completed_input'],'known_output':result['known_completed_output'],'cancel_terminal_ns':cancel['emit_ns'],'accepted_ns':accepted['emit_ns'],'terminal_status':terminal['status']}))
