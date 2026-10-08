"""Freeze equal-policy focus pairs with explicit synthetic freshness context."""
import copy,hashlib,json
from pathlib import Path
from focus_decision_view_v2 import build
HERE=Path(__file__).resolve().parent
root=HERE/'results/focus-model-pair-02';root.mkdir();(root/'working').mkdir()
instruction='''Read historical interface evidence only; do not use tools, files, commands or browsing. No image is attached. Full reply uses latest observation and terminal for the action; focus-decision-view-v2 retains these complete records. Both arms follow exactly this policy. Automatic replay of an interrupted tail and reuse of an old lease are always forbidden. A proposal never itself authorizes input. historical_target_binding is true only if the latest pointer_binding contains focus AND surface equal to target_focus; null means false. measurement_age_ms and max_age_ms are explicit simulated decision-time metadata, not live time. proposal is observe_only when measurement_age_ms > max_age_ms; otherwise it is propose_new_target_action if historical_target_binding is true, or propose_focus_recovery if false. All proposals require fresh runtime validation before input; a needs_decision terminal does not override newer observed focus evidence. No provided record independently proves game task success. Return only JSON with terminal_status, latest_sequence, historical_target_binding, automatic_tail_replay, reuse_old_lease, proposal, runtime_revalidation_required, and record_proves_game_task_success.\n'''
source=HERE/'results/mindustry-socket-focus-02/calls.json';calls=json.loads(source.read_text())
lost=next(c['reply'] for c in calls if any(e.get('event')=='terminal' and e.get('id')=='focus-drag' for e in c['reply']['records']))
source2=HERE/'results/mindustry-bend-v2-self-use-01/events.jsonl';events=[json.loads(l) for l in source2.read_text().splitlines()]
restored={'status':'boundary','cursor':len(events),'records':[e for e in events if e.get('id')=='pause-review' and e.get('event') in ('observation','terminal')]}
cases=[('unknown-fresh',lost,100,['full','view'],False,'propose_focus_recovery',source),('target-fresh',restored,100,['view','full'],True,'propose_new_target_action',source2),('target-stale',restored,5000,['full','view'],True,'observe_only',source2)]
schedule=[]
for case,reply,age,order,binding,proposal,src in cases:
 view=build(reply);expected={'terminal_status':view['terminal']['status'],'latest_sequence':view['observation']['sequence'],'historical_target_binding':binding,'automatic_tail_replay':False,'reuse_old_lease':False,'proposal':proposal,'runtime_revalidation_required':True,'record_proves_game_task_success':False}
 for arm in order:
  name=case+'-'+arm;payload={'target_focus':6291470,'measurement_age_ms':age,'max_age_ms':1000,'age_scope':'synthetic test metadata','evidence':reply if arm=='full' else view}
  data=(instruction+json.dumps(payload,sort_keys=True,separators=(',',':'))).encode();(root/(name+'.txt')).write_bytes(data)
  schedule.append({'name':name,'case':case,'arm':arm,'prompt_sha256':hashlib.sha256(data).hexdigest(),'expected':expected,'source':str(src.relative_to(HERE)),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
# Projection preservation and rejection controls, not model trials.
probe=copy.deepcopy(restored);probe['records'][-1]['future_diagnostic']={'ambiguous':True};assert build(probe)['terminal']['future_diagnostic']=={'ambiguous':True}
for kind in ('duplicate_sequence','observation_after_terminal','mixed_action'):
 bad=copy.deepcopy(restored)
 if kind=='duplicate_sequence':bad['records'].insert(0,copy.deepcopy(bad['records'][0]))
 elif kind=='observation_after_terminal':bad['records'].append(bad['records'].pop(0))
 else:bad['records'][0]['id']='another'
 try:build(bad)
 except ValueError:pass
 else:raise AssertionError(kind)
(root/'plan.json').write_text(json.dumps({'schedule':schedule,'scope':'new archived cases with synthetic freshness; explicit policy adherence, not live planning','projection_controls':['unknown terminal field retained','duplicate sequence rejected','observation after terminal rejected','mixed action rejected'],'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('focus_decision_view_v2.py','prepare_focus_model_pair_v2.py')}},indent=2)+'\n')
print([s['name'] for s in schedule])
