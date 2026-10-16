"""Presentation of validated durable results; never input authority or task score."""
from copy import deepcopy


def present(result):
    state = result['state']
    if state['format'] != 'durable-submit-v4' or state['authority'] != 'none':
        raise ValueError('validated durable result required')
    pending = state['pending']
    continuation = state['continuation']
    resolution = state['last_resolution']
    action = result['request'].get('action_id')
    terminal = (resolution or {}).get('terminal')
    rejected = (resolution or {}).get('rejected')
    matched = (isinstance(action, str) and bool(action) and
               any(record and record.get('id') == action for record in (terminal, rejected)))
    closed = continuation['channel_closed']
    status = 'unresolved' if pending is not None else ('resolved' if matched else 'no_pending')
    conflict = bool(pending and pending['conflict'])
    return {
        'format': 'recovery-view-v1', 'authority': 'none',
        'status': status, 'read_action_id': action,
        'channel': 'closed' if closed else 'not_reported_closed',
        'runtime_liveness': 'not_established_by_channel_status',
        'new_input': 'blocked' if pending is not None or closed else 'requires_fresh_admission',
        'next_step': ('inspect_channel_and_runtime' if closed else
                      'inspect_conflicting_evidence' if conflict else
                      'explicit_read_or_inspect' if pending is not None else
                      'interpret_observation_and_resolution'),
        'pending': deepcopy(pending),
        'resolution_for_read_action': deepcopy(resolution) if matched and pending is None else None,
        'last_resolution_historical': deepcopy(resolution),
        'observation': deepcopy(continuation['observation']),
        'observation_scope': 'latest received sample; not a freshness or target-identity guarantee',
        'task_completion': 'not_scored_here',
    }
