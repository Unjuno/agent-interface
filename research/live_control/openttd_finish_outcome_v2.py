"""Classify OpenTTD task score and controller finish reason as separate facts."""


KINDS = {'visual_verify', 'bounded_turn_limit', 'typed_model_safe_stop', 'supervisor_cleanup'}


def classify(evaluation, *, finish_kind, exit_code, proposals_executed,
             journal_calls, reason, arm):
    if finish_kind not in KINDS:
        raise ValueError('declared finish_kind required')
    if type(evaluation.get('success')) is not bool:
        raise ValueError('boolean independent evaluation success required')
    common = {
        'exit_code': exit_code,
        'arm': arm,
        'proposals_executed': proposals_executed,
        'journal_calls': journal_calls,
        'finish_kind': finish_kind,
        'reason': reason,
        'evaluation': evaluation,
        'success': evaluation['success'],
    }
    if evaluation['success']:
        return 'result.json', {
            **common,
            'controller_outcome': (
                'verified_success' if finish_kind == 'visual_verify'
                else finish_kind + '_with_independent_task_success'),
            'scope': 'independent task score and controller finish reason are both retained',
        }
    failure_mode = {
        'visual_verify': 'visual_verify_false_positive',
        'bounded_turn_limit': 'bounded_turn_limit',
        'typed_model_safe_stop': 'typed_model_safe_stop',
        'supervisor_cleanup': 'supervisor_cleanup',
    }[finish_kind]
    return 'failure-evaluation.json', {
        **common,
        'controller_outcome': failure_mode,
        'failure_mode': failure_mode,
    }
