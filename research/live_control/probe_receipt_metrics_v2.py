"""Retained success plus metric/exception/unknown-field negative controls."""
import copy
import json
from pathlib import Path
from decision_receipt_v3 import build as old
from decision_receipt_v4 import build, metric_at
from report_pages_v2 import digest

HERE = Path(__file__).resolve().parent
root = HERE / 'results/receipt-metrics-02'
root.mkdir(exist_ok=False)
source = HERE / 'results/cause-servo-live-01/servo/report.json'
data = source.read_bytes()
report = json.loads(data)
baseline = build(data)
assert len(baseline['tracking_metrics']) == 6
assert len(baseline['attention']) == len(old(data)['attention']) - 6
assert baseline['detail_review_required']
assert len(baseline['servo_feedback']) == 2
path = baseline['servo_feedback'][0]['path']
def synchronize(altered):
    altered['last_reply'] = copy.deepcopy(altered['exchanges'][1]['reply'])
    altered['continuation_batch'] = copy.deepcopy(altered['exchanges'][1]['reply'])
    altered['terminal'] = copy.deepcopy(altered['exchanges'][1]['reply']['records'][-1])

cases = []
for label, value in [('string', 'timeout'), ('boolean', True), ('negative', -.1), ('too_large', 1.1),
                     ('null', None), ('nan', float('nan'))]:
    altered = copy.deepcopy(report)
    event = altered
    for key in path:
        event = event[key]
    event['tracking']['error'] = value
    assert not metric_at(altered, path + ['tracking', 'error'])
    synchronize(altered)
    receipt = build(json.dumps(altered).encode())
    if label != 'nan':
        assert receipt['program_binding'] is not None, 'test must not rely on copy mismatch'
    assert receipt['detail_review_required']
    cases.append({'case': label, 'not_classified_as_metric': True, 'attention_retained': True})
for label in ('lost', 'unknown_tracking_field', 'nested_exception', 'numeric_other_error'):
    altered = copy.deepcopy(report)
    event = altered
    for key in path:
        event = event[key]
    if label == 'lost':
        event['tracking']['status'] = 'lost'
    elif label == 'unknown_tracking_field':
        event['tracking']['new_condition'] = 'unrecognized'
    elif label == 'nested_exception':
        event['tracking']['exception'] = 'failure'
    else:
        event['error'] = .2
    synchronize(altered)
    receipt = build(json.dumps(altered).encode())
    if label != 'nan':
        assert receipt['program_binding'] is not None, 'test must not rely on copy mismatch'
    assert receipt['detail_review_required']
    if label == 'numeric_other_error':
        assert any(a['path'] == path + ['error'] for a in receipt['attention'])
    else:
        assert not metric_at(altered, path + ['tracking', 'error'])
    cases.append({'case': label, 'attention_retained': True})
fault = HERE / 'results/cause-live-02/interrupt/report.json'
assert build(fault.read_bytes())['detail_review_required']
result = {'success': True, 'source_sha256': digest(data), 'fault_sha256': digest(fault.read_bytes()),
          'sources': {n: digest((HERE / n).read_bytes()) for n in ['probe_receipt_metrics_v2.py', 'decision_receipt_v4.py']},
          'old_attention_count': len(old(data)['attention']), 'new_attention_count': len(baseline['attention']),
          'cases': cases, 'limits': 'Offline classifier tests, no full nested schema or new live performance validation.'}
(root / 'receipt.json').write_text(json.dumps(baseline, indent=2) + '\n')
(root / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
