"""Admission wrapper connecting runtime core v1 to the X11 backend."""
from __future__ import annotations
from typing import Any

from runtime.core_v1.contract import admit_program
from .backend import X11Backend, X11BackendError


class X11RuntimeSession:
    def __init__(self, backend: X11Backend):
        self.backend = backend

    def dispatch(
        self,
        program: dict[str, Any],
        *,
        current_observation_seq: int,
        current_binding_revision: int,
        now_ns: int | None = None,
    ) -> dict[str, Any]:
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
            release = self.backend.release_all()
            return {
                "status": "refused",
                "error": "BACKEND_CONSTRAINT",
                "detail": str(error),
                "required_capabilities": list(admission.required_capabilities),
                "backend_emissions": self.backend.emissions,
                "release": release,
            }

        result = self.backend.execute(program)
        releases = result.get("releases", [])
        verified = bool(releases) and all(row.get("verified") for row in releases)
        return {
            "status": "completed" if verified else "release_unverified",
            "admission": "accepted",
            "required_capabilities": list(admission.required_capabilities),
            "execution": result,
        }
