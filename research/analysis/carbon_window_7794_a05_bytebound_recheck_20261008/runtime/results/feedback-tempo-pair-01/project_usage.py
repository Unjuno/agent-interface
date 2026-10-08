from pathlib import Path
import json,importlib.util,subprocess
root=Path('/var/tmp/agent-interface-evidence-storage-main');out=root/'runtime/results/feedback-tempo-pair-01'
source=Path('/mnt/c/Users/junny/.codex/sessions/2026/09/12/rollout-2026-09-12T23-46-37-01a09615-a96c-7b70-8284-e6391b885be5.jsonl')
whole={'name':'inclusive_two_arm_construction_control_and_initial_oracle_window'}
with source.open(encoding='utf-8') as f:
 for index,line in enumerate(f,1):
  if 'custom_tool_call' not in line or 'feedback-tempo-pair-01' not in line and 'tempo-pair-command.py' not in line:continue
  row=json.loads(line);p=row.get('payload',{})
  if row.get('type')!='response_item' or p.get('type')!='custom_tool_call':continue
  code=p.get('input','')
  if 'project-tempo-pair-usage.py' in code:continue
  if 'runtime/results/feedback-tempo-pair-01/01-immediate pending' in code:whole.update(begin_call_id=p['call_id'],begin_line=index)
  if 'tempo-pair-command.py' in code and '02-cue-wait 6 ' in code:whole['end_call_id']=p['call_id']
if 'begin_call_id' not in whole or 'end_call_id' not in whole:raise ValueError('missing boundaries '+str(whole))
spec=importlib.util.spec_from_file_location('usage',root/'research/live_control/primary_usage_projection.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def lines():
 with source.open(encoding='utf-8') as f:
  for index,line in enumerate(f,1):yield line if index>=whole['begin_line'] or '"type":"turn_context"' in line or '"type": "turn_context"' in line else '{}\n'
result=module.project(lines(),[whole]);result['source_session']=str(source)
result['prefix_handling']='irrelevant prefix skipped with original line numbers; all turn_context and selected source lines preserved'
result['scope_note']='Begin tool includes source scaffold commit/build and baseline allocation. End tool includes candidate close, terminal wait and first app-event read. Includes primary reviews/control/image tool calls; excludes later audit, frame re-view/correction, accounting and publication. Arm-specific billing/token savings are not inferable; baseline close/candidate allocation share a tool boundary.'
(out/'usage-whole.json').write_text(json.dumps(result,indent=2)+'\n');(out/'usage-whole-selection.json').write_text(json.dumps([whole],indent=2)+'\n')
print(json.dumps({'windows':[{'name':w['name'],'status':w['status'],'totals':w['totals']} for w in result['windows']]},indent=2),flush=True)
verify=subprocess.check_output(['git','show','HEAD:runtime/results/feedback-primary-presentation-01/verify_usage.py'],cwd=root,text=True)
verify=verify.replace('single whole-context live control window; billing unavailable; excludes earlier implementation/tests/build and later audit/publication','combined construction/control/first-oracle window; billing unavailable; not arm-specific cost comparison')
(out/'verify_usage.py').write_text(verify)
