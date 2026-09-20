#!/usr/bin/env python3
"""Independent offline audit. Does not import candidate guard or runner."""
import copy
import json
import sys
from pathlib import Path


def errors_for(result):
    errors = []
    events = result.get("events")
    if not isinstance(events, list):
        return ["events not a list"]
    ready = [e["identity"] for e in events if e.get("event") == "fixture_ready"]
    stale = next((e for e in events if e.get("event") == "stale_admission"), None)
    fresh = next((e for e in events if e.get("event") == "fresh_positive_control"), None)
    precondition = next((e for e in events if e.get("event") == "preinput_precondition"), None)
    if precondition is None or precondition.get("passed") is not True:
        errors.append("pre-input identity precondition not satisfied")
    if len(ready) != 2:
        errors.append("expected exactly two fixture identities")
    else:
        old, new = ready
        for key in ("xid", "geometry", "pixel_sha256"):
            if old.get(key) != new.get(key):
                errors.append(f"identity mismatch: {key}")
        for key in ("pid", "start_ticks"):
            if old.get(key) == new.get(key):
                errors.append(f"incarnation did not change: {key}")
        for current in ready:
            xres = current.get("xres", {})
            if xres.get("xid") != current.get("xid") or xres.get("pid") != current.get("pid"):
                errors.append("XRes identity does not match fixture")
    if stale is None:
        errors.append("stale admission row missing")
    elif stale.get("admitted") is not False or stale.get("bridge_called") is not False or stale.get("emissions") != 0 or stale.get("effect_exists") is not False:
        errors.append("stale alias was not refused before emission/effect")
    if fresh is None:
        errors.append("fresh positive control row missing")
    elif (fresh.get("admitted") is not True or fresh.get("bridge_called") is not True
          or fresh.get("click", {}).get("emissions") != 1
          or fresh.get("click", {}).get("button1_down_after") is not False
          or fresh.get("effect", {}).get("count") != 1
          or (len(ready) == 2 and fresh.get("effect", {}).get("pid") != ready[1].get("pid"))):
        errors.append("fresh positive-control evidence invalid")
    if result.get("status") != "PASS_SCOPED_STALE_REFUSAL_AND_FRESH_CONTROL":
        errors.append("runner status not scoped PASS")
    if result.get("final_emissions") != 1:
        errors.append("unexpected final bridge emission count")
    return errors


def main(path):
    raw = json.loads(Path(path).read_text())
    errors = errors_for(raw)
    controls = {}
    if not errors:
        for label, change in (
            ("mutate_xid", lambda r: r["events"][1]["identity"].__setitem__("xid", -1)),
            ("admit_stale", lambda r: next(e for e in r["events"] if e.get("event") == "stale_admission").__setitem__("admitted", True)),
            ("hide_emission", lambda r: next(e for e in r["events"] if e.get("event") == "fresh_positive_control")["click"].__setitem__("emissions", 0)),
        ):
            damaged = copy.deepcopy(raw)
            change(damaged)
            controls[label] = bool(errors_for(damaged))
        if not all(controls.values()):
            errors.append("corruption challenge escaped independent checks")
    audit = {"status": "PASS_INDEPENDENT_AUDIT" if not errors else "FAIL_AUDIT",
             "errors": errors, "corruption_controls_rejected": controls}
    print(json.dumps(audit, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
