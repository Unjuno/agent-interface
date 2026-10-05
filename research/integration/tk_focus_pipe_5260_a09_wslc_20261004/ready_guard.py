"""Independent readiness custody gate; no GUI, input or process effects."""
import json
from pathlib import Path


def pre_input_errors(ready):
    errors = []
    witness = ready.get("readiness", {})
    if (witness != {"scheduled": 1, "focus_callbacks": 1, "finalizations": 1} or
            any(type(witness.get(key)) is not int for key in ("scheduled", "focus_callbacks", "finalizations"))):
        errors.append("single_epoch_witness")
    if type(ready.get("ready_ns")) is not int or ready["ready_ns"] <= 0:
        errors.append("ready_clock")
    try:
        g = ready["geometry"]
        keys = ("root_id", "target_id", "root_width", "root_height", "target_width", "target_height",
                "root_x", "root_y", "target_x", "target_y", "target_root_x", "target_root_y")
        if not all(type(g[k]) is int for k in keys):
            errors.append("geometry_types")
        elif (min(g[k] for k in ("root_width", "root_height", "target_width", "target_height")) <= 1 or
              min(g["root_id"], g["target_id"]) <= 0 or g["root_id"] == g["target_id"]):
            errors.append("geometry_nonpositive")
        elif ((g["target_root_x"], g["target_root_y"]) !=
              (g["root_x"] + g["target_x"], g["root_y"] + g["target_y"])):
            errors.append("coordinate_derivation_disagreement")
    except (KeyError, TypeError):
        errors.append("geometry_missing")
    return errors


def readiness_errors(root, row):
    errors = []
    app, ready = row.get("app", {}), row.get("ready", {})
    expected_witness = {"scheduled": 1, "focus_callbacks": 1, "finalizations": 1}
    witnesses = (ready.get("readiness"), app.get("readiness"))
    if any(witness != expected_witness or
           any(type(witness.get(key)) is not int for key in expected_witness)
           for witness in witnesses):
        errors.append("single_epoch_witness")
    if app.get("ready_snapshot") != ready:
        errors.append("app_ready_snapshot")
    if (type(ready.get("ready_ns")) is not int or ready["ready_ns"] <= 0 or
            not isinstance(ready.get("geometry"), dict) or
            not isinstance(ready.get("baseline_frame"), dict) or
            any(app.get(name) != ready.get(name) for name in ("ready_ns", "geometry", "baseline_frame"))):
        errors.append("app_ready_metadata")
    if row.get("app_pid") != app.get("pid") or type(app.get("pid")) is not int or app["pid"] <= 0:
        errors.append("app_pid_binding")
    try:
        stdout_app = json.loads(row["app_stdout"])
    except (KeyError, TypeError, ValueError):
        stdout_app = None
    if stdout_app != app:
        errors.append("app_stdout_binding")
    for name, expected, label in (("ready.json", ready, "ready_file_binding"),
                                  ("app_result.json", app, "app_file_binding")):
        try:
            actual = json.loads((Path(root) / name).read_bytes())
        except (OSError, ValueError):
            actual = None
        if actual != expected:
            errors.append(label)
    return errors
