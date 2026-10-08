import hashlib,json
from pathlib import Path
p=Path(__file__).resolve().parent
load=lambda name:json.loads((p/name).read_text())
keycode=load('run/fixture.json')['keycode']
rows=load('run/observations.json')
assert [r['condition'] for r in rows]==['initial_up','held_key_and_left','released_by_fixture']
for row in rows:
    r=row['record']
    assert r['backend_emissions_before']==r['backend_emissions_after']==0
    assert r['input_dispatched'] is False and r['authority_granted'] is False
    assert r['clears_recovery_required'] is False
    assert r['coverage']['extended_buttons_observed'] is False
    assert r['coverage']['atomic_snapshot'] is False
    assert [s['requested_offset_ms'] for s in r['samples']]==[0,10,50]
    for s in r['samples']:
        assert s['status']=='observed'
        assert s['keycodes_down']==([keycode] if row['condition']=='held_key_and_left' else [])
        assert s['core_buttons_down']==([1] if row['condition']=='held_key_and_left' else [])
        assert r['started_ns']<=s['started_ns']<=s['keymap_known_ns']<=s['pointer_known_ns']<=r['ended_ns']
assert all(r['returncode'] is not None for r in load('run/cleanup.json'))
assert load('run/result.json')['prior_failure_cause_identified'] is False
if (p/'MANIFEST.json').exists():
    for name,digest in load('MANIFEST.json').items():
        assert hashlib.sha256((p/name).read_bytes()).hexdigest()==digest
print(json.dumps({'controlled_conditions':3,'samples':9,'diagnostic_emissions':0,
                  'prior_failure_cause_identified':False}))
