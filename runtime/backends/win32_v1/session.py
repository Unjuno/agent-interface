"""Admission wrapper connecting runtime core v1 to the Win32 backend."""
from __future__ import annotations
from typing import Any

from runtime.core_v1.contract import admit_program
from .backend import Win32Backend, Win32BackendError


class Win32RuntimeSession:
    def __init__(self, backend: Win32Backend):
        self.backend = backend
        # A new binding or direct backend cleanup is not session recovery.
        self.recovery_required = False

    def _record_release(self, releases):
        verified = isinstance(releases, list) and bool(releases) and all(
            isinstance(row, dict) and row.get("verified") is True
            and row.get("keys_down") == [] and row.get("buttons_down") == []
            for row in releases
        )
        self.recovery_required = self.recovery_required or not verified
        return verified

    def recover_input(self):
        """Attempt neutralization once; never replay the failed program."""
        if not self.recovery_required:
            return {"status": "refused", "error": "INPUT_RECOVERY_NOT_REQUIRED",
                    "release_attempted": False, "recovery_required": False}
        try:
            release = self.backend.release_all()
        except Exception as error:
            return {"status": "recovery_failed", "error": repr(error),
                    "release_attempted": True, "recovery_required": True}
        verified = self._record_release([release])
        if verified:
            self.recovery_required = False
        return {"status": "input_recovered" if verified else "recovery_failed",
                "release_attempted": True, "release": release,
                "recovery_required": self.recovery_required,
                "task_success": None, "replay_allowed": False}

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
        try:
            self.backend.preflight(program)
        except Win32BackendError as error:
            try:
                release = self.backend.release_all()
            except Exception:
                self.recovery_required = True
                raise
            self._record_release([release])
            return {
                "status": "refused",
                "error": "BACKEND_CONSTRAINT",
                "detail": str(error),
                "required_capabilities": list(admission.required_capabilities),
                "backend_emissions": self.backend.emissions,
                "release": release,
                "recovery_required": self.recovery_required,
            }
        try:
            result = self.backend.execute(program)
        except Win32BackendError as error:
            self.recovery_required = True
            return {
                "status": "execution_failed",
                "error": "BACKEND_EXECUTION",
                "release": getattr(error, "release_receipt", None),
                "cleanup_error": getattr(error, "cleanup_error", None),
                "detail": str(error),
                "backend_emissions": self.backend.emissions,
                "recovery_required": self.recovery_required,
            }
        except Exception:
            self.recovery_required = True
            raise
        releases = result.get("releases", []) if isinstance(result, dict) else None
        verified = self._record_release(releases)
        return {
            "status": "completed" if verified else "release_unverified",
            "admission": "accepted",
            "required_capabilities": list(admission.required_capabilities),
            "execution": result,
            "recovery_required": self.recovery_required,
        }
