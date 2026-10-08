import copy
import hashlib
import json
from pathlib import Path
from openpyxl import load_workbook

root = Path(__file__).resolve().parent
run = root / 'run'
load = lambda p: json.loads(p.read_text())
assert len(list(run.glob('request-*.json'))) == len(list(run.glob('reply-*.json'))) == 2
assert len(list((root / 'baseline').glob('request-*.json'))) == 3
assert not (run / 'source-3.json').exists()
requests = [load(run / f'request-{i}.json') for i in (1, 2)]
assert requests[0] == load(root / 'baseline/request-1.json')
baseline2 = load(root / 'baseline/request-2.json')
assert requests[1] == dict(baseline2, source_sequence=4, finish_after=True)
assert requests[0]['interaction'] == 'keyboard' and requests[1]['point'] == [750, 463]
replies = [load(run / f'reply-{i}.json') for i in (1, 2)]
assert [r['status'] for r in replies] == ['boundary', 'finished']
assert requests[1]['source_sequence'] == replies[0]['observation']['sequence']
assert replies[0]['action']['window_review']['previous_window_id'] != replies[0]['action']['window_review']['requested_window_id']
final = replies[1]
assert final['finish_mode'] == 'after_action'
assert final['evaluation']['success'] and final['evaluation']['actual'] == [551, 768]
assert final['cleanup']['status'] == 'completed' and not final['cleanup']['errors']
assert all(p['returncode'] is not None for p in final['cleanup']['processes'])
assert final['observation'] == final['action']['window_review']['observation']
assert final['observation']['capture_ns'] < final['evaluation']['known_ns'] < final['cleanup']['ended_ns']
# Do not relabel the disappeared-dialog feedback as a match.
assert final['action']['feedback']['status'] == 'needs_review'
assert 'BadWindow' in final['action']['feedback']['error']
wb = load_workbook(run / 'sheet.xlsx', read_only=True, data_only=False)
assert [wb.active[c].value for c in ('A1', 'A2', 'B1')] == [551, 768, None]
wb.close()
actions = load(run / 'actions.json')
assert actions == [r['action'] for r in replies]
assert [a['interaction'] for a in actions] == ['keyboard', 'click']
assert [a['result']['execution']['program_emissions'] for a in actions] == [20, 3]
assert all(a['result']['status'] == 'completed' for a in actions)
assert all(r['verified'] and r['keys_down'] == r['buttons_down'] == []
           for a in actions for r in a['result']['execution']['releases'])
programs = [load(p) for p in (run / 'bridge').glob('program-*.json')]
assert len(programs) == 2
assert sum(not any(op['op'].startswith('pointer_') for op in p['ops']) for p in programs) == 1
corruption_controls = 0
for stage in (1, 2):
    def check_link(reply):
        assert reply['decision_sha256'] == hashlib.sha256((run / f'request-{stage}.json').read_bytes()).hexdigest()
    check_link(replies[stage - 1])
    bad = copy.deepcopy(replies[stage - 1]); bad['decision_sha256'] = '0' * 64
    try: check_link(bad)
    except AssertionError: corruption_controls += 1
    else: raise AssertionError('corrupt request link accepted')
links = 0
def images(value):
    global links
    if isinstance(value, dict):
        n = value.get('native')
        if isinstance(n, dict) and 'artifact' in n:
            a = n['artifact']; path = run / 'bridge/images' / Path(a['path']).name
            assert hashlib.sha256(path.read_bytes()).hexdigest() == a['sha256']
            assert a['source_raw_sha256'] == n['sha256'] and value['capture_ns'] == n['capture_started_ns']
            links += 1
        for child in value.values(): images(child)
    elif isinstance(value, list):
        for child in value: images(child)
for path in run.rglob('*.json'): images(load(path))
for name, digest in load(root / 'SOURCE_FREEZE.json')['files'].items():
    assert hashlib.sha256((root / 'source' / Path(name).name).read_bytes()).hexdigest() == digest
if (root / 'MANIFEST.json').exists():
    for name, digest in load(root / 'MANIFEST.json').items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
print(json.dumps({'disposition': 'PASS_CALC_FINAL_ACTION_SCOPED', 'requests': 2,
    'baseline_requests': 3, 'saved_A1_A2_B1': [551, 768, None],
    'image_hash_links': links, 'corruption_controls_rejected': corruption_controls,
    'last_image_dialog_pixels_remain': 'primary-assistant visual observation',
    'final_feedback': 'needs_review/BadWindow preserved', 'causal_latency_benefit': 'unmeasured'}, indent=2))
