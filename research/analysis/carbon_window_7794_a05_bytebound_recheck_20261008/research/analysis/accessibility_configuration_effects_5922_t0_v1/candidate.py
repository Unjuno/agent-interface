"""Finite presentation/effect simulator for Issue #5922; no real input is emitted."""
import json
from pathlib import Path


def hit(elements, point):
    x, y = point["x"], point["y"]
    for element in elements:
        rect = element["rect"]
        if rect["x"] <= x < rect["x"] + rect["w"] and rect["y"] <= y < rect["y"] + rect["h"]:
            return element
    return None


def admitted_action(element_id, obj, value):
    return {"element_id": element_id, "object": obj, "value": value,
            "authority": "save-display-name-only", "released": True}


def execute(case, route, task):
    expected_object = task["object"]
    desired = task["desired_value"]
    action = None
    if route == "explicit_unknown":
        return {"route": route, "disposition": "UNKNOWN", "action": None, "verified": False}
    if route == "raw_coordinate":
        element = hit(case["elements"], case["cached_target"])
        # The pixel-coded baseline also requires the default blue cue.
        if element is not None and element["color"] != case["visual"]["expected_color"]:
            element = None
        if element is not None and element["enabled"]:
            action = admitted_action(element["id"], expected_object if element["id"] == "save" else "profile.delete_account",
                                     desired if element["id"] == "save" else "DELETE")
    elif route == "fresh_semantic_rebind":
        if not case["function_available"]:
            return {"route": route, "disposition": "UNKNOWN_APP_FUNCTION", "action": None, "verified": False}
        if case["ax"]["epoch"] != case["epoch"]:
            return {"route": route, "disposition": "UNKNOWN_STALE_EVIDENCE", "action": None, "verified": False}
        matches = [e for e in case["elements"] if e["id"] == case["ax"]["target_id"] == "save"
                   and e["role"] == "button" and e["name"] == "Save display name"]
        if len(matches) != 1 or not matches[0]["enabled"]:
            return {"route": route, "disposition": "UNKNOWN_TARGET", "action": None, "verified": False}
        action = admitted_action("save", expected_object, desired)
    else:
        raise ValueError("unknown route")

    if action is None:
        return {"route": route, "disposition": "NO_EFFECT", "action": None, "verified": False}
    if action["element_id"] == "save":
        if case["effect_receipt"]:
            disposition, verified = "SAVED", True
        else:
            # The click may have happened, but no effect/completion evidence exists.
            disposition, verified = "UNKNOWN_EFFECT", False
    else:
        disposition, verified = "FORBIDDEN_EFFECT", False
    return {"route": route, "disposition": disposition, "action": action, "verified": verified}


def run(fixture):
    rows = []
    for case in fixture["cases"]:
        for route in fixture["routes"]:
            result = execute(case, route, fixture["task"])
            rows.append({"case_id": case["id"], "configuration": case["configuration"],
                         **result, "expected_semantic": case["expected_semantic"]})
    return {"schema": "accessibility-configuration-candidate-output-v1", "rows": rows}


if __name__ == "__main__":
    fixture_path = Path(__file__).with_name("fixture.json")
    print(json.dumps(run(json.loads(fixture_path.read_text(encoding="utf-8"))), sort_keys=True, separators=(",", ":")))
