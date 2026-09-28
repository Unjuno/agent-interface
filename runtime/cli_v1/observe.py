"""One fresh native observation, independent of input dispatch or task scoring."""
from __future__ import annotations

import uuid
from runtime.selector_v1 import BackendUnavailable, open_session

SCHEMA = "agent-interface/runtime-observation-v1"


def valid_observation_request(target, frame, region):
    """Validate capture syntax without opening a session or sending input."""
    return (type(target) is str and frame in ("window_client", "screen_physical_px") and
            type(region) is list and len(region) == 4 and
            all(type(v) is int for v in region) and
            0 <= region[0] <= 32767 and 0 <= region[1] <= 32767 and
            1 <= region[2] <= 8192 and 1 <= region[3] <= 8192 and
            region[2] * region[3] <= 16_777_216)


def observe(targets, *, target, frame, region, capture_directory=None, display_name=None):
    return _observe(targets, target=target, frame=frame, region=region,
                    capture_directory=capture_directory, display_name=display_name)


def observe_in_session(session, *, target, frame, region, capture_directory=None):
    """Capture through a caller-owned session without closing it or clearing recovery.

    The caller serializes access and owns closure. No input, source/binding update,
    recovery reset or authority renewal is performed by this facade.
    """
    if session is None or getattr(session, "backend", None) is None:
        return {"schema": SCHEMA, "observation_id": uuid.uuid4().hex,
                "status": "invalid_request", "error": "INVALID_SESSION",
                "side_effect_authority": False, "input_dispatched": False}
    return _observe({}, target=target, frame=frame, region=region,
                    capture_directory=capture_directory, supplied_session=session)


def _observe(targets, *, target, frame, region, capture_directory=None,
             display_name=None, supplied_session=None):
    row = {"schema": SCHEMA, "observation_id": uuid.uuid4().hex,
           "side_effect_authority": False, "input_dispatched": False}
    if not valid_observation_request(target, frame, region):
        return dict(row, status="invalid_request", error="INVALID_OBSERVATION_REGION")
    try:
        session = (supplied_session if supplied_session is not None
                   else open_session(targets, display_name=display_name))
    except BackendUnavailable as error:
        return dict(row, status="backend_unavailable", error=str(error))
    except Exception as error:
        # Backend selection succeeded, but construction/capability setup failed.
        # Preserve the observation API's structured no-authority failure boundary.
        return dict(row, status="observation_failed", error=repr(error),
                    failure_phase="backend_initialization")
    try:
        reader = getattr(session.backend, "observe_read_only", None)
        if not callable(reader):
            raise ValueError("READ_ONLY_OBSERVATION_UNSUPPORTED")
        if capture_directory is not None:
            configure = getattr(session.backend, "configure_capture_artifacts", None)
            if not callable(configure):
                raise ValueError("CAPTURE_ARTIFACTS_UNSUPPORTED")
            configure(capture_directory)
        row.update(status="returned", observation=reader(target, frame, region))
    except Exception as error:
        row.update(status="observation_failed", error=repr(error))
    finally:
        close = (getattr(session.backend, "close", None)
                 if supplied_session is None else None)
        if callable(close):
            try:
                close()
            except Exception as error:
                row.update(status="observation_failed", cleanup_error=repr(error))
                row.setdefault("error", "BACKEND_CLOSE_FAILED")
    return row
