"""Validation, clock-domain and missingness controls for TimingEnvelope v1."""
import copy
import hashlib
import json
import tempfile
from pathlib import Path

from timing_envelope_v1 import Recorder, interval, validate


H = Path(__file__).resolve().parent
R = H / 'results/timing-envelope-controls-01'
R.mkdir(exist_ok=False)
with tempfile.TemporaryDirectory() as temporary:
    recorder = Recorder(Path(temporary) / 'events.jsonl')
    first = recorder.record('observation_detected', uncertainty_ns=25_000_000)
    second = recorder.record('planner_request_started', cause='observation_detected')
    missing = recorder.record('os_injection', state='NOT_RECORDED',
                              cause='planner_request_started')
    assert first['sequence'] == 1 and second['sequence'] == 2
    assert interval(first, second)['status'] == 'comparable'
    assert interval(second, missing) == {
        'status': 'missing_endpoint', 'duration_ns': None,
        'uncertainty_ns': None}
    other = copy.deepcopy(second)
    other['clock']['domain_id'] = 'other'
    assert interval(first, other)['status'] == 'different_clock_domain'
    reverse = copy.deepcopy(second)
    reverse['timestamp_ns'] = first['timestamp_ns'] - 1
    assert interval(first, reverse)['status'] == 'ordering_error'
    rows = [json.loads(line) for line in
            (Path(temporary) / 'events.jsonl').read_text().splitlines()]
    assert [row['sequence'] for row in rows] == [1, 2, 3]

invalid = {}
base = first
for name, mutate in (
        ('unknown_state', lambda row: row.__setitem__('state', 'UNKNOWN')),
        ('observed_without_time', lambda row: row.__setitem__('timestamp_ns', None)),
        ('observed_without_clock', lambda row: row.__setitem__('clock', None)),
        ('negative_uncertainty', lambda row: row.__setitem__('uncertainty_ns', -1)),
        ('missing_with_time', lambda row: row.update(
            {'state': 'MISSING', 'timestamp_ns': 1})),
        ('extra_field', lambda row: row.__setitem__('authority', True))):
    candidate = copy.deepcopy(base)
    mutate(candidate)
    try:
        validate(candidate)
    except ValueError as exc:
        invalid[name] = str(exc)
assert len(invalid) == 6
plan = {'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest()
                    for name in ('timing_envelope_v1.py',
                                 'probe_timing_envelope_v1.py')}}
(R / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
(R / 'invalid.json').write_text(json.dumps(invalid, indent=2) + '\n')
result = {'same_process_interval': 'comparable',
          'missing_interval': 'missing_endpoint',
          'different_domain_interval': 'different_clock_domain',
          'invalid_records_refused': len(invalid)}
(R / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
