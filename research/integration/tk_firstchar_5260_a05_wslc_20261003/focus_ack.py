"""Fail-closed first-key admission for a private app focus receipt (no input)."""


def acknowledgement_errors(ack, state, binding, seen_ns, max_age_ms):
    errors = []
    if not all(isinstance(value, dict) for value in (ack, state, binding)):
        return ['missing_receipt']
    integer_fields = ('pid','target_id','ready_ns','click_started_ns')
    if (any(type(binding.get(k)) is not int or binding[k] <= 0
            for k in integer_fields) or not isinstance(binding.get('token'), str)
            or not binding['token'] or type(seen_ns) is not int or seen_ns <= 0
            or type(max_age_ms) is not int or max_age_ms <= 0):
        return ['binding_type']
    if ack.get('schema') != 'issue5260-a05-focus-ack-v1':
        errors.append('schema')
    for field in ('token','pid','target_id'):
        if ack.get(field) != binding[field] or state.get(field) != binding[field]:
            errors.append('identity:' + field)
        if field != 'token' and (type(ack.get(field)) is not int or
                                 type(state.get(field)) is not int):
            errors.append('identity_type:' + field)
    if ack.get('widget') != 'target' or ack.get('focus_get') != 'target':
        errors.append('ack_not_target')
    if state.get('widget') != 'target':
        errors.append('state_not_target')
    ack_fields = ('event_ns','written_ns','sequence')
    if (any(type(ack.get(k)) is not int or ack[k] <= 0 for k in ack_fields) or
            any(type(state.get(k)) is not int or state[k] <= 0
                for k in ('event_ns','sequence'))):
        errors.append('receipt_type')
    else:
        if not (binding['ready_ns'] < binding['click_started_ns'] <=
                ack['event_ns'] <= ack['written_ns'] <= seen_ns):
            errors.append('receipt_clock_order')
        if seen_ns - ack['written_ns'] > max_age_ms * 1_000_000:
            errors.append('receipt_expired')
        if any(state[k] != ack[k] for k in ('event_ns','sequence')):
            errors.append('state_changed')
    return errors
