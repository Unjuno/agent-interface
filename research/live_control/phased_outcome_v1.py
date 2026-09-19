"""Typed presentation over validated phased-submit-v1 evidence, no authority.

No GUI/application-effect inference and no transport. Raw reports remain the
audit source. A step can have input acknowledgments even when steps_completed
is zero. Such acknowledgments are not proof of the requested application effect.
"""
from copy import deepcopy


def present(report):
    if report.get('format') != 'phased-submit-v1' or report.get('authority') != 'none':
        raise ValueError('validated phased-submit-v1 report required')
    exchanges = report['exchanges']
    programs = []
    pending = False
    closed = False
    release_unknown = False
    for result in exchanges:
        state = result['state']
        if state.get('format') != 'durable-submit-v4' or state.get('authority') != 'none':
            raise ValueError('validated durable-submit-v4 result required')
        pending = state['pending'] is not None
        closed = state['continuation']['channel_closed']
        command = result['request'].get('command', {})
        if command.get('op') != 'submit' or not any(s['op'] != 'observe' for s in command['steps']):
            continue
        action_id = command['id']
        records = [e for e in result['reply']['records'] if e.get('id') == action_id]
        admitted = any(e['event'] == 'accepted' for e in records)
        resolution = state.get('last_resolution') or {}
        terminal = resolution.get('terminal')
        if not terminal or terminal.get('id') != action_id:
            terminal = None
        rejected = resolution.get('rejected')
        if not rejected or rejected.get('id') != action_id:
            rejected = None
        release = (terminal or {}).get('release') or {}
        released = (release.get('verified') is True and
                    release.get('keys_down') == [] and release.get('buttons_down') == [])
        release_unknown |= terminal is not None and not released
        acknowledgments = [e for e in records if e['event'] in ('input_admission', 'pointer_admission')
                           and type(e.get('input_ack_ns')) is int]
        programs.append({'action_id': action_id,
                         'admission': 'confirmed' if admitted else 'rejected' if rejected else 'unconfirmed',
                         'started_steps': sorted({e['step'] for e in records if e['event'] == 'step_started'}),
                         'input_ack_events': len(acknowledgments),
                         'terminal_status': terminal['status'] if terminal else None,
                         'steps_completed': terminal['steps_completed'] if terminal else None,
                         'release_verified_empty': released if terminal else None,
                         'effect': 'unknown'})
    unresolved = any(p['terminal_status'] is None and p['admission'] != 'rejected' for p in programs)
    if pending:
        disposition = 'protocol_pending'
    elif not exchanges and report.get('reason') == 'target_refused':
        disposition = 'not_submitted'
    elif unresolved or not programs:
        disposition = 'evidence_unresolved'
    elif any(p['admission'] == 'confirmed' and p['terminal_status'] in
             ('needs_decision', 'expired', 'cancelled', 'failed') for p in programs):
        disposition = 'program_interrupted'
    elif (report['status'] == 'completed' and all(p['admission'] == 'confirmed' and
          p['terminal_status'] == 'completed' and p['release_verified_empty'] for p in programs)):
        disposition = 'programs_completed'
    elif any(p['admission'] == 'confirmed' for p in programs):
        disposition = 'partial_sequence_stopped'
    else:
        disposition = 'admission_rejected'
    blocked = pending or closed or release_unknown or disposition == 'evidence_unresolved'
    return {'format': 'phased-outcome-v1', 'authority': 'none',
            'disposition': disposition, 'original_reason': report.get('reason'),
            'programs': programs, 'pending_protocol': pending, 'channel_closed': closed,
            'tail_submitted': report['tail_submitted'],
            'application_effect': 'unknown; not inferred from program status, input ACK or image equality',
            'new_input': 'blocked' if blocked else 'requires_new_decision_and_fresh_admission',
            'automatic_retry': 'not_authorized_by_this_view',
            'scope': 'delivery/program evidence only; no semantic task score'}


def feedback(original, report):
    """Replace the misleading aggregate label, retaining original raw resolution."""
    result = deepcopy(original)
    view = present(report)
    result['phase_status'] = view['disposition']
    result['execution_outcome'] = view
    return result
