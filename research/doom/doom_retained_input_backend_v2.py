"""Typed DOOM backend with one post-batch sample after all key releases."""
from doom_typed_coast_backend_v1 import Backend as Previous, suite
from input_transition_owner_v2 import InputOwner


class Backend(Previous):
    def __init__(self, session, out, emit, signal_readers):
        super().__init__(session, out, emit, signal_readers)
        self.owner.close()
        self.owner = InputOwner(session.name)
        self._release_receipts = []

    @staticmethod
    def _interruption(lease):
        if lease is None or not hasattr(lease, 'interruption_snapshot'):
            return None
        return lease.interruption_snapshot()

    def raw(self, key, down):
        if down:
            if self._release_receipts:
                raise AssertionError('release receipt batch leaked into key-down')
            record = self.owner.call('down', self.lease, key)
            self.held.add(key)
            if record is not None:
                self.emit(record)
            return

        was_backend_owned = key in self.held
        receipt = self.owner.call('up', self.lease, key)
        self.held.discard(key)
        if not isinstance(receipt, dict) or receipt.get('event') != 'input_release_receipt_v2':
            raise AssertionError('v2 release receipt required')
        receipt = dict(receipt)
        receipt['backend_owned_before_release'] = was_backend_owned
        self._release_receipts.append(receipt)

        # Critical non-perturbation rule: no sample and no emit while any key in
        # this logical hold remains to be released.
        if self.held:
            return

        state = self.owner.call('input_state')
        interruption = self._interruption(self.lease)
        receipts = self._release_receipts
        self._release_receipts = []
        token = getattr(self.lease, 'intent_token', None)
        tokens_match = all(row.get('intent_token') == token for row in receipts)
        ownership_match = all(row.get('backend_owned_before_release') is True for row in receipts)
        owner_empty = isinstance(state, dict) and state.get('owned_keycodes') == []
        verified = bool(receipts and tokens_match and ownership_match and owner_empty and interruption is None)

        event = {
            'event': 'input_release_batch_v2',
            'owner_id': state.get('owner_id') if isinstance(state, dict) else None,
            'intent_token': token,
            'receipts': receipts,
            'keys': [row.get('key') for row in receipts],
            'release_call_started_ns': min(row['release_call_started_ns'] for row in receipts),
            'release_call_returned_ns': max(row['release_call_returned_ns'] for row in receipts),
            'owner_sample_after_started_ns': state.get('sample_started_ns') if isinstance(state, dict) else None,
            'owner_sample_after_finished_ns': state.get('sample_finished_ns') if isinstance(state, dict) else None,
            'owned_keycodes_after': state.get('owned_keycodes') if isinstance(state, dict) else None,
            'owner_transition_verified': verified,
            'physical_verification_authoritative': False,
            'grants_input_authority': False,
            'measurement_contract': (
                'all explicit key releases complete before one post-batch owner-state sample '
                'and one aggregate telemetry publication'
            ),
        }
        if isinstance(interruption, dict):
            inner = interruption.get('record') if isinstance(interruption.get('record'), dict) else interruption
            if isinstance(inner, dict):
                event['interruption_reason'] = inner.get('reason')
                event['interruption_verified_ns'] = inner.get('verified_ns')
        self.emit(event)
