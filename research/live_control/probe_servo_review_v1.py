"""Consistent-copy mutations exercise fallback of the successful-servo card."""
import copy
import json
from pathlib import Path
from servo_review_v1 import build
from decision_receipt_v4 import build as detailed
from report_pages_v2 import digest

HERE = Path(__file__).resolve().parent
out = HERE / 'results/servo-review-01'
out.mkdir(exist_ok=False)
source = HERE / 'results/cause-servo-live-01/servo/report.json'
data = source.read_bytes()
original = json.loads(data)
baseline = build(data)
assert baseline['format'] == 'servo-review-v1'
cases = []
for name in ('unknown_top', 'unknown_observation', 'unknown_tracking', 'metric_exception', 'lost',
             'revision', 'owner', 'physical_button', 'deadline', 'wrong_correction', 'outcome_false',
             'outcome_id', 'goal_delta', 'release_failed', 'completed_with_cause', 'unknown_terminal'):
    report = copy.deepcopy(original)
    records = report['exchanges'][1]['reply']['records']
    observation = next(e for e in records if e['event'] == 'observation')
    feedback = next(e for e in records if e['event'] == 'servo_feedback')
    outcome = next(e for e in records if e['event'] == 'servo_outcome')
    terminal = records[-1]
    if name == 'unknown_top': report['new_condition'] = 'unrecognized'
    elif name == 'unknown_observation': observation['new_condition'] = True
    elif name == 'unknown_tracking': feedback['tracking']['new_condition'] = True
    elif name == 'metric_exception': feedback['tracking']['error'] = 'timeout'
    elif name == 'lost': feedback['tracking']['status'] = 'lost'
    elif name == 'revision': observation['input_state_after']['revision'] += 1
    elif name == 'owner': observation['input_state_after']['owner_id'] = 'another'
    elif name == 'physical_button': observation['input_state_after']['physical_pointer_mask'] = 0
    elif name == 'deadline': observation['input_state_after']['active_lease_deadline_ns'] += 1
    elif name == 'wrong_correction': feedback['command']['x'] += 10
    elif name == 'outcome_false': outcome['local_goal_reached'] = False
    elif name == 'outcome_id': outcome['id'] = 'another'
    elif name == 'goal_delta': [e for e in records if e['event'] == 'servo_feedback'][-1]['tracking']['delta'] = [0, 0]
    elif name == 'release_failed': terminal['release']['verified'] = False
    elif name == 'completed_with_cause': terminal['interruption'] = {'intent_token': 'synthetic', 'record': {'reason': 'focus_changed'}}
    elif name == 'unknown_terminal': terminal['new_condition'] = True
    report['terminal'] = copy.deepcopy(terminal)
    report['last_reply'] = copy.deepcopy(report['exchanges'][1]['reply'])
    report['continuation_batch'] = copy.deepcopy(report['last_reply'])
    altered = json.dumps(report).encode()
    assert detailed(altered)['program_binding'] is not None
    result = build(altered)
    assert result['format'] == 'decision-receipt-v4' and result['detail_review_required'] and result['compact_unavailable']
    cases.append({'case': name, 'fallback_reason': result['compact_unavailable']})
fault = HERE / 'results/cause-live-02/interrupt/report.json'
assert build(fault.read_bytes())['detail_review_required']
result = {'success': True, 'sources': {n: digest((HERE / n).read_bytes()) for n in ['servo_review_v1.py', 'probe_servo_review_v1.py']},
          'source_sha256': digest(data), 'cases': cases,
          'detailed_bytes': len(json.dumps(detailed(data)).encode()), 'card_bytes': len(json.dumps(baseline).encode()),
          'limits': 'Selected record consistency checks, not full schema validation, authenticity, live model receipt or token accounting.'}
(out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
(out / 'card.json').write_text(json.dumps(baseline, indent=2) + '\n')
print(json.dumps(result))
