"""Run shared ABBA scoring with the single-envelope v4 action contract."""
import json
from pathlib import Path

import run_target_handle_model_screen_v2 as shared


HERE = Path(__file__).resolve().parent
shared.ROOT = HERE / "results/target-handle-model-screen-04"
shared.SCHEMA = HERE / "target_action_envelope_schema_v1.json"


def parse(text, mode):
    value = json.loads(text)
    target = value.get("target", {})
    common = (
        set(value) == {"op", "target", "button", "duration_ms"}
        and value.get("op") == "pointer_click"
        and value.get("button") == 1
        and value.get("duration_ms") == 80
        and set(target) == {"kind", "x", "y", "target_handle", "dx", "dy"}
        and type(target.get("x")) is int
        and type(target.get("y")) is int
        and type(target.get("dx")) is int
        and type(target.get("dy")) is int
    )
    if mode == "coordinate":
        correct = (
            common
            and target.get("kind") == "absolute"
            and 270 <= target["x"] < 312
            and 242 <= target["y"] < 260
            and target.get("target_handle") == ""
            and target.get("dx") == 0
            and target.get("dy") == 0
        )
    else:
        correct = (
            common
            and target
            == {
                "kind": "handle",
                "x": 0,
                "y": 0,
                "target_handle": "h_save_form",
                "dx": 20,
                "dy": 9,
            }
        )
    return value, correct


shared.parse = parse


if __name__ == "__main__":
    shared.main()
