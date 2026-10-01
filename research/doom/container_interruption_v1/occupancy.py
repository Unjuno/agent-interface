"""Fail-closed any-key occupancy bounds in an explicitly measured clock window.

Normal release uses v3 caller brackets. Interrupted input uses a verified empty
boundary as an upper bound, with ZERO certified lower occupancy: an ordinary
key-up edge cannot be inferred from a later cleanup call. No controller authority
is created here. These are source-conditioned owner-commanded intervals, not
continuous physical-keymap measurement and not useful-task-effect evidence.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Iterable


class EvidenceError(ValueError):
    """The trace cannot establish the requested interval."""


def integer(value, name):
    if type(value) is not int or value < 0:
        raise EvidenceError(f"{name}: nonnegative integer required")
    return value


def identity(value, name):
    if not isinstance(value, str) or not value:
        raise EvidenceError(f"{name}: nonempty string required")
    return value


def union_ns(intervals: Iterable[tuple[int, int]], start: int, end: int) -> int:
    """Clip before union: simultaneous keys count once, never once per key."""
    integer(start, 'window start'); integer(end, 'window end')
    if end < start:
        raise EvidenceError('inverted window')
    clipped = []
    for a, b in intervals:
        integer(a, 'interval start'); integer(b, 'interval end')
        if b < a:
            raise EvidenceError('inverted interval')
        a, b = max(a, start), min(b, end)
        if a < b:
            clipped.append((a, b))
    total = 0
    right = start
    for a, b in sorted(clipped):
        total += max(0, b - max(a, right))
        right = max(right, b)
    return total


def _empty(record):
    return (isinstance(record, dict) and record.get('verified') is True
            and record.get('keys_down') == [] and record.get('buttons_down') == []
            and type(record.get('verified_ns')) is int)


def analyze_program(events: list[dict], program_id: str, start_ns: int, end_ns: int) -> dict:
    """Analyze one accepted lease. Missing releases must never become coast=0.

    Inputs must be full append-order events from one serialized runtime. Event
    identity is the accepted intent token; historical down rows have no program id.
    Repeated keys are paired FIFO, but concurrent duplicate downs are rejected.
    """
    identity(program_id, 'program id')
    integer(start_ns, 'window start'); integer(end_ns, 'window end')
    if end_ns <= start_ns:
        raise EvidenceError('positive measured window required')
    accepted = [r for r in events if r.get('event') == 'accepted' and r.get('id') == program_id]
    terminals = [r for r in events if r.get('event') == 'terminal' and r.get('id') == program_id]
    if len(accepted) != 1 or len(terminals) != 1:
        raise EvidenceError('one accepted record and one terminal required')
    accepted, terminal = accepted[0], terminals[0]
    token = identity(accepted.get('intent_token'), 'accepted intent token')
    if sum(r.get('event') == 'accepted' and r.get('intent_token') == token for r in events) != 1:
        raise EvidenceError('intent token reused by another acceptance')
    accepted_ns = integer(accepted.get('accepted_ns'), 'accepted_ns')
    terminal_ns = integer(terminal.get('terminal_ns'), 'terminal_ns')
    if terminal_ns < accepted_ns:
        raise EvidenceError('terminal precedes acceptance')
    cleanup = terminal.get('release')
    if not _empty(cleanup):
        raise EvidenceError('terminal empty release unverified')
    if cleanup.get('intent_token') not in (None, token):
        raise EvidenceError('terminal release token mismatch')
    cleanup_ns = integer(cleanup['verified_ns'], 'terminal verified_ns')
    if not accepted_ns <= cleanup_ns <= terminal_ns:
        raise EvidenceError('terminal release outside program lifetime')

    interruption = terminal.get('interruption')
    interrupt_record = None
    if interruption is not None:
        if not isinstance(interruption, dict) or interruption.get('intent_token') != token:
            raise EvidenceError('interruption token mismatch')
        interrupt_record = interruption.get('record')
        if not _empty(interrupt_record):
            raise EvidenceError('interruption release unverified')
        if not accepted_ns <= interrupt_record['verified_ns'] <= terminal_ns:
            raise EvidenceError('interruption outside program lifetime')

    known_tokens = {r.get('intent_token') for r in events if r.get('event') == 'accepted'}
    for row in events:
        if row.get('event') == 'input_admission':
            if not isinstance(row.get('intent_token'), str) or row['intent_token'] not in known_tokens:
                raise EvidenceError('unattributed input admission')

    pending = defaultdict(deque)
    intervals = []
    uncertain = []
    admission_count = release_count = 0
    for row in events:
        kind = row.get('event')
        if kind == 'input_admission' and row.get('intent_token') == token:
            key = identity(row.get('key'), 'admission key')
            a = integer(row.get('admitted_ns'), 'admitted_ns')
            b = integer(row.get('input_ack_ns'), 'input_ack_ns')
            if not accepted_ns <= a <= b <= terminal_ns:
                raise EvidenceError('admission clock order')
            if pending[key]:
                raise EvidenceError('duplicate down while same key remains unpaired')
            pending[key].append(row)
            admission_count += 1
        elif kind == 'input_release_transition' and (
                row.get('intent_token') == token or row.get('release_batch_identifier') == program_id):
            if row.get('intent_token') != token or row.get('release_batch_identifier') != program_id:
                raise EvidenceError('release program/token mismatch')
            if row.get('operation') != 'up':
                raise EvidenceError('keyboard-only occupancy cannot absorb pointer releases')
            key = identity(row.get('key'), 'release key')
            if not pending[key]:
                raise EvidenceError('duplicate or orphan release')
            down = pending[key].popleft()
            a = down['admitted_ns']; b = down['input_ack_ns']
            c = integer(row.get('release_call_started_ns'), 'release_call_started_ns')
            d = integer(row.get('release_call_returned_ns'), 'release_call_returned_ns')
            if not b <= c <= d <= terminal_ns:
                raise EvidenceError('release clock order')
            if row.get('transition_schema') != 'input-release-transition-v3':
                raise EvidenceError('unsupported normal release schema')
            ordinary = (row.get('owner_transition_verified') is True
                        and row.get('ordinary_release_candidate') is True)
            # A prior/overlapping asynchronous release makes the explicit up a
            # cleanup receipt, not proof that input survived until its request.
            prior_async = interrupt_record is not None and interrupt_record['verified_ns'] <= d
            if ordinary and not prior_async:
                intervals.append({'key': key, 'kind': 'normal', 'lower': [b, c], 'upper': [a, d]})
            else:
                uncertain.append((down, d))
            release_count += 1

    for queue in pending.values():
        for down in queue:
            uncertain.append((down, cleanup_ns))
    if uncertain and terminal.get('status') == 'completed':
        raise EvidenceError('completed program has missing/unverified direct release')
    if uncertain and terminal.get('status') not in ('cancelled', 'expired', 'needs_decision', 'failed'):
        raise EvidenceError('unrecognized interruption lifecycle')
    for down, upper_end in uncertain:
        verified_end = min(upper_end, cleanup_ns)
        if interrupt_record is not None:
            verified_end = min(verified_end, interrupt_record['verified_ns'])
        if verified_end < down['input_ack_ns']:
            raise EvidenceError('verified empty predates this input acknowledgement')
        intervals.append({'key': down['key'], 'kind': 'interrupted_censored',
                          'lower': None, 'upper': [down['admitted_ns'], verified_end]})

    lo = union_ns([tuple(x['lower']) for x in intervals if x['lower'] is not None], start_ns, end_ns)
    hi = union_ns([tuple(x['upper']) for x in intervals], start_ns, end_ns)
    duration = end_ns - start_ns
    if not 0 <= lo <= hi <= duration:
        raise EvidenceError('interval inclusion failed')
    return {'schema': 'windowed-any-key-occupancy-v1', 'program_id': program_id,
            'intent_token': token, 'window_start_ns': start_ns, 'window_end_ns': end_ns,
            'window_ns': duration, 'admission_count': admission_count,
            'explicit_release_count': release_count, 'intervals': intervals,
            'retained_lower_ns': lo, 'retained_upper_ns': hi,
            'no_input_lower_ns': duration-hi, 'no_input_upper_ns': duration-lo,
            'measurement_class': 'INTERRUPTION_CENSORED' if uncertain else 'NORMAL_DIRECT_OR_EMPTY',
            'exact_physical_occupancy': False, 'grants_input_authority': False}
