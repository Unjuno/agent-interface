"""Pure sampled handoff check; no transport, lease renewal, or input authority.

Inputs must come from the validated durable continuation. A successful result
is not widget identity, an atomic focus guarantee, or task completion.
"""


def evaluate(action_id, activation_steps, terminal, source, fresh, clock):
    def refuse(reason):
        return {'eligible': False, 'reason': reason, 'authority': 'none'}

    if (len(activation_steps) != 2 or
            activation_steps[0].get('op') != 'pointer_click' or
            activation_steps[1] != {'op': 'observe'}):
        return refuse('not_activation_program')
    if terminal.get('id') != action_id or terminal.get('status') != 'completed':
        return refuse('activation_not_completed')
    if terminal.get('steps_completed') != 2 or terminal.get('interruption') is not None:
        return refuse('activation_partial_or_interrupted')
    release = terminal.get('release') or {}
    if (release.get('verified') is not True or release.get('keys_down') != [] or
            release.get('buttons_down') != []):
        return refuse('release_not_verified')
    timestamps = [release.get('verified_ns'), terminal.get('terminal_ns'),
                  fresh.get('capture_ns'), clock.get('runtime_ns')]
    if any(type(t) is not int for t in timestamps):
        return refuse('invalid_timestamps')
    released, ended, captured, now = timestamps
    if not released <= ended < captured <= now:
        return refuse('not_post_terminal_observation')
    if now - captured >= 1_000_000_000:
        return refuse('observation_expired')
    if (fresh.get('sequence', -1) <= source.get('sequence', -1) or
            clock.get('sequence') != fresh.get('sequence')):
        return refuse('sequence_mismatch')
    binding = source.get('pointer_binding')
    if (not isinstance(binding, dict) or not binding.get('focus') or
            not binding.get('surface') or not binding.get('geometry') or
            fresh.get('pointer_binding') != binding):
        return refuse('binding_changed_or_missing')
    point = [activation_steps[0].get('x'), activation_steps[0].get('y')]
    for side in ('before', 'after'):
        state = fresh.get('input_state_' + side) or {}
        if (fresh.get('input_focus_' + side) != binding['focus'] or
                state.get('focus') != binding['focus'] or
                fresh.get('pointer_context_' + side) != binding):
            return refuse('focus_or_context_changed')
        if (state.get('owned_buttons') != [] or state.get('owned_keycodes') != [] or
                state.get('physical_pointer_mask') != 0):
            return refuse('input_not_idle')
        if state.get('pointer') != point:
            return refuse('pointer_moved')
    return {'eligible': True, 'expected_sequence': fresh['sequence'],
            'authority': 'none',
            'scope': 'sampled post-activation context; not semantic or atomic',
            'input_deadline': 'caller must explicitly bound a new keyboard-only program'}
