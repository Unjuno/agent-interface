from pathlib import Path
import json,importlib.util,hashlib,subprocess
repo=Path('/var/tmp/agent-interface-evidence-storage-main')
out=repo/'runtime/results/primary-modal-accounting-01'
source=Path('/mnt/c/Users/junny/.codex/sessions/2026/09/12/rollout-2026-09-12T23-46-37-01a09615-a96c-7b70-8284-e6391b885be5.jsonl')
begins=[];ends=[]
with source.open(encoding='utf-8') as stream:
 for index,line in enumerate(stream,1):
  if 'primary-target-tools-live-04' not in line:continue
  row=json.loads(line);p=row.get('payload',{})
  if row.get('type')!='response_item' or p.get('type')!='custom_tool_call':continue
  code=p.get('input','')
  if 'account_primary_modal.py' in code:continue
  if 'Freeze schema-qualified fresh primary Calc modal allocation' in code:begins.append((index,p['call_id']))
  if 'cat cleanup.json && cat evaluation.json' in code:ends.append((index,p['call_id']))
if len(begins)!=1 or len(ends)!=1:raise ValueError('nonunique actual boundaries '+str((begins,ends)))
selection=[{'name':'primary_modal_allocation_through_terminal_file_oracle','begin_line':begins[0][0],'begin_call_id':begins[0][1],'end_call_id':ends[0][1]}]
spec=importlib.util.spec_from_file_location('usage',repo/'research/live_control/primary_usage_projection.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def lines():
 with source.open(encoding='utf-8') as stream:
  for index,line in enumerate(stream,1):
   yield line if index>=begins[0][0] or '"type":"turn_context"' in line or '"type": "turn_context"' in line else '{}\n'
result=module.project(lines(),selection)
result['source_session']=str(source)
result['scope_note']='Fourth construction allocation preparation/build/launch through first post-terminal independent XLSX scoring read. Includes reader/scaffold authoring, original image tool turns, review/clock/close and cleanup; excludes previous failures, implementation, earlier preflight, subsequent audit/publication/accounting. Whole shared context, not isolated route cost or matched savings.'
(out/'usage-whole.json').write_text(json.dumps(result,indent=2)+'\n')
(out/'usage-whole-selection.json').write_text(json.dumps(selection,indent=2)+'\n')
w=result['windows'][0];records=[w['begin'],w['end'],*w['usage_records']]
for call in w['calls']:records.extend([call,call['output']])
expected={r['source_line']:r['source_sha256'] for r in records};retained=[]
with source.open(encoding='utf-8') as stream:
 for index,line in enumerate(stream,1):
  if index not in expected:continue
  if hashlib.sha256(line.encode()).hexdigest()!=expected[index]:raise ValueError('source changed')
  record=json.loads(line)
  if record.get('type') not in ('token_usage_record','response_item'):raise ValueError('unexpected private record type')
  if record.get('type')=='response_item' and record['payload']['type'] not in ('custom_tool_call','custom_tool_call_output'):raise ValueError('do not retain reasoning or other chat text')
  retained.append({'source_line':index,'raw_line':line})
  if len(retained)==len(expected):break
if len(retained)!=len(expected):raise ValueError('missing selected source')
(out/'actual-source-records.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in retained))
verifier=subprocess.check_output(['git','-C',str(repo),'show','HEAD:runtime/results/primary-exchange-live-01/verify_retained_usage.py'],text=True)
(out/'verify_retained_usage.py').write_text(verifier)
print(json.dumps({'totals':w['totals'],'responses':len(w['usage_records']),'source_rows':len(retained),'begin':w['begin'],'end':w['end']},indent=2))
