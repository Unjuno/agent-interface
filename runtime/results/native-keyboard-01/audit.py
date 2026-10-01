"""Read-only audit of the actual click then keyboard continuation."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
p=Path(__file__).resolve().parent
load=lambda name:json.loads((p/name).read_text())
actions=load('run/actions.json')
assert [a['interaction'] for a in actions]==['click','keyboard']
programs=[json.loads(q.read_text()) for q in (p/'run/bridge').glob('program-*.json')]
assert len(programs)==2
keyboard=[pr for pr in programs if not any(op['op'].startswith('pointer_') for op in pr['ops'])]
assert len(keyboard)==1
ops=keyboard[0]['ops']
assert ops[0]=={'op':'focus','target':'app'} and ops[-1]=={'op':'release_all'}
assert sum(op=={'op':'key_chord','keys':['Right']} for op in ops)==12
assert {'op':'key_chord','keys':['CTRL','s']} in ops
assert keyboard[0]['terminal']['release_all_required'] is True
assert actions[1]['result']['execution']['program_emissions']==28
assert [c['stage'] for c in actions[1]['result']['guard_checks']]==['before_admission','before_focus']
assert 'input.pointer' not in actions[1]['result']['required_capabilities']
assert [c['stage'] for c in actions[0]['result']['guard_checks']]==['before_admission','before_focus','before_move','before_press']
for action in actions:
    assert action['result']['status']=='completed'
    assert all(r['verified'] and r['keys_down']==r['buttons_down']==[] for r in action['result']['execution']['releases'])
    probes=[action['old_target_probe'],*action['retired_target_probes']]
    assert all(r['emissions']==0 and r['result']['status']=='refused' for r in probes)
    assert 'visual_watch' not in action
for stage in (1,2,3):
    request=p/f'run/request-{stage}.json'
    assert hashlib.sha256(request.read_bytes()).hexdigest()==load(f'run/reply-{stage}.json')['decision_sha256']
    assert load(f'run/request-{stage}.json')['source_sequence']==load(f'run/source-{stage}.json')['sequence']
assert load('run/reply-3.json')['status']=='finished'
rect=ET.parse(p/'run/shape.svg').find('.//{http://www.w3.org/2000/svg}rect')
assert [float(rect.get(k)) for k in ('x','y','width','height')]==[74,50,40,30]
assert rect.get('transform') is None
assert all(r['returncode'] is not None for r in load('run/cleanup.json'))
links=0
def images(v):
    global links
    if isinstance(v,dict):
        n=v.get('native')
        if isinstance(n,dict) and 'artifact' in n:
            a=n['artifact']; data=(p/'run/bridge/images'/Path(a['path']).name).read_bytes()
            assert hashlib.sha256(data).hexdigest()==a['sha256']
            assert a['source_raw_sha256']==n['sha256'] and v['capture_ns']==n['capture_started_ns']
            links+=1
        for child in v.values(): images(child)
    elif isinstance(v,list):
        for child in v: images(child)
for q in (p/'run').rglob('*.json'): images(json.loads(q.read_text()))
if (p/'MANIFEST.json').exists():
    assert all(hashlib.sha256((p/k).read_bytes()).hexdigest()==v for k,v in load('MANIFEST.json').items())
client=load('clients/keyboard-client-2-returned.json')['exchange']
print(json.dumps({'saved_x':74,'keyboard_program_emissions':28,'pointer_ops_in_keyboard_program':0,
    'keyboard_guard_checks':2,'retired_click_probes_refused':3,'image_hash_links':links,
    'keyboard_combined_exchange_ms':(client['returned_ns']-client['started_ns'])/1e6,
    'matched_speed_comparison':False},indent=2))
