from pathlib import Path
import json,hashlib
from PIL import Image
root=Path(__file__).resolve().parent
manifest=json.loads((root/'FILES.sha256.json').read_bytes())
assert set(manifest)=={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name!='FILES.sha256.json'}
for path,receipt in manifest.items():
    raw=(root/path).read_bytes()
    assert len(raw)==receipt['bytes'] and hashlib.sha256(raw).hexdigest()==receipt['sha256'],path
runtime=root/'run/episode/runtime'
events=[json.loads(x) for x in (runtime/'events.jsonl').read_bytes().splitlines()]
assert events==[json.loads(x) for x in (runtime/'delivered.jsonl').read_bytes().splitlines()]
full={x['sequence']:x for x in events if x.get('event')=='observation'}
typed={x['sequence']:x for x in events if x.get('event')=='typed_observation'}
for row in full.values():
    with Image.open(runtime/Path(row['image']).name) as frame:
        assert hashlib.sha256(frame.convert('RGB').tobytes()).hexdigest()==row['frame_rgb_sha256']
for signal in ('health','ammo'): assert typed[59]['signals'][signal]['status']=='unknown'
assert typed[60]['signals']['health']['value']==91 and typed[60]['signals']['ammo']['value']==45
assert full[60]['pointer_binding']==full[59]['pointer_binding'] and full[60]['capture_ns']>full[59]['capture_ns']
report=json.loads((root/'run/episode/report.json').read_bytes())
refresh=report['source_refreshes'][2]; attempt=refresh['attempts'][0]
assert refresh['status']=='recovered' and refresh['recovered_sequence']==60
assert attempt['command']['steps']==[{'op':'observe'}]
assert attempt['terminal']['status']=='completed'
release=attempt['terminal']['release']
assert release['intent_token']==attempt['acceptance']['intent_token'] and release['verified'] is True
assert release['keys_down']==[] and release['buttons_down']==[]
decision=report['decisions'][2]
assert Path(decision['source_image']).name=='060.png' and decision['planner_answer_eligible'] is True
assert decision['plan_terminal']=='completed' and decision['model_action_discarded'] is False
assert any(r.get('event')=='accepted' and str(r.get('id','')).startswith('plan-2-') for r in events)
assert report['score']['map_exit'] is False
print(json.dumps({'members':len(manifest),'rgb':len(full),'scope':'saved source-refresh/readmission linkage; not useful recovery or exception cleanup'}))
