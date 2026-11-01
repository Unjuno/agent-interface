"""Experimental one-shot recovery on a caller-owned disposable Xvfb display.

The caller must retain exclusive custody of both objects and all display
clients. This component does not create a replacement or prove old-task
success, key-up delivery, queue drainage, or ownership of an arbitrary display.
"""
from copy import deepcopy
import threading
import time

from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from .private_display_owner import PrivateDisplayOwner


class PrivateDisplayRecovery:
    """Recover once; an optional reserve leaves time for display retirement.

    The reserve shortens the cancellation deadline, but does not impose a
    hard bound on cancellation, process shutdown, or operating-system calls.
    """
    def __init__(self, display_owner, guarded_owner, *, retirement_reserve_ns=0):
        if type(retirement_reserve_ns) is not int or retirement_reserve_ns < 0:
            raise ValueError('retirement reserve must be nonnegative integer nanoseconds')
        if not isinstance(display_owner, PrivateDisplayOwner) or not isinstance(guarded_owner, OwnedGuardedSessionOwner):
            raise TypeError('recovery requires private display and guarded owner objects')
        session = display_owner._session
        process = display_owner._process
        guarded_process = guarded_owner._process
        supervisor = guarded_owner._cleanup_supervisor
        supervisor_process = getattr(supervisor, '_process', None)
        if (session is None or process is None or process.poll() is not None
                or display_owner._retired
                or guarded_owner._owned_display_owner is not display_owner
                or guarded_owner.state != 'open'
                or guarded_process is None or not guarded_process.is_alive()
                or supervisor_process is None or not supervisor_process.is_alive()
                or guarded_owner.display_name != session.display
                or guarded_owner._xauthority != str(session.authority)):
            raise ValueError('guarded owner must be pinned to the live private display')
        self._display_owner = display_owner
        self._guarded_owner = guarded_owner
        self._display_process = process
        self._display_session = session
        self._guarded_process = guarded_process
        self._supervisor = supervisor
        self._retirement_reserve_ns = retirement_reserve_ns
        self._lock = threading.Lock()
        self._result = None
        self._token = None

    def _binding_intact(self):
        return (self._guarded_owner._owned_display_owner is self._display_owner
                and self._guarded_owner._process is self._guarded_process
                and self._guarded_owner._cleanup_supervisor is self._supervisor
                and self._display_owner._process is self._display_process
                and self._display_owner._session is self._display_session
                and self._guarded_owner.display_name == self._display_session.display
                and self._guarded_owner._xauthority == str(self._display_session.authority))

    def cancel_guarded(self, token, *, deadline_monotonic_ns):
        if type(token) is not str or not token:
            raise ValueError('nonempty cancellation token required')
        if type(deadline_monotonic_ns) is not int or deadline_monotonic_ns <= 0:
            raise ValueError('absolute monotonic deadline required')
        remaining = max(0, deadline_monotonic_ns - time.monotonic_ns()) / 1e9
        if not self._lock.acquire(timeout=remaining):
            return {'status':'unknown', 'reason':'recovery_lock_deadline',
                    'fresh_display_allowed':False, 'replay_allowed':False}
        try:
            if self._result is not None:
                if token == self._token:
                    return deepcopy(self._result)
                return {'status':'unknown', 'reason':'recovery_already_used',
                        'fresh_display_allowed':False, 'replay_allowed':False}
            now_ns = time.monotonic_ns()
            if now_ns >= deadline_monotonic_ns:
                return {'status':'unknown', 'reason':'deadline_before_cancel',
                        'fresh_display_allowed':False, 'replay_allowed':False}
            cancel_deadline_ns = deadline_monotonic_ns - self._retirement_reserve_ns
            if now_ns >= cancel_deadline_ns:
                return {'status':'unknown', 'reason':'insufficient_cancel_budget',
                        'fresh_display_allowed':False, 'replay_allowed':False}
            if not self._binding_intact():
                return {'status':'unknown', 'reason':'display_binding_changed',
                        'fresh_display_allowed':False, 'replay_allowed':False}
            try:
                cancellation = self._guarded_owner.cancel_guarded(
                    token, deadline_monotonic_ns=cancel_deadline_ns)
            except Exception as error:
                cancellation = {'status':'cancel_unconfirmed', 'cleanup_status':'UNKNOWN',
                                'owner_process_retired':False,
                                'error_type':type(error).__name__}
            if not isinstance(cancellation, dict) or type(cancellation.get('status')) is not str:
                cancellation = {'status':'cancel_unconfirmed', 'cleanup_status':'UNKNOWN',
                                'owner_process_retired':False,
                                'reason':'malformed_cancellation_receipt'}
            after_cancel_ns = time.monotonic_ns()
            if after_cancel_ns >= deadline_monotonic_ns:
                result = {'status':'unknown', 'reason':'deadline_after_cancel',
                          'cancellation':deepcopy(cancellation),
                          'fresh_display_allowed':False, 'replay_allowed':False,
                          'release_confirmed':False, 'task_success':None,
                          'cleanup_status':'UNKNOWN'}
                self._result = deepcopy(result)
                self._token = token
                return result
            must_retire = (cancellation.get('status') not in ('cancel_requested', 'not_active')
                           or cancellation.get('cleanup_status') == 'UNKNOWN')
            result = {'status':'unknown',
                      'cancellation':deepcopy(cancellation),
                      'fresh_display_allowed':False, 'replay_allowed':False,
                      'release_confirmed':False, 'task_success':None,
                      'cleanup_status':'UNKNOWN' if must_retire else cancellation.get('cleanup_status')}
            if must_retire:
                if not self._binding_intact():
                    result['reason'] = 'display_binding_changed'
                    self._result = deepcopy(result)
                    self._token = token
                    return result
                remaining = (deadline_monotonic_ns - after_cancel_ns) / 1e9
                if remaining <= 0:
                    retirement = {'status':'unknown', 'reason':'deadline_before_display_retire'}
                else:
                    try:
                        retirement = self._display_owner.retire(timeout_s=remaining)
                    except Exception as error:
                        retirement = {'status':'unknown', 'reason':'display_retire_exception',
                                      'error_type':type(error).__name__}
                if not isinstance(retirement, dict):
                    retirement = {'status':'unknown', 'reason':'malformed_display_retirement'}
                result['display_retirement'] = retirement
                if time.monotonic_ns() >= deadline_monotonic_ns:
                    result['reason'] = 'deadline_after_display_retire'
                result['fresh_display_allowed'] = (retirement.get('status') == 'retired'
                    and cancellation.get('owner_process_retired') is True
                    and 'reason' not in result)
            self._result = deepcopy(result)
            self._token = token
            return result
        finally:
            self._lock.release()
