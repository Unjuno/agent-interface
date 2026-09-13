"""Control cases for declared OpenTTD finish reasons."""
from openttd_finish_outcome_v2 import classify


def run(success, kind):
    return classify({'event': 'independent_evaluation', 'success': success},
                    finish_kind=kind, exit_code=0, proposals_executed=3,
                    journal_calls=14, reason='controlled', arm='fixed-astra')


def main():
    expected_failures = {
        'visual_verify': 'visual_verify_false_positive',
        'bounded_turn_limit': 'bounded_turn_limit',
        'typed_model_safe_stop': 'typed_model_safe_stop',
        'supervisor_cleanup': 'supervisor_cleanup',
    }
    for kind, expected in expected_failures.items():
        name, outcome = run(False, kind)
        assert name == 'failure-evaluation.json'
        assert outcome['failure_mode'] == expected and not outcome['success']
        assert outcome['finish_kind'] == kind
        name, outcome = run(True, kind)
        assert name == 'result.json' and outcome['success']
        assert outcome['finish_kind'] == kind
        assert outcome['controller_outcome'] == (
            'verified_success' if kind == 'visual_verify'
            else kind + '_with_independent_task_success')
    for bad in ('abort', '', None):
        try:
            run(False, bad)
        except ValueError:
            pass
        else:
            raise AssertionError('undeclared finish kind accepted')
    try:
        classify({'success': 1}, finish_kind='visual_verify', exit_code=0,
                 proposals_executed=0, journal_calls=0, reason='bad', arm='control')
    except ValueError:
        pass
    else:
        raise AssertionError('non-boolean score accepted')
    print({'passed': 12, 'invalid_rejected': 4})


if __name__ == '__main__':
    main()
