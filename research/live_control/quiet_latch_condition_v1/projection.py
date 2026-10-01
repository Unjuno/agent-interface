"""Read-only condition projection. Evidence/history never grants input authority.

Trusted local cooperative source only. Instance/challenge binding is not source
truth authentication. A valid read is historical immediately after acquisition;
new actions still require their own current preconditions and authority.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ReadContext:
    scope: str
    instance: str
    challenge: str
    clock_domain: str
    sent_ns: int
    received_ns: int
    decision_ns: int
    max_age_ns: int = 100_000_000


def project(history: dict, receipt: object, context: ReadContext, *,
            mode: str = 'bound_read') -> dict:
    """Produce a view without modifying either history or condition evidence."""
    if mode not in ('historical_only', 'bound_read'):
        raise ValueError('unsupported mode')
    if (type(history.get('condition_active')) is not bool or
            history.get('session') != context.scope or
            history.get('grants_input_authority') is not False):
        raise ValueError('invalid history boundary')
    pending = history.get('pending')
    if pending is not None and (type(pending) is not int or pending < 1):
        raise ValueError('invalid pending identity')
    valid, current, reason = False, 'UNKNOWN', 'UNAVAILABLE'
    if mode == 'historical_only':
        current = 'ACTIVE' if history['condition_active'] else 'CLEAR'
        reason = 'HISTORICAL_ONLY_NOT_CURRENT_EVIDENCE'
    elif type(receipt) is dict:
        expected = {'scope': context.scope, 'instance': context.instance,
                    'challenge': context.challenge, 'clock_domain': context.clock_domain}
        reason = 'BINDING_MISMATCH'
        if all(type(receipt.get(k)) is str and receipt[k] == v for k, v in expected.items()):
            names = ('read_start_ns', 'read_end_ns')
            clocks = (context.sent_ns, context.received_ns, context.decision_ns, context.max_age_ns)
            reason = 'INVALID_CLOCK_TYPE'
            if all(type(receipt.get(k)) is int for k in names) and all(type(t) is int for t in clocks):
                start, end = (receipt[k] for k in names)
                reason = 'INVALID_CLOCK_ORDER'
                if (0 < context.sent_ns <= start <= end <= context.received_ns <= context.decision_ns
                        and context.max_age_ns > 0):
                    reason = 'STALE'
                    if context.decision_ns - start <= context.max_age_ns:
                        reason = 'INVALID_CONDITION'
                        if type(receipt.get('condition')) is bool:
                            current = 'ACTIVE' if receipt['condition'] else 'CLEAR'
                            valid, reason = True, 'BOUND_CURRENT_READ'
                        elif receipt.get('condition') is None:
                            reason = 'SOURCE_UNAVAILABLE'
    attention = pending is not None or current != 'CLEAR'
    return {'current_condition': current, 'condition_evidence_valid': valid,
            'reason': reason, 'historical_condition_active': history['condition_active'],
            'pending_sequence': pending, 'last_acked': history['last_acked'],
            'next_sequence': history['next_sequence'], 'attention_required': attention,
            'grants_input_authority': False, 'history_mutated': False}
