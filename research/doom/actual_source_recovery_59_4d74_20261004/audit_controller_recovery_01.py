from pathlib import Path
import json,hashlib
from PIL import Image
root=Path(__file__).resolve().parent
run=root/'controller-recovery-01'
runtime=run/'episode/runtime'
events=[json.loads(x) for x in (runtime/'events.jsonl').read_bytes().splitlines()]
assert events==[json.loads(x) for x in (runtime/'delivered.jsonl').read_bytes().splitlines()]
observations={x['sequence']:x for x in events if x.get('event')=='observation'}
typed={x['sequence']:x for x in events if x.get('event')=='typed_observation'}
report=json.loads((run/'episode/report.json').read_bytes())
print(json.dumps({'score':report['score'],'decisions':[{'iteration':d['iteration'],'source_image':d['source_image'],'eligible':d['planner_answer_eligible'],'status':d['planner_turn_status'],'discarded':d.get('model_action_discarded'),'plan_terminal':d['plan_terminal']} for d in report['decisions']],'typed59':typed.get(59),'typed60':typed.get(60),'finish_commands':[x['command'] for x in events if x.get('event')=='command' and x['command'].get('op')=='finish']}))
for row in observations.values():
    with Image.open(runtime/Path(row['image']).name) as image:
        assert hashlib.sha256(image.convert('RGB').tobytes()).hexdigest()==row['frame_rgb_sha256']
for relative,receipt in json.loads((root/'CONTROLLER_SOURCE_10_PREPARATION.json').read_bytes())['members'].items():
    assert hashlib.sha256((root/'current-controller-source-10'/relative).read_bytes()).hexdigest()==receipt['sha256']
recovery=report['source_refreshes'][2]
assert recovery['status']=='recovered' and recovery['source_sequence']==59 and recovery['recovered_sequence']==60
attempt=recovery['attempts'][0]
assert attempt['command']['steps']==[{'op':'observe'}]
assert attempt['terminal']['status']=='completed'
assert attempt['terminal']['release']['intent_token']==attempt['acceptance']['intent_token']
assert attempt['terminal']['release']['verified'] is True
assert attempt['terminal']['release']['keys_down']==[] and attempt['terminal']['release']['buttons_down']==[]
summary={'scope':'saved evidence integrity and source-refresh linkage only', 'rgb_observations':len(observations),'source_pins':1955,'recovery':recovery,'score':report['score'],'decisions':[{k:d.get(k) for k in ['iteration','planner_turn_status','planner_answer_eligible','model_action_discarded','plan_terminal']} for d in report['decisions']]}
(run/'SAVED_RECOVERY_AUDIT.json').write_bytes(json.dumps(summary,indent=2).encode())
