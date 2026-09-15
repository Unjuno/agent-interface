"""No-authority retry advice for one application-acknowledged effect.

Requires trusted application receipts with session/operation/attempt identity.
A timeout is missing evidence, never proof of non-application. This is not an
input owner, a durable idempotency service, or a general GUI outcome oracle.
"""
from __future__ import annotations


def tick(value: int) -> int:
    if type(value) is not int or value < 0:
        raise ValueError('timestamp must be an exact nonnegative integer')
    return value


class OutcomeFence:
    def __init__(self, session: str, operation: str, issued_ns: int) -> None:
        if any(type(x) is not str or not x for x in (session, operation)):
            raise ValueError('nonempty session and operation required')
        self.session, self.operation = session, operation
        self.attempt = 1
        self.issued_ns = tick(issued_ns)
        self.status = 'PENDING'
        self.last_receipt_ns = issued_ns
        self.release_ns: int | None = None
        self.ignored = 0

    def observe(self, receipt: dict, now_ns: int) -> str:
        now_ns = tick(now_ns)
        if now_ns < self.issued_ns:
            raise ValueError('observer clock precedes input')
        if not isinstance(receipt, dict):
            self.status = 'INVALID_EVIDENCE'
            return self.status
        identity = (receipt.get('session'), receipt.get('operation'), receipt.get('attempt'))
        if any(type(x) is not str or not x for x in identity[:2]) or type(identity[2]) is not int:
            self.status = 'INVALID_EVIDENCE'
            return self.status
        if identity != (self.session, self.operation, self.attempt):
            self.ignored += 1
            return 'IGNORED_OTHER_IDENTITY'
        if self.status == 'INVALID_EVIDENCE':
            return self.status
        timestamp, state = receipt.get('observed_ns'), receipt.get('status')
        if (receipt.get('schema') != 'application-effect-receipt-v1'
                or type(timestamp) is not int
                or not self.issued_ns <= timestamp <= now_ns
                or timestamp < self.last_receipt_ns
                or state not in ('PENDING', 'COMMITTED', 'REJECTED_NO_EFFECT')):
            self.status = 'INVALID_EVIDENCE'
            return self.status
        if state == 'REJECTED_NO_EFFECT' and receipt.get('no_effect_final') is not True:
            self.status = 'INVALID_EVIDENCE'
            return self.status
        if self.status in ('COMMITTED', 'REJECTED_NO_EFFECT') and state != self.status:
            self.status = 'INVALID_EVIDENCE'
            return self.status
        self.last_receipt_ns, self.status = timestamp, state
        return state

    def released(self, verified: bool, observed_ns: int) -> None:
        observed_ns = tick(observed_ns)
        if type(verified) is not bool or verified is not True or observed_ns < self.issued_ns:
            raise ValueError('current verified empty release required')
        self.release_ns = observed_ns

    def may_retry(self) -> bool:
        return self.status == 'REJECTED_NO_EFFECT' and self.release_ns is not None

    def begin_retry(self, issued_ns: int) -> None:
        issued_ns = tick(issued_ns)
        if not self.may_retry() or issued_ns <= max(self.last_receipt_ns, self.release_ns):
            raise ValueError('retry needs a later admission after final no-effect and release')
        self.attempt += 1
        self.issued_ns = self.last_receipt_ns = issued_ns
        self.status, self.release_ns = 'PENDING', None

    def finish_observation(self) -> str:
        return 'UNKNOWN' if self.status == 'PENDING' else self.status
