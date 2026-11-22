"""Raw-only independent audit for the post-sample cancellation composition pair."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def check(cancel, control):
    errors = []
    for label, row, status, reason, released_count in (
        ("cancel", cancel, "cancelled", "cancelled", 1),
        ("control", control, "completed", "release", 0),
    ):
        if row.get("experiment") != "CROSS-COMPONENT-POST-SAMPLE-CANCEL-7429-7440":
            errors.append(f"{label}: experiment identity")
        if row.get("terminal", {}).get("status") != status:
            errors.append(f"{label}: terminal status")
        owner = row.get("owner_release", {})
        if owner.get("event") != "owner_release" or owner.get("reason") != reason:
            errors.append(f"{label}: owner reason")
        if owner.get("verified") is not True or owner.get("keys_down") != [] or owner.get("buttons_down") != []:
            errors.append(f"{label}: verified empty release")
        if row.get("input_released_count") != released_count:
            errors.append(f"{label}: input_released count")
        terminal = row.get("terminal", {})
        if label == "cancel":
            if terminal.get("interruption", {}).get("record", {}).get("reason") != "cancelled":
                errors.append("cancel: interruption cause")
            release_events = row.get("emitted_events", [])
            if "input_released" not in release_events or release_events.index("input_released") > release_events.index("terminal"):
                errors.append("cancel: release publication order")
        elif terminal.get("interruption") is not None:
            errors.append("control: unexpected interruption")
        if "input_release_publication" in terminal:
            errors.append(f"{label}: unexpected publication status")
        if row.get("fake_x_events") != [[2, 38], [3, 38]]:
            errors.append(f"{label}: fake XTEST down/up sequence")
    if "cancel_requested" not in cancel.get("emitted_events", []):
        errors.append("cancel: cancel request absent")
    if "cancel_requested" in control.get("emitted_events", []):
        errors.append("control: unexpected cancel request")
    if any(cancel.get("owner_release", {}).get(k) != control.get("owner_release", {}).get(k)
           for k in ("verified", "keys_down", "buttons_down")):
        errors.append("pair: release state differs")
    if cancel.get("terminal", {}).get("status") == control.get("terminal", {}).get("status"):
        errors.append("pair: no terminal-status difference")
    return errors


def main():
    cancel = json.loads((ROOT / "RUN-01.json").read_text(encoding="utf-8"))
    control = json.loads((ROOT / "RUN-02.json").read_text(encoding="utf-8"))
    errors = check(cancel, control)
    corruptions = []
    bad = copy.deepcopy(cancel)
    bad["owner_release"]["verified"] = False
    corruptions.append(check(bad, control))
    bad = copy.deepcopy(cancel)
    bad["input_released_count"] = 2
    corruptions.append(check(bad, control))
    bad = copy.deepcopy(cancel)
    bad["terminal"]["status"] = "completed"
    corruptions.append(check(bad, control))
    result = {
        "audit": "CROSS_COMPONENT_POST_SAMPLE_CANCEL_AUDIT_V1",
        "result": "PASS_SCOPED_REPRODUCTION" if not errors and all(corruptions) else "FAIL",
        "errors": errors,
        "negative_controls_rejected": all(corruptions),
        "negative_control_error_counts": [len(x) for x in corruptions],
        "interpretation": "The current owner recheck preserves cancellation cause across the forced post-sample boundary; the executor publishes the verified-empty release before terminal. Ordinary release remains an un-interrupted completion. Fake-Xlib composition only; no physical input or task effect.",
    }
    (ROOT / "AUDIT-01.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
