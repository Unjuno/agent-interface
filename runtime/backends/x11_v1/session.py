"""Admission wrapper connecting runtime core v1 to the X11 backend."""
from __future__ import annotations
from typing import Any

from runtime.core_v1.contract import admit_program
from .backend import X11Backend, X11BackendError, X11ExecutionError


class X11RuntimeSession:
    def __init__(self, backend: X11Backend):
        self.backend = backend
        # Sticky for this connection owner. A new image/window binding is not
        # evidence that physical controls have returned to neutral.
        self.recovery_required = False

    def _record_release(self, releases):
        verified = isinstance(releases, list) and bool(releases) and all(
            isinstance(row, dict) and row.get("verified") is True and row.get("keys_down") == []
            and row.get("buttons_down") == [] for row in releases)
        self.recovery_required = self.recovery_required or not verified
        return verified

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
        except X11ExecutionError as error:
            self._record_release(error.execution.get("releases", []))
            return {
                "status": "execution_failed", "admission": "accepted",
                "error": "BACKEND_EXECUTION_FAILED",
                "required_capabilities": list(admission.required_capabilities),
                "execution": error.execution,
                "recovery_required": self.recovery_required,
            }
        except Exception:
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
