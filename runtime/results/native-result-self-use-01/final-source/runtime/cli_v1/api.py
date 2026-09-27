"""Model/vendor-neutral local API over promoted runtime backends."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

from runtime.selector_v1 import BackendUnavailable, open_session, select_backend

SCHEMA_DOCTOR = "agent-interface/runtime-doctor-v1"
SCHEMA_DISPATCH = "agent-interface/runtime-dispatch-result-v1"


def doctor(*, platform: str | None = None, environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    plan = select_backend(platform=platform, environ=environ)
    return {
        "schema": SCHEMA_DOCTOR,
        "selection": asdict(plan),
        "runtime_available": plan.available,
        "side_effect_authority": False,
        "note": "Selection is diagnostic only; backend manifest and core admission govern effect authority.",
    }


def dispatch(
    program: dict[str, Any],
    targets: Mapping[str, int],
    *,
    current_observation_seq: int,
    current_binding_revision: int,
    display_name: str | None = None,
) -> dict[str, Any]:
    if type(current_observation_seq) is not int or current_observation_seq < 0:
        return {"schema": SCHEMA_DISPATCH, "status": "invalid_request", "error": "INVALID_OBSERVATION_SEQ"}
    if type(current_binding_revision) is not int or current_binding_revision < 0:
        return {"schema": SCHEMA_DISPATCH, "status": "invalid_request", "error": "INVALID_BINDING_REVISION"}
    if not isinstance(program, dict):
        return {"schema": SCHEMA_DISPATCH, "status": "invalid_request", "error": "PROGRAM_NOT_OBJECT"}
    try:
        session = open_session(targets, display_name=display_name)
    except BackendUnavailable as error:
        return {"schema": SCHEMA_DISPATCH, "status": "backend_unavailable", "error": str(error)}
    row: dict[str, Any] = {}
    try:
        result = session.dispatch(
            program,
            current_observation_seq=current_observation_seq,
            current_binding_revision=current_binding_revision,
        )
        row = {"schema": SCHEMA_DISPATCH, "status": "returned", "result": result}
    except Exception as error:
        row = {"schema": SCHEMA_DISPATCH, "status": "runtime_failed", "error": repr(error)}
    finally:
        # This facade owns the session it opens. In particular, X11 holds a
        # display connection even if core admission refuses the program.
        close = getattr(getattr(session, "backend", None), "close", None)
        if callable(close):
            try:
                close()
            except Exception as error:
                row["status"] = "runtime_failed"
                row.setdefault("error", "BACKEND_CLOSE_FAILED")
                row["cleanup_error"] = repr(error)
    return row
