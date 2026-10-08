from pathlib import Path
import json
import importlib.util
import subprocess

root=Path('/var/tmp/agent-interface-evidence-storage-main')
out=root/'runtime/results/original-presentation-live-01'
source=Path('/mnt/c/Users/junny/.codex/sessions/2026/09/12/rollout-2026-09-12T23-46-37-01a09615-a96c-7b70-8284-e6391b885be5.jsonl')
window={'name':'primary_live_control_through_terminal_oracle_and_same_file_review'}
with source.open(encoding='utf-8') as stream:
    for index,line in enumerate(stream,1):
        if 'original-presentation-live-01' not in line:continue
        row=json.loads(line);payload=row.get('payload',{})
        if row.get('type')!='response_item' or payload.get('type')!='custom_tool_call':continue
        code=payload.get('input','')
        if 'project-original-live-usage.py' in code:continue
        if '/keeper.py /var/tmp/' in code and '/case immediate' in code:
            window.update(begin_call_id=payload['call_id'],begin_line=index)
        if 'getextrema' in code and 'tools.view_image' in code and 'primary-007.png' in code:
            window['end_call_id']=payload['call_id']
if 'begin_call_id' not in window or 'end_call_id' not in window:
    raise ValueError('missing actual window boundaries '+str(window))
spec=importlib.util.spec_from_file_location('usage',root/'research/live_control/primary_usage_projection.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def lines():
    with source.open(encoding='utf-8') as stream:
        for index,line in enumerate(stream,1):
            yield line if index>=window['begin_line'] or '"type":"turn_context"' in line or '"type": "turn_context"' in line else '{}\n'
result=module.project(lines(),[window]);result['source_session']=str(source)
result['scope_note']='Launch through explicit close, owner terminal, first independent app-event/hash read and fifth same-file image view. Includes primary control/inspection and driver authoring; excludes scaffold/build before launch, later verification/accounting/publication. No comparison arm or billing inference.'
(out/'usage-whole.json').write_text(json.dumps(result,indent=2)+'\n')
(out/'usage-whole-selection.json').write_text(json.dumps([window],indent=2)+'\n')
verify=subprocess.check_output(['git','-C',str(root),'show','c7f0f8d499c384692824a1261310478a350232d4:runtime/results/feedback-tempo-pair-01/verify_usage.py'],text=True)
verify=verify.replace('combined construction/control/first-oracle window; billing unavailable; not arm-specific cost comparison','single live-control/terminal-oracle window; billing unavailable; not a comparison')
(out/'verify_usage.py').write_text(verify)
print(json.dumps({'windows':[{'name':w['name'],'status':w['status'],'totals':w['totals']} for w in result['windows']]},indent=2))
