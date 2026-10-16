"""Explicit MAP01 process-incarnation policy over unchanged release telemetry."""
from copy import deepcopy
from functools import partial
import time

from doom_owner_thread_release_batch_backend_v1 import Backend as Previous
from input_transition_owner_v4 import InputOwner as TransitionOwner
from input_owner_v12 import InputOwner as NativeOwner
from target_process_identity_v1 import IdentityReader
from executor_v3 import DecisionRequired


class Backend(Previous):
    def __init__(self, session, out, emit, signal_readers, *, window_lifecycle=False):
        if type(window_lifecycle) is not bool:
            raise ValueError('window_lifecycle must be boolean')
        self._external_emit = emit
        self._capture_samples = None
        self._source_identity = None
        self._source_window_identity = None
        self.window_identity = IdentityReader(session.name) if window_lifecycle else None
        self.capture_identity = IdentityReader(session.name)
        try:
            super().__init__(session, out, self._emit_identity, signal_readers)
            self.owner.close()
            options = dict(process_identity=True)
            if window_lifecycle: options.update(window_lifecycle=True, _window_reader=self.window_identity)
            self.owner = TransitionOwner(session.name, _owner_cls=partial(NativeOwner, **options))
        except BaseException as error:
            self.capture_identity.close()
            if self.window_identity is not None: self.window_identity.close()
            if hasattr(self, 'owner'):
                try:
                    self.owner.close()
                except BaseException as cleanup_error:
                    error.add_note('identity backend startup cleanup failed: ' + type(cleanup_error).__name__)
            raise

    def binding(self):
        value = super().binding()
        xid = value.get('surface')
        if type(xid) is not int or xid <= 1:
            raise DecisionRequired('process identity requires an observed target surface')
        try:
            digest = self.capture_identity.read(xid,
                perf_deadline_ns=time.perf_counter_ns() + 1_000_000_000)
            window = (self.window_identity.read_window(xid,
                perf_deadline_ns=time.perf_counter_ns()+1_000_000_000)
                if self.window_identity is not None else None)
        except Exception as error:
            raise DecisionRequired('capture process identity unavailable') from error
        if self._capture_samples is not None:
            self._capture_samples.append((deepcopy(value), digest, window))
        return value

    def _emit_identity(self, event):
        is_source = event.get('event') in ('typed_observation', 'observation')
        if is_source:
            samples = self._capture_samples
            if (type(samples) is not list or len(samples) != 2 or samples[0] != samples[1] or
                    samples[1][0] != event.get('pointer_binding')):
                raise DecisionRequired('process identity changed across capture')
            identity = {'sequence': event['sequence'], 'surface': samples[1][0]['surface'],
                        'digest': samples[1][1]}
            event = dict(event, target_process_identity=identity)
            if self.window_identity is not None:
                event['target_window_identity'] = dict(sequence=identity['sequence'], surface=identity['surface'], digest=samples[1][2])
        self._external_emit(event)
        if is_source and event['event'] == 'observation':
            self._source_identity = (identity['sequence'], identity['surface'], identity['digest'])
            if self.window_identity is not None:
                self._source_window_identity = (identity['sequence'], identity['surface'], samples[1][2])

    def snapshot(self, identifier, index):
        self._source_identity = None
        self._source_window_identity = None
        self._capture_samples = []
        try:
            return super().snapshot(identifier, index)
        finally:
            self._capture_samples = None

    def bind_lease_source(self, lease, expected_sequence):
        if hasattr(lease, 'target_process_identity'):
            raise DecisionRequired('lease process identity is already bound')
        source = self._source_identity
        binding = deepcopy(self.observed_pointer)
        if (type(source) is not tuple or source[0] != expected_sequence or
                expected_sequence != self.sequence or type(binding) is not dict or
                binding.get('surface') != source[1] or self.observed_focus != binding.get('focus')):
            raise DecisionRequired('fresh complete process-bound observation required')
        if self.window_identity is not None:
            window = self._source_window_identity
            if (hasattr(lease, 'target_window_identity') or type(window) is not tuple
                    or window[:2] != source[:2]):
                raise DecisionRequired('fresh complete window-bound observation required')
            lease.target_window_identity = (*window, lease.deadline)
        lease.target_process_identity = (*source, lease.deadline)
        lease.expected_focus = binding['focus']
        lease.expected_surface = binding['surface']
        lease.expected_geometry = deepcopy(binding['geometry'])

    def close(self):
        self.capture_identity.close()
        if self.window_identity is not None: self.window_identity.close()
        return super().close()
