"""Deterministic ordering and shape controls for combined observe-target."""
from types import SimpleNamespace

from PIL import Image

from observe_target_handle_v1 import OPERATION, execute, validate_step


class Handles:
    def __init__(self):
        self.received = None

    def resolve_point(self, alias, offset, observation, image, now_ns,
                      session_scope=None):
        self.received = (alias, offset, observation, image, now_ns, session_scope)
        return {"eligible": True, "status": "REVALIDATED", "handle": alias,
                "point": [41, 52], "reference_kind": "session_alias",
                "private_registry_id_exposed": False}


def main():
    backend = SimpleNamespace()
    backend.session = SimpleNamespace(name=":probe")
    backend.handles = Handles()
    backend.sequence = 4
    backend.last_capture_ns = 100
    backend.observed_pointer = {"focus": 1, "surface": 2,
                                "geometry": [0, 0, 100, 100]}
    backend._image = Image.new("RGB", (100, 100), "white")
    events = []
    backend.emit = events.append
    backend.image = lambda: backend._image
    backend.observation = lambda: {
        "sequence": backend.sequence,
        "capture_ns": backend.last_capture_ns,
        "pointer_binding": backend.observed_pointer,
    }

    def snapshot(identifier, index):
        backend.sequence += 1
        backend.last_capture_ns = 200
        backend.emit({"event": "observation", "id": identifier, "step": index,
                      "sequence": backend.sequence, "capture_ns": 200})

    backend.snapshot = snapshot
    outcome = execute(
        backend,
        {"op": OPERATION, "target_handle": "save_form", "offset": [20, 9]},
        "probe", 0,
    )
    assert [event["event"] for event in events] == [
        "observation", "target_handle_checked"
    ]
    checked = events[-1]
    assert checked["status"] == "REVALIDATED"
    assert checked["observation_sequence"] == 5
    assert checked["observation_capture_ns"] == 200
    assert checked["private_registry_id_exposed"] is False
    assert backend.handles.received[2]["sequence"] == 5
    assert backend.handles.received[2]["capture_ns"] == 200
    assert outcome["point"] == [41, 52]

    valid = {"op": OPERATION, "target_handle": "save_form", "offset": [20, 9]}
    validate_step(valid)
    invalid = [
        {**valid, "extra": 1},
        {**valid, "target_handle": 3},
        {**valid, "offset": [20]},
        {**valid, "offset": [20, True]},
    ]
    for candidate in invalid:
        try:
            validate_step(candidate)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid observe-target accepted")
    print("observe_target_handle_v1_probe_passed")


if __name__ == "__main__":
    main()
