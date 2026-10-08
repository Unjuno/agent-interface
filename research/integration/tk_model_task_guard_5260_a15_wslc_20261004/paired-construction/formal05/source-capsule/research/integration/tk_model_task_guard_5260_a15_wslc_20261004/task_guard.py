"""Trusted caller-side task consistency, never input or completion authority.

Snapshots are supplied by a separately frozen cooperative app. This module
does not authenticate their producer, emit native input, read task files,
replace a model decision, or make focus and input atomic.
"""
from copy import deepcopy
import re

SNAPSHOT_FIELDS = {'binding', 'nonce', 'sequence', 'started_ns', 'completed_ns',
                   'target', 'decoy', 'focus'}
BINDING_FIELDS = {'pid', 'token', 'root_id', 'target_id', 'freeze_sha256'}
REVIEW_FIELDS = {'decision', 'observed_target', 'observed_decoy', 'prefix'}


def _binding_valid(binding):
    return (type(binding) is dict and set(binding) == BINDING_FIELDS
            and all(type(binding[name]) is int and binding[name] > 0
                    for name in ('pid', 'root_id', 'target_id'))
            and type(binding['token']) is str and bool(binding['token'])
            and type(binding['freeze_sha256']) is str
            and re.fullmatch('[0-9a-f]{64}', binding['freeze_sha256']) is not None)


def _snapshot_error(current, expected_binding, request_nonce, minimum_sequence,
                    boundary_ns, now_ns, max_age_ns):
    if (type(current) is not dict or set(current) != SNAPSHOT_FIELDS
            or not _binding_valid(expected_binding)
            or not _binding_valid(current['binding'])
            or type(request_nonce) is not str or not request_nonce
            or type(current['nonce']) is not str
            or any(type(current[name]) is not str
                   for name in ('target', 'decoy', 'focus'))
            or type(minimum_sequence) is not int or minimum_sequence < 1
            or any(type(value) is not int or value < 1
                   for value in (boundary_ns, now_ns))
            or type(max_age_ns) is not int or max_age_ns < 0
            or any(type(current[name]) is not int or current[name] < 1
                   for name in ('sequence', 'started_ns', 'completed_ns'))):
        return 'MALFORMED_SNAPSHOT'
    if current['binding'] != expected_binding:
        return 'BINDING_CHANGED'
    if current['nonce'] != request_nonce or current['sequence'] <= minimum_sequence:
        return 'SNAPSHOT_NOT_NEW'
    if not boundary_ns < current['started_ns'] <= current['completed_ns'] <= now_ns:
        return 'SNAPSHOT_CLOCK'
    # Age from acquisition start, not just completion, is conservative.
    if now_ns - current['started_ns'] > max_age_ns:
        return 'SNAPSHOT_EXPIRED'
    if current['focus'] != 'target':
        return 'FOCUS_NOT_TARGET'
    return None


def _result(status, reason, **details):
    return {'status': status, 'reason': reason, 'grants_input_authority': False,
            'task_complete': False, **details}


def decide_review(review, current, *, wanted, expected_binding, request_nonce,
                  image_sequence, response_seen_ns, now_ns,
                  max_age_ns=50_000_000):
    """A semantic proposal still needs ordinary fresh native input admission."""
    if (type(review) is not dict or set(review) != REVIEW_FIELDS
            or any(type(value) is not str for value in review.values())
            or review['decision'] not in ('NO_REPAIR', 'INSERT_PREFIX', 'REFUSE')
            or (len(review['prefix']) != 1 if review['decision'] == 'INSERT_PREFIX'
                else review['prefix'] != '')):
        return _result('YIELD', 'MALFORMED_REVIEW')
    if type(wanted) is not str or not wanted:
        return _result('YIELD', 'MALFORMED_TASK')
    error = _snapshot_error(current, expected_binding, request_nonce,
                            image_sequence, response_seen_ns, now_ns, max_age_ns)
    if error:
        return _result('YIELD', error)
    if (review['observed_target'] != current['target']
            or review['observed_decoy'] != current['decoy']):
        return _result('YIELD', 'MODEL_STATE_MISMATCH')
    if review['decision'] == 'REFUSE':
        return _result('YIELD', 'MODEL_REFUSED')
    if current['decoy']:
        return _result('YIELD', 'DECOY_NOT_EMPTY')
    details = {'binding': deepcopy(current['binding']),
               'baseline_sequence': current['sequence'],
               'baseline_completed_ns': current['completed_ns'],
               'prior_target': current['target'], 'expected_target': wanted}
    if review['decision'] == 'NO_REPAIR':
        if current['target'] != wanted:
            return _result('YIELD', 'TASK_NOT_EXACT')
        return _result('PLAN_SAVE', 'CURRENT_TASK_EXACT', **details)
    # Verify only the supplied semantic repair. Never synthesize a new prefix.
    if not current['target'] or review['prefix'] + current['target'] != wanted:
        return _result('YIELD', 'PREFIX_NOT_TASK_REPAIR')
    return _result('PLAN_PREFIX', 'CURRENT_PREFIX_REPAIR',
                   prefix=review['prefix'], **details)


def verify_repair_effect(proposal, current, *, request_nonce,
                         action_finished_ns, now_ns, max_age_ns=50_000_000):
    """A later exact typed effect may propose Save, not certify task completion."""
    required = {'status', 'reason', 'grants_input_authority', 'task_complete',
                'binding', 'baseline_sequence', 'prior_target',
                'expected_target', 'prefix', 'baseline_completed_ns'}
    if (type(proposal) is not dict or set(proposal) != required
            or proposal['status'] != 'PLAN_PREFIX'
            or proposal['grants_input_authority'] is not False
            or proposal['task_complete'] is not False
            or any(type(proposal[name]) is not str
                   for name in ('prefix', 'prior_target', 'expected_target'))
            or len(proposal['prefix']) != 1 or not proposal['prior_target']
            or proposal['prefix'] + proposal['prior_target'] != proposal['expected_target']):
        return _result('YIELD', 'MALFORMED_REPAIR_PLAN')
    if (type(proposal['baseline_completed_ns']) is not int
            or proposal['baseline_completed_ns'] < 1
            or type(action_finished_ns) is not int
            or action_finished_ns <= proposal['baseline_completed_ns']):
        return _result('YIELD', 'REPAIR_CLOCK')
    error = _snapshot_error(current, proposal['binding'], request_nonce,
                            proposal['baseline_sequence'], action_finished_ns,
                            now_ns, max_age_ns)
    if error:
        return _result('YIELD', error)
    if current['target'] != proposal['expected_target'] or current['decoy']:
        return _result('YIELD', 'REPAIR_EFFECT_NOT_EXACT')
    return _result('PLAN_SAVE', 'CURRENT_REPAIR_EFFECT_EXACT',
                   binding=deepcopy(current['binding']),
                   baseline_sequence=current['sequence'],
                   baseline_completed_ns=current['completed_ns'],
                   prior_target=current['target'],
                   expected_target=proposal['expected_target'])
