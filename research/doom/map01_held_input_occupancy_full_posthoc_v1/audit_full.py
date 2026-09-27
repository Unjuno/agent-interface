from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

EXPECTED = {
    'map01-v38-integrated-threat-live-01': {
        'report.json': '7fa222f9b273ee10ad1ed3e24b8f7f234f46cc137265a90d70c6073981602f58',
        'runtime/events.jsonl': '80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3',
    },
    'map01-v39-coast-liveness-live-01': {
        'report.json': '719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687',
        'runtime/events.jsonl': '2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381',
    },
}

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('result', type=Path)
    ap.add_argument('--repo', type=Path, required=True)
    args = ap.parse_args()
    value = json.loads(args.result.read_text())
    assert value['schema'] == 'map01-held-input-occupancy-full-posthoc-v1'
    assert value['task'] == 'MAP01-HELD-OCCUPANCY-FULL-POSTHOC-20260916-001'
    assert len(value['runs']) == 2
    errors = []
    for run in value['runs']:
        name = run['run']
        if name not in EXPECTED:
            errors.append(f'unexpected run {name}'); continue
        root = args.repo / 'research/doom/results' / name
        actual = {'report.json': sha256(root/'report.json'),
                  'runtime/events.jsonl': sha256(root/'runtime/events.jsonl')}
        if actual != EXPECTED[name] or run['source_sha256'] != EXPECTED[name]:
            errors.append(f'source mismatch {name}')
        for hold in run['holds']:
            if not (hold['first_key_admitted_ns'] <= hold['first_key_ack_ns'] <=
                    hold['confirmed_any_key_held_until_ns'] <= hold['released_by_ns']):
                errors.append(f'bad hold order {name}:{hold["id"]}:{hold["step"]}')
            if hold['physical_any_key_occupancy_lower_ms'] > hold['physical_any_key_occupancy_upper_ms']:
                errors.append(f'negative interval {name}:{hold["id"]}:{hold["step"]}')
            if hold['exact_physical_duration_known'] is not False:
                errors.append(f'false exactness {name}:{hold["id"]}:{hold["step"]}')
        sum_lower = round(sum(d['physical_any_key_occupancy_lower_ms'] for d in run['decisions']), 3)
        sum_upper = round(sum(d['physical_any_key_occupancy_upper_ms'] for d in run['decisions']), 3)
        sum_width = round(sum(d['occupancy_interval_width_ms'] for d in run['decisions']), 3)
        totals = run['totals']
        if (sum_lower, sum_upper, sum_width) != (
            totals['physical_any_key_occupancy_lower_ms'],
            totals['physical_any_key_occupancy_upper_ms'],
            totals['occupancy_interval_width_ms']):
            errors.append(f'total mismatch {name}')
        wait = round(sum(d['model_wait_ms'] for d in run['decisions']), 3)
        if wait != run['total_model_wait_ms']:
            errors.append(f'wait mismatch {name}')
        width_to_wait = totals['occupancy_interval_width_ms'] / wait if wait else None
        width_to_upper = totals['occupancy_interval_width_ms'] / totals['physical_any_key_occupancy_upper_ms'] if totals['physical_any_key_occupancy_upper_ms'] else 0.0
        diag = run['diagnostic']
        if abs(width_to_wait - diag['width_to_model_wait']) > 1e-12:
            errors.append(f'width/wait mismatch {name}')
        if abs(width_to_upper - diag['width_to_occupancy_upper']) > 1e-12:
            errors.append(f'width/upper mismatch {name}')
    expected_decision = ('RETAIN_FULL_OCCUPANCY_INTERVALS_SCOPED'
        if all(r['diagnostic']['informative_enough_for_next_matched_metric'] for r in value['runs'])
        else 'SCHEMA_CENSORING_TOO_WIDE')
    if value['decision'] != expected_decision:
        errors.append('decision mismatch')
    out = {'status': 'PASS_FULL_POSTHOC_AUDIT' if not errors else 'FAIL_FULL_POSTHOC_AUDIT',
           'errors': errors, 'result_sha256': sha256(args.result)}
    print(json.dumps(out, indent=2))
    raise SystemExit(0 if not errors else 1)

if __name__ == '__main__':
    main()
