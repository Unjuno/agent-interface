"""Opt-in MCP owner that retires only an explicitly owned disposable target."""
from __future__ import annotations

from copy import deepcopy
from functools import wraps
import threading

from .owned_guarded_session import OwnedGuardedSessionOwner
from ..guarded_x11_v1.owned_target_process import (
    OwnedTargetProcess, _prestarted_target_identity_worker)
from ..guarded_x11_v1.cancel_supervisor import PrestartedCancellationSupervisor


def _with_retirement_lock(method):
    @wraps(method)
    def locked(self, *args, **kwargs):
        with self._target_retirement_lock:
            return method(self, *args, **kwargs)
    return locked


class OwnedTargetGuardedSessionOwner(OwnedGuardedSessionOwner):
    """Bind one configured XID to a launched child and retire it on uncertainty.

    The target handle must come from ``OwnedTargetProcess.launch(...,
    disposable=True)``. Target retirement runs after the control owner exits and
    before the inherited independent release/readback cleanup. It never turns
    the old task result into success or permits replay.
    """

    def __init__(self, targets, directory, display_name=None, *,
                 owned_target_process: OwnedTargetProcess,
                 prestarted_target_identity=False, **kwargs):
        if type(prestarted_target_identity) is not bool:
            raise ValueError('prestarted_target_identity must be a boolean')
        if not isinstance(owned_target_process, OwnedTargetProcess):
            raise TypeError('owned_target_process must be an OwnedTargetProcess handle')
        if not owned_target_process.running:
            raise ValueError('owned target process must still be running')
        if not isinstance(targets, dict) or len(targets) != 1:
            raise ValueError('owned target retirement requires exactly one configured XID')
        super().__init__(targets, directory, display_name, **kwargs)
        self._owned_target_process = owned_target_process
        self._owned_target_xid = next(iter(targets.values()))
        self._owned_target_binding = None
        self._owned_target_retirement = None
        self._target_retirement_lock = threading.RLock()
        self._target_custody = owned_target_process.claim_session()
        self._target_custody_released = False
        try:
            self._target_identity_supervisor = (PrestartedCancellationSupervisor(
                _prestarted_target_identity_worker)
                if prestarted_target_identity else None)
        except BaseException:
            owned_target_process.release_session(self._target_custody)
            self._target_custody = None
            raise

    def _ensure_started(self):
        super()._ensure_started()
        if self._owned_target_binding is not None:
            return
        if self._target_identity_supervisor is None:
            binding = self._owned_target_process.bind_x11_target_supervised(
                self.display_name, self._owned_target_xid, _custody=self._target_custody)
        else:
            binding = self._owned_target_process.bind_x11_target_prestarted(
                self._target_identity_supervisor, self.session_id,
                self.display_name, self._owned_target_xid, _custody=self._target_custody)
        if binding.get('status') != 'bound':
            raise RuntimeError('owned target binding refused: ' + str(
                binding.get('reason', 'unknown')))
        self._owned_target_binding = deepcopy(binding)

    def _cleanup_after_owner_retirement(self, retirement, **kwargs):
        with self._target_retirement_lock:
            if self._owned_target_retirement is None and retirement.get('retired') is True:
                self._attempt_target_retirement()
        return super()._cleanup_after_owner_retirement(retirement, **kwargs)

    @_with_retirement_lock
    def _attempt_target_retirement(self):
        first = None
        custody = getattr(self, '_target_custody', None)
        kwargs = {'_custody':custody} if custody is not None else {}
        try:
            result = self._owned_target_process.retire_bound_target(**kwargs)
            if (result.get('status') == 'unknown'
                    and result.get('reason') == 'pidfd_signal_failed'
                    and result.get('target_identity_verified') is True):
                first = deepcopy(result)
                result = self._owned_target_process.retire_bound_target(**kwargs)
        except Exception as error:
            result = {'status':'unknown', 'reason':'target_retirement_exception',
                      'error_type':type(error).__name__,
                      'target_identity_verified':False,
                      'process_exit_verified':False}
        self._owned_target_retirement = deepcopy(result)
        if first is not None:
            self._owned_target_retirement['immediate_previous_attempt'] = first
        if result.get('process_exit_verified') is True:
            try:
                self._owned_target_process.close(**kwargs)
            except Exception as error:
                self._owned_target_retirement['handle_close_error'] = type(error).__name__

    def cancel_guarded(self, token, *, operation_id=None,
                       deadline_monotonic_ns=None):
        result = super().cancel_guarded(
            token, operation_id=operation_id,
            deadline_monotonic_ns=deadline_monotonic_ns)
        return self._with_target_receipts(result)

    @_with_retirement_lock
    def _with_target_receipts(self, result):
        if self._owned_target_retirement is not None:
            result = dict(result, owned_target_retirement=deepcopy(
                self._owned_target_retirement))
        if self._owned_target_binding is not None:
            result = dict(result, owned_target_binding=deepcopy(
                self._owned_target_binding))
        return result

    def _retirement_cleanup_result_fields(self, retirement):
        return self._with_target_receipts(
            super()._retirement_cleanup_result_fields(retirement))

    def close(self):
        with self._target_retirement_lock:
            previous = deepcopy(getattr(self, '_owned_target_retirement', None))
        try:
            report = super().close()
            retirement = getattr(self, '_retirement', None) or {}
            with self._target_retirement_lock:
                if (previous is not None and previous.get('status') == 'unknown'
                        and previous.get('process_exit_verified') is not True
                        and retirement.get('retired') is True
                        and self._owned_target_retirement == previous):
                    self._attempt_target_retirement()
                    previous.pop('previous_attempt', None)
                    self._owned_target_retirement['previous_attempt'] = previous
                custody = getattr(self, '_target_custody', None)
                process = getattr(self, '_process', None)
                if (custody is not None and report.get('verified') is True
                        and not getattr(self, '_target_custody_released', False)
                        and report.get('status') == 'closed'
                        and getattr(self, 'state', None) == 'closed'
                        and not getattr(self, '_execution_unknown', False)
                        and (process is None or not process.is_alive())):
                    self._owned_target_process.release_session(custody)
                    self._target_custody_released = True
            return self._with_target_receipts(report)
        finally:
            supervisor = getattr(self, '_target_identity_supervisor', None)
            if supervisor is not None:
                supervisor.close()
