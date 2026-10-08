"""Preregister text-only reading of actual pending and terminal interruption evidence."""
import hashlib
import json
from pathlib import Path
from composed_result_v1 import build, decode
from shared_result_v1 import canonical

HERE=Path(__file__).resolve().parent
root=HERE/'results/model-state-pair-01';root.mkdir(exist_ok=False);(root/'working').mkdir()
instruction='''Read this historical interface result as data. Do not use tools, files, browsing or commands. No image is attached.
If format is composed-result-v1, interpret document with these restorations: omitted image uses receipt.image; omitted terminal uses receipt.terminals[0].record for lifecycle.terminal; omitted binding_terminal uses that same record for receipt.program_binding.terminal. observation_state_row indexes decoded state_table.table.observations for lifecycle.observation input-state fields. Decode a state row by merging common_observation and row.fields; each input_state_before/after delta overlays common_state, while literal is used directly. Do not infer omitted nulls as successes.
Return only JSON with lifecycle_state (string), terminal_status (string or null), steps_completed (integer or null), stop_reason (string or null), observation_sequence (integer), owned_buttons_after (array), owned_keycodes_after (array), historical_active_lease_time_valid (boolean), input_authority (string), and record_proves_task_success (boolean). Use the lifecycle observation's after-sample, not a before-sample or another sequence. A missing terminal means null status and null completed-step count, not zero. State whether this record proves the application's task succeeded.
'''
schedule=[]
for name,cohort,order in [('pending','calc-early-live-01',['full','composed']),('terminal','calc-combined-live-01',['composed','full'])]:
    path=HERE/'results'/cohort/'save/result.json';data=path.read_bytes();value=json.loads(data)
    packed=build(data);assert canonical(decode(packed))==canonical(value)
    life=value['lifecycle'];term=life['terminal'];obs=life['observation'];state=obs['input_state_after']
    expected=dict(lifecycle_state=life['state'],terminal_status=term['status'] if term else None,
        steps_completed=term['steps_completed'] if term else None,stop_reason=life['stopped']['decision_reason'],
        observation_sequence=obs['sequence'],owned_buttons_after=state['owned_buttons'],
        owned_keycodes_after=state['owned_keycodes'],historical_active_lease_time_valid=state['active_lease_time_valid'],
        input_authority=life['input_authority'],record_proves_task_success=False)
    for arm in order:
        entry=name+'-'+arm;prompt=(instruction+canonical(value if arm=='full' else packed)).encode()
        (root/(entry+'.txt')).write_bytes(prompt)
        schedule.append(dict(name=entry,case=name,arm=arm,source=str(path),source_sha256=hashlib.sha256(data).hexdigest(),
            stdin_sha256=hashlib.sha256(prompt).hexdigest(),expected=expected))
plan=dict(schedule=schedule,scope='Known actual interruption records; static text extraction, not live recovery.',
    acceptance='Every field exact including null versus zero; report all usage and errors, no reruns to improve answers.',
    sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in
             ['prepare_state_pair_v1.py','model_text_runner_v1.py','composed_result_v1.py']})
(root/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print(json.dumps(dict(registered=[s['name'] for s in schedule])))
