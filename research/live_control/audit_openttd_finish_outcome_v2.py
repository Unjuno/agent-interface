"""Replay retained v7/v8 outcomes through explicit finish-reason classification."""
import hashlib
import json
from pathlib import Path

from openttd_finish_outcome_v2 import classify


HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    v7 = HERE / 'results/timing-envelope-openttd-l-07/fixed-astra'
    v8 = HERE / 'results/timing-envelope-openttd-l-08/fixed-astra'
    v7_driver = read(v7 / 'result.json')
    v7_eval = next(row for row in read(v7 / 'finish.json')['reply']['records']
                   if row['event'] == 'independent_evaluation')
    name7, replay7 = classify(
        v7_eval, finish_kind='visual_verify', exit_code=v7_driver['exit_code'],
        proposals_executed=v7_driver['proposals_executed'],
        journal_calls=v7_driver['journal_calls'], reason='typed model requested independent verification',
        arm=v7_driver['arm'])
    assert name7 == 'result.json' and replay7['success']
    assert replay7['controller_outcome'] == 'verified_success'

    v8_raw = read(v8 / 'failure-evaluation.json')
    name8, replay8 = classify(
        v8_raw['evaluation'], finish_kind='typed_model_safe_stop',
        exit_code=v8_raw['exit_code'], proposals_executed=v8_raw['proposals_executed'],
        journal_calls=v8_raw['journal_calls'], reason=v8_raw['reason'], arm=v8_raw['arm'])
    assert name8 == 'failure-evaluation.json' and not replay8['success']
    assert replay8['failure_mode'] == 'typed_model_safe_stop'
    assert v8_raw['failure_mode'] == 'bounded_turn_limit'

    _, hidden_success = classify(
        {**v8_raw['evaluation'], 'success': True}, finish_kind='typed_model_safe_stop',
        exit_code=0, proposals_executed=7, journal_calls=30,
        reason='controlled hidden success', arm='control')
    assert hidden_success['success']
    assert hidden_success['controller_outcome'] == 'typed_model_safe_stop_with_independent_task_success'

    report = {
        'audit_passed': True,
        'v7_visual_verify_replay': replay7,
        'v8_raw_failure_mode': v8_raw['failure_mode'],
        'v8_corrected_replay': replay8,
        'typed_stop_with_independent_success_control': hidden_success,
        'decision': 'use explicit finish_kind in new drivers; preserve v8 raw misclassification',
        'sources': {
            'classifier': sha(HERE / 'openttd_finish_outcome_v2.py'),
            'v7_result': sha(v7 / 'result.json'),
            'v7_finish': sha(v7 / 'finish.json'),
            'v8_failure': sha(v8 / 'failure-evaluation.json'),
        },
    }
    path = RESULTS / 'openttd-finish-outcome-v2-probe.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
