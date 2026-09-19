"""Non-perturbing explicit-release receipts around unchanged InputOwner v10.

Unlike v1, explicit up/button_up does not perform a post-release owner sample.
It only brackets the existing synchronous v10 call with caller timestamps. A
backend may batch these cheap receipts and sample state only after all keys in a
logical release batch have been released.
"""
import time

from input_owner_v10 import InputOwner as Previous


class InputOwner:
    def __init__(self, display_name, _owner_cls=Previous):
        self._inner = _owner_cls(display_name)

    @property
    def owner_id(self):
        return self._inner.owner_id

    @property
    def records(self):
        return list(self._inner.records)

    def close(self):
        return self._inner.close()

    @staticmethod
    def _intent_token(lease):
        return getattr(lease, 'intent_token', None) if lease is not None else None

    def _decorate(self, result, lease):
        if not isinstance(result, dict):
            return result
        decorated = dict(result)
        token = self._intent_token(lease)
        if token is not None:
            decorated.setdefault('intent_token', token)
        return decorated

    def call(self, operation, lease=None, key=None):
        if operation not in ('up', 'button_up'):
            started_ns = time.perf_counter_ns() if operation in ('release', 'close') else None
            result = self._inner.call(operation, lease, key)
            returned_ns = time.perf_counter_ns() if started_ns is not None else None
            result = self._decorate(result, lease)
            if isinstance(result, dict) and result.get('event') == 'owner_release':
                result.setdefault('release_call_started_ns', started_ns)
                result.setdefault('release_call_returned_ns', returned_ns)
            return result

        release_call_started_ns = time.perf_counter_ns()
        result = self._inner.call(operation, lease, key)
        release_call_returned_ns = time.perf_counter_ns()
        if result is not None:
            raise AssertionError('InputOwner v10 explicit release unexpectedly returned payload')

        record = {
            'event': 'input_release_receipt_v2',
            'operation': operation,
            'key' if operation == 'up' else 'button': key,
            'owner_id': self.owner_id,
            'intent_token': self._intent_token(lease),
            'valid_until_ns': getattr(lease, 'deadline', None) if lease is not None else None,
            'release_call_started_ns': release_call_started_ns,
            'release_call_returned_ns': release_call_returned_ns,
            'grants_input_authority': False,
        }
        return record
