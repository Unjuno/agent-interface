"""Read retained native trials for integration planning; never dispatch input."""
import hashlib
import json
from pathlib import Path

repo = Path(__file__).resolve().parents[3]
names = ['native-continuation-integrated-01', 'native-process-snapshot-live-01',
         'native-process-snapshot-recheck-01']
trials = []
for name in names:
    root = repo / 'runtime/results' / name
    run = root / 'allocation/run'
    rows = [json.loads(line) for line in (root / 'responses.jsonl').read_bytes().splitlines()]
    metadata = [json.loads(r['result']['content'][0]['text']) for r in rows]
    requests = sorted(run.glob('request-*.json'))
    digests = []
    for request in requests:
        stage = int(request.stem.split('-')[1])
        digest = hashlib.sha256(request.read_bytes()).hexdigest()
        reply = json.loads((run / f'reply-{stage}.json').read_bytes())
        assert reply['decision_sha256'] == digest
        digests.append(digest)
    goal = json.loads((run / 'goal.json').read_bytes())
    final = next(m for m in reversed(metadata)
                 if m.get('receipt', {}).get('native_result', {}).get('status') == 'finished')
    trials.append({'name': name, 'responses_sha256': hashlib.sha256((root / 'responses.jsonl').read_bytes()).hexdigest(),
        'request_sha256': digests, 'calls': [r['tool'] for r in rows],
        'initial_image_sha256': metadata[0]['image_reference']['sha256'],
        'explicit_public_task_present': 'task' in goal,
        'final_task_success': final['receipt']['native_result']['evaluation']['success'],
        'final_submit_process_status': final.get('allocation', {}).get('status'),
        'submit_sdk_ms': [(r['sdk_return_ns']-r['sdk_entry_ns'])/1e6 for r in rows if r['tool']=='native_submit']})
assert all(t['request_sha256'] == trials[0]['request_sha256'] for t in trials)
assert len({t['initial_image_sha256'] for t in trials}) == 1
print(json.dumps({'scope': 'retained primary-assistant WSL traces, not a controlled adaptive-model evaluation',
    'trials': trials, 'identical_action_requests_and_initial_pixels': True,
    'missing_for_abc_comparison': ['fixed/adaptive local candidate', 'frozen rich-model identity and context',
        'model input/output tokens and cost', 'host model-visible image boundary',
        'cold-start/update/invalidation costs', 'calibration and abstention labels',
        'held-out domains and disturbances', 'independent review and real-container gate']}, indent=2))
