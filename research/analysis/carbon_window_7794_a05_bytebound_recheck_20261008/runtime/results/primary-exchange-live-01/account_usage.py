from pathlib import Path
import json
import importlib.util
import subprocess
import hashlib

repo=Path('/var/tmp/agent-interface-evidence-storage-main')
out=repo/'runtime/results/primary-exchange-live-01'
source=Path('/mnt/c/Users/junny/.codex/sessions/2026/09/12/rollout-2026-09-12T23-46-37-01a09615-a96c-7b70-8284-e6391b885be5.jsonl')
window={'name':'primary_exchange_allocation_control_through_first_terminal_oracle'}
begins=[];ends=[]
with source.open(encoding='utf-8') as stream:
    for index,line in enumerate(stream,1):
        if 'primary-exchange-live-01' not in line:continue
        row=json.loads(line);payload=row.get('payload',{})
        if row.get('type')!='response_item' or payload.get('type')!='custom_tool_call':continue
        code=payload.get('input','')
        if 'account-primary-exchange-live.py' in code:continue
        if 'Freeze primary exchange self-use allocation and packaged source' in code and 'keeper.py runtime/results/primary-exchange-live-01/frozen-runtime.pyz' in code:
            begins.append((index,payload['call_id']))
        if '$closed =' in code and "'events.jsonl'" in code and 'original-reply-7.json' in code:
            ends.append((index,payload['call_id']))
if len(begins)!=1 or len(ends)!=1:raise ValueError('nonunique source boundaries '+str((begins,ends)))
window.update(begin_line=begins[0][0],begin_call_id=begins[0][1],end_call_id=ends[0][1])
spec=importlib.util.spec_from_file_location('usage',repo/'research/live_control/primary_usage_projection.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def lines():
    with source.open(encoding='utf-8') as stream:
        for index,line in enumerate(stream,1):
            yield line if index>=window['begin_line'] or '"type":"turn_context"' in line or '"type": "turn_context"' in line else '{}\n'
result=module.project(lines(),[window]);result['source_session']=str(source)
result['scope_note']='Allocation/scaffold publication command through first post-terminal app-event/release read; includes primary control, image views and driver authoring. Excludes prior implementation/contract tests/build and later artifact verification/accounting/publication. No comparison or billing inference.'
(out/'usage-whole.json').write_text(json.dumps(result,indent=2)+'\n')
(out/'usage-whole-selection.json').write_text(json.dumps([window],indent=2)+'\n')
verifier=subprocess.check_output(['git','-C',str(repo),'show','HEAD:runtime/results/original-presentation-live-01/verify_usage.py'],text=True)
(out/'verify_usage.py').write_text(verifier)
w=result['windows'][0]
rows=[w['begin'],w['end'],*w['usage_records']]
for c in w['calls']:rows.extend([c,c['output']])
expected={r['source_line']:r['source_sha256'] for r in rows};retained=[]
with source.open(encoding='utf-8') as stream:
    for index,line in enumerate(stream,1):
        if index not in expected:continue
        if hashlib.sha256(line.encode()).hexdigest()!=expected[index]:raise ValueError('source digest changed')
        retained.append({'source_line':index,'raw_line':line})
        if len(retained)==len(expected):break
if len(retained)!=len(expected):raise ValueError('source records missing')
(out/'actual-source-records.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in retained))
print(json.dumps({'totals':w['totals'],'responses':len(w['usage_records']),'source_rows':len(retained),'begin':w['begin'],'end':w['end']},indent=2))
