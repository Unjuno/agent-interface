"""First interruption evidence belongs to a lease instance, never a deadline lookup."""
import copy
import threading
import uuid
from lease import Lease as Previous

REASONS = frozenset(('focus_changed', 'surface_changed', 'expired', 'cancelled', 'stop_requested'))


class Lease(Previous):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.intent_token = uuid.uuid4().hex
        self._cause_lock = threading.Lock()
        self._cause = None

    def record_interruption(self, record):
        if record.get('event') != 'owner_release' or record.get('reason') not in REASONS:
            return
        with self._cause_lock:
            if self._cause is None:
                self._cause = {'intent_token': self.intent_token, 'record': copy.deepcopy(record)}

    def interruption_snapshot(self):
        with self._cause_lock:
            return copy.deepcopy(self._cause)
