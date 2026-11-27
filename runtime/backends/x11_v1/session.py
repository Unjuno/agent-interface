"""Admission wrapper connecting runtime core v1 to the X11 backend."""
from __future__ import annotations
from typing import Any
from dataclasses import dataclass

from runtime.core_v1.contract import admit_program
from .backend import X11Backend, X11BackendError, X11ExecutionError


@dataclass
class _RecoveryCustody:
    required: bool = False
    epoch: int = 0


class X11RuntimeSession:
    def __init__(self, backend: X11Backend):
        self.backend = backend
        # Caller-serialized, backend-object custody. Constructing a wrapper
        # neither clears an obligation nor acknowledges another wrapper's old
        # source/alias context. Distinct backends/processes remain separate.
        self._recovery = backend.__dict__.setdefault('_x11_session_recovery', _RecoveryCustody())
        if not isinstance(self._recovery, _RecoveryCustody):
            raise ValueError('invalid backend recovery custody')
        self._recovery_epoch = self._recovery.epoch

    @property
    def recovery_required(self):
        return self._recovery.required or self._recovery_epoch != self._recovery.epoch

    @recovery_required.setter
    def recovery_required(self, required):
        if type(required) is not bool:
            raise ValueError('recovery_required must be bool')
        if required:
            if not self._recovery.required:
                self._recovery.epoch += 1
            self._recovery.required = True
        elif self.recovery_required:
            raise ValueError('explicit verified input recovery required')

    def _record_release(self, releases):
        verified = isinstance(releases, list) and bool(releases) and all(
            isinstance(row, dict) and row.get("verified") is True and row.get("keys_down") == []
            and row.get("buttons_down") == [] for row in releases)
        if not verified:
            self.recovery_required = True
        return verified

    def recover_input(self):
        """Explicit neutralization only; never replay the failed program."""
        if not self.recovery_required:
            return {'status': 'refused', 'error': 'INPUT_RECOVERY_NOT_REQUIRED',
                    'release_attempted': False, 'recovery_required': False}
        try:
            release = self.backend.release_all()
        except BaseException as error:
            self.recovery_required = True
            if not isinstance(error, Exception):
                raise
            return {'status': 'recovery_failed', 'error': repr(error),
                    'release_attempted': True, 'recovery_required': True}
        verified = self._record_release([release])
        if verified:
            self._recovery.required = False
            self._recovery_epoch = self._recovery.epoch
        return {'status': 'input_recovered' if verified else 'recovery_failed',
                'release_attempted': True, 'release': release,
                'recovery_required': self.recovery_required,
                'task_success': None, 'replay_allowed': False}

    def dispatch(
        self,
        program: dict[str, Any],
        *,
        current_observation_seq: int,
        current_binding_revision: int,
        now_ns: int | None = None,
    ) -> dict[str, Any]:
        if self.recovery_required:
            return {"status": "refused", "error": "INPUT_RECOVERY_REQUIRED",
                    "recovery_required": True, "input_dispatched": False,
                    "required_capabilities": [], "backend_emissions": self.backend.emissions}
        now_ns = self.backend.monotonic_ns() if now_ns is None else now_ns
        admission = admit_program(
            program,
            self.backend.manifest(),
            now_ns=now_ns,
            current_observation_seq=current_observation_seq,
            current_binding_revision=current_binding_revision,
        )
        if not admission.accepted:
            return {
                "status": "refused",
                "error": admission.error,
                "required_capabilities": list(admission.required_capabilities),
                "backend_emissions": self.backend.emissions,
            }

        # Native/backend-specific constraints must also be checked before the
        # first physical emission. They are a second admission layer, not an
        # execution-time partial failure.
        try:
            self.backend.preflight(program)
        except X11BackendError as error:
            try:
                release = self.backend.release_all()
            except BaseException:
                self.recovery_required = True
                raise
            self._record_release([release])
            return {
                "status": "refused",
                "error": "BACKEND_CONSTRAINT",
                "program_execution_started": False, "program_emissions": 0,
                "cleanup_attempted": True,
                "detail": str(error),
                "required_capabilities": list(admission.required_capabilities),
                "backend_emissions": self.backend.emissions,
                "release": release,
                "recovery_required": self.recovery_required,
            }
        except BaseException:
            self.recovery_required = True
            raise

        try:
            result = self.backend.execute(program)
        except X11ExecutionError as error:
            self._record_release(error.execution.get("releases", []))
            return {
                "status": "execution_failed", "admission": "accepted",
                "error": "BACKEND_EXECUTION_FAILED",
                "required_capabilities": list(admission.required_capabilities),
                "execution": error.execution,
                "recovery_required": self.recovery_required,
            }
        except X11BackendError as error:
            # execute repeats preflight before its effect boundary. A managed
            # client may disappear after the first check; this is still a
            # pre-input constraint failure, not an unknown execution exception.
            try:
                release = self.backend.release_all()
            except BaseException:
                self.recovery_required = True
                raise
            self._record_release([release])
            return {
                "status": "refused", "error": "BACKEND_CONSTRAINT",
                "program_execution_started": False, "program_emissions": 0,
                "cleanup_attempted": True,
                "detail": str(error),
                "required_capabilities": list(admission.required_capabilities),
                "backend_emissions": self.backend.emissions,
                "release": release, "recovery_required": self.recovery_required,
            }
        except BaseException:
            self.recovery_required = True
            raise
        releases = result.get("releases", [])
        verified = self._record_release(releases)
        return {
            "status": "completed" if verified else "release_unverified",
            "admission": "accepted",
            "required_capabilities": list(admission.required_capabilities),
            "execution": result,
            "recovery_required": self.recovery_required,
        }
