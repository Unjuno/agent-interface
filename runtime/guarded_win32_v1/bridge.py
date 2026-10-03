"""Private trusted-caller move bridge; references never create authority."""
import copy, hashlib, threading, time, uuid
from runtime.core_v1.contract import SCHEMA_PROGRAM, admit_program
from runtime.backends.win32_v1.session import Win32RuntimeSession

class BoundView:

    def __init__(self, owner):
        self.owner = owner

    @property
    def emissions(self):
        return self.owner.backend.emissions

    def monotonic_ns(self):
        return time.monotonic_ns()

    def manifest(self):
        return self.owner.backend.manifest()

    def release_all(self):
        return self.owner.backend.release_all()

    def preflight(self, p):
        return self.owner.backend.preflight(p, bound_target=self.owner.observer.target, guard=self.owner.binding_guard)

    def execute(self, p):
        return self.owner.backend.execute(p, bound_target=self.owner.observer.target, guard=self.owner.guard, preflight_guard=self.owner.binding_guard)

class MoveBridge:

    def __init__(self, observer, authorize, cancelled):
        if not callable(authorize) or not callable(cancelled):
            raise ValueError('trusted authority and cancellation required')
        self.observer = observer
        self.backend = observer.backend
        self.authorize = authorize
        self.cancelled = cancelled
        self.session = Win32RuntimeSession(BoundView(self))
        self.lock = threading.Lock()
        self.permits = {}
        self.active = None
        self.pending_verifier = None
        self.last_verifier_exit = None

    def prepare(self, alias, offset):
        if not self.lock.acquire(blocking=False):
            raise ValueError('operation active')
        try:
            if not self.verifier_idle():
                raise ValueError('verifier still active')
            if self.cancelled() is not False or self.session.recovery_required:
                raise ValueError('cancelled or recovery required')
            if not self.neutral():
                raise ValueError('input neutrality unavailable')
            resolution = self.observer.resolve_fresh(alias, offset)
            if not resolution['eligible']:
                raise ValueError('reference refused: ' + resolution['status'])
            row, _ = self.observer.get(resolution['sequence'])
            intent = {'scope': self.observer.scope, 'target': self.observer.target, 'operation': 'pointer_move', 'alias': alias, 'offset': list(offset), 'point': list(resolution['point'])}
            lease = self.authorize(copy.deepcopy(intent))
            if type(lease) is not dict or set(lease) != {'lease_id', 'expires_at_ns'} or type(lease['lease_id']) is not str or (not lease['lease_id']) or (type(lease['expires_at_ns']) is not int):
                raise ValueError('caller authority unavailable')
            deadline = min(lease['expires_at_ns'], resolution['valid_until_ns'])
            if time.monotonic_ns() >= deadline:
                raise ValueError('authority expired')
            program = {'schema': SCHEMA_PROGRAM, 'program_id': 'move-' + uuid.uuid4().hex, 'source': {'observation_seq': row['sequence'], 'binding_revision': row['binding_revision']}, 'authority': {'lease_id': lease['lease_id'], 'expires_at_ns': deadline}, 'terminal': {'release_all_required': True}, 'ops': [{'op': 'pointer_move', 'frame': 'window_client', 'x': resolution['point'][0], 'y': resolution['point'][1]}, {'op': 'release_all'}]}
            admission = admit_program(program, self.backend.manifest(), now_ns=time.monotonic_ns(), current_observation_seq=row['sequence'], current_binding_revision=row['binding_revision'])
            if not admission.accepted:
                raise ValueError('ordinary admission refused: ' + str(admission.error))
            token = uuid.uuid4().hex
            self.permits.clear()
            self.permits[token] = {'program': program, 'row': row, 'scope': self.observer.scope, 'deadline': deadline}
            return {'authorization': token, 'sequence': row['sequence'], 'valid_until_ns': deadline, 'point': list(resolution['point'])}
        finally:
            self.lock.release()

    def verifier_idle(self):
        p = self.pending_verifier
        if p is None:
            return True
        status = p.poll()
        if status is None:
            return False
        self.last_verifier_exit = {'pid': p.pid, 'exit': status}
        self.pending_verifier = None
        return True

    def neutral(self):
        if self.backend.held_keys or self.backend.held_buttons:
            self.session.recovery_required = True
            return False
        return True

    def binding_guard(self):
        if not self.verifier_idle():
            return False
        a = self.active
        o = self.observer
        if a is None or self.cancelled() is not False or self.session.recovery_required or o.review_required:
            return False
        if not self.neutral():
            return False
        row = a['row']
        if o.scope != a['scope'] or o.sequence != row['sequence'] or o.binding_revision != row['binding_revision'] or (time.monotonic_ns() >= a['deadline']):
            return False
        if o._binding() != row['pointer_binding']:
            o.review_required = True
            return False
        return True

    def guard(self):
        if not self.binding_guard():
            return False
        a = self.active
        o = self.observer
        row = a['row']
        g = row['pointer_binding']['geometry']
        raw = self.backend.capture_pixels(o.target, 'window_client', 0, 0, g['width'], g['height'])
        if not self.neutral():
            return False
        if o._binding() != row['pointer_binding']:
            o.review_required = True
            return False
        return type(raw) is bytes and hashlib.sha256(raw).hexdigest() == row['native']['sha256'] and (time.monotonic_ns() < a['deadline']) and (self.cancelled() is False) and (o.scope == a['scope']) and (o.sequence == row['sequence']) and (o.binding_revision == row['binding_revision']) and (not o.review_required) and (not self.session.recovery_required)

    def execute(self, token, *, verify_effect=None, effect_deadline_ns=None):
        if not self.lock.acquire(blocking=False):
            return {'status': 'refused', 'error': 'OPERATION_ACTIVE', 'input_dispatched': False}
        try:
            a = self.permits.pop(token, None)
            if a is None:
                return {'status': 'refused', 'error': 'AUTHORIZATION_CONSUMED_OR_UNKNOWN', 'input_dispatched': False}
            if verify_effect is not None and (not callable(verify_effect) or type(effect_deadline_ns) is not int or effect_deadline_ns <= time.monotonic_ns()):
                return {'status': 'refused', 'error': 'INVALID_EFFECT_VERIFIER', 'input_dispatched': False}
            self.active = a
            if not self.guard():
                return {'status': 'refused', 'error': 'LIVE_REFERENCE_OR_AUTHORITY_CHANGED', 'input_dispatched': False}
            result = self.session.dispatch(copy.deepcopy(a['program']), current_observation_seq=self.observer.sequence, current_binding_revision=self.observer.binding_revision)
            if verify_effect is not None:
                from .effect import verify
                result['effect'] = verify(self, a, result, verify_effect, effect_deadline_ns)
                result['task_success'] = result['effect']['task_success']
                result['recovery_required'] = self.session.recovery_required
            return result
        finally:
            self.active = None
            self.lock.release()

    def recover_input(self):
        if not self.lock.acquire(blocking=False):
            return {'status': 'refused', 'error': 'OPERATION_ACTIVE', 'release_attempted': False, 'recovery_required': self.session.recovery_required}
        try:
            self.permits.clear()
            return self.session.recover_input()
        finally:
            self.lock.release()
