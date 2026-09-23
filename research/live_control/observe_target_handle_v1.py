"""X11-independent validation and execution for fresh observe-target queries."""
import time


OPERATION = "observe_target_handle"


def validate_step(step):
    if set(step) != {"op", "target_handle", "offset"}:
        raise ValueError("invalid observe-target fields")
    if (type(step["target_handle"]) is not str
            or type(step["offset"]) is not list
            or len(step["offset"]) != 2
            or any(type(value) is not int for value in step["offset"])):
        raise ValueError("observe-target requires an alias and two integer offsets")


def execute(backend, step, identifier, index):
    # Capture first so the resolution and returned frame have one identity.
    backend.snapshot(identifier, index)
    checked_ns = time.perf_counter_ns()
    observation = backend.observation()
    outcome = backend.handles.resolve_point(
        step["target_handle"], step["offset"], observation, backend.image(),
        checked_ns, session_scope="x11:" + backend.session.name
    )
    backend.emit({
        "event": "target_handle_checked",
        "id": identifier,
        "step": index,
        "checked_ns": checked_ns,
        "observation_sequence": observation["sequence"],
        "observation_capture_ns": observation["capture_ns"],
        "authority": "observation only; grants no input authority",
        **outcome,
    })
    return outcome
