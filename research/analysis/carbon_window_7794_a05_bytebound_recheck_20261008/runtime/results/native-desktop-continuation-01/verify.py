"""Saved desktop evidence checks: no extraction, GUI, subprocess or replay."""
import hashlib
import json
from pathlib import Path
import tarfile

root = Path(__file__).resolve().parent
manifest = json.loads((root/'manifest.json').read_text())
with tarfile.open(root/'evidence.tar.gz', 'r:gz') as archive:
    members = archive.getmembers()
    assert len(members) == len(manifest)
    assert all(m.isfile() for m in members)
    assert {m.name for m in members} == set(manifest)
    data = {m.name: archive.extractfile(m).read() for m in members}
for name, expected in manifest.items():
    assert hashlib.sha256(data[name]).hexdigest() == expected, name

def read(name):
    return json.loads(data[name].decode('utf-8-sig'))

spans = {}
for run in ('calc-01', 'calc-02'):
    def get(name):
        return read(run+'/'+name)
    assert get('allocation/run/evaluation.json')['actual'] == [763, 660]
    assert get('allocation/run/evaluation.json')['success'] is True
    assert get('saved-file-check.json')['saved_cells'] == [763, 660]
    assert hashlib.sha256(data[run+'/allocation/run/sheet.xlsx']).hexdigest() == get('saved-file-check.json')['sha256']
    assert get('primary-declaration.json')['primary_visible_goal_complete'] is True
    for stage in (1, 2):
        reply = get(f'action-{stage}-metadata.json')
        raw = get(f'allocation/run/reply-{stage}.json')
        assert raw['action']['result']['status'] == 'completed'
        releases = raw['action']['result']['execution']['releases']
        assert releases and all(r['verified'] is True and r['keys_down'] == [] and r['buttons_down'] == [] for r in releases)
        assert reply['outcome_summary']['feedback_status'] == 'needs_review'
        assert reply['image_status'] == 'image'
        continuation = reply['continuation']
        assert continuation['status'] == 'source_available'
        assert continuation['stage'] == stage+1
        next_decision = get(f'decision-{stage+1}.json')['arguments']
        assert next_decision['stage'] == continuation['stage']
        assert next_decision['decision']['source_sequence'] == continuation['source_sequence']
        source = data[f'{run}/allocation/run/source-{stage+1}.json']
        assert hashlib.sha256(source).hexdigest() == continuation['source_sha256']
    owner = get('action-4-metadata.json')['allocation']
    assert owner['status'] == 'terminal' and owner['returncode'] == 0
    times = [get(f'action-{n}-timing.json') for n in (1, 2, 3)]
    total = (times[-1]['end_ns']-times[0]['start_ns'])/1e9
    inside = sum(t['end_ns']-t['start_ns'] for t in times)/1e9
    recorded = get('RESULT.json')
    assert abs(recorded['client_span_first_submit_through_finish_s']-total) < 1e-9
    assert abs(recorded['inside_three_sdk_calls_s']-inside) < 1e-9
    spans[run] = {'total_s': total, 'sdk_s': inside, 'between_s': total-inside}

for stage in (1, 2, 3):
    assert read(f'calc-01/decision-{stage}.json') == read(f'calc-02/decision-{stage}.json')
ink = read('inkscape-01/action-1-metadata.json')
assert ink['outcome_summary']['action_status'] == 'refused'
assert ink['image_status'] == 'no_observation'
raw = read('inkscape-01/allocation/run/reply-1.json')
assert raw['action']['result']['input_dispatched'] is False
assert raw['action']['result']['guard_checks'][0]['reason'] == 'region_pixels_missing'
assert ink['continuation']['status'] == 'unavailable'
owner = read('inkscape-01/action-2-metadata.json')['allocation']
assert owner['status'] == 'terminal' and owner['returncode'] == 1
print(json.dumps({'status': 'PASS_ARCHIVE_CONSISTENCY', 'files': len(data),
                  'calc_spans': spans, 'inkscape': 'refused_before_input',
                  'scope': 'saved evidence only; no independent adoption or performance claim'}))
