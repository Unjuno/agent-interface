"""Freeze paired model prompts before invocation; known focus records, text only."""
import hashlib,json
from pathlib import Path
from focus_decision_view_v1 import build
HERE=Path(__file__).resolve().parent
root=HERE/'results/focus-model-pair-01';root.mkdir();(root/'working').mkdir()
instruction='''Read the following historical interface evidence. Do not use tools, files, commands or browsing. No image is attached. The user's intended window is target_focus. The attempted refocus, if present, was intentional; task success is a separate question. A focus-decision-view-v1 is a lossy projection with its latest matching observation and terminal, not a grant of authority. For a full reply, use the last matching observation and terminal. Return only JSON with terminal_status, stop_reason, latest_sequence, observed_target_pointer_binding (boolean: latest pointer_binding has both focus and surface equal to target_focus), replay_interrupted_tail (boolean), reuse_old_lease (boolean), next_step (one of restore_focus_then_reobserve or fresh_intent_after_revalidation), and record_proves_game_task_success (boolean). Report historical evidence only; observing target binding never authorizes automatic input or lease reuse.\n'''
schedule=[]
for case,stage,order in [('lost','fault-terminal',['full','view']),('restored','refocus',['view','full'])]:
 source=HERE/'results/mindustry-focus-self-use-01'/stage/'reply.json';reply=json.loads(source.read_text());view=build(reply,6291470)
 expected={'terminal_status':'needs_decision','stop_reason':'focus_changed','latest_sequence':3 if case=='lost' else 6,'observed_target_pointer_binding':case=='restored','replay_interrupted_tail':False,'reuse_old_lease':False,'next_step':'restore_focus_then_reobserve' if case=='lost' else 'fresh_intent_after_revalidation','record_proves_game_task_success':False}
 for arm in order:
  name=case+'-'+arm;payload={'target_focus':6291470,'reply':reply} if arm=='full' else view
  data=(instruction+json.dumps(payload,separators=(',',':'),sort_keys=True)).encode();(root/(name+'.txt')).write_bytes(data)
  schedule.append({'name':name,'case':case,'arm':arm,'prompt_sha256':hashlib.sha256(data).hexdigest(),'expected':expected,'source':str(source.relative_to(HERE)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
(root/'plan.json').write_text(json.dumps({'schedule':schedule,'scope':'two known static text cases; lossiness limited to explicit questions, not broad comprehension or live recovery','acceptance':'all fields exact; retain wrong answers and do not rerun to improve result','sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('focus_decision_view_v1.py','prepare_focus_model_pair_v1.py')}},indent=2)+'\n')
print([s['name'] for s in schedule])
