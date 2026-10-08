#!/usr/bin/env python3
"""Strict offline structural audit for the retained Issue #3675 trace."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


EVENTS = (
    "fixture_ready",
    "fixture_ready",
    "preinput_precondition",
    "stale_admission",
    "fresh_positive_control",
)
TOP_KEYS = {"allocation", "events", "final_emissions", "freeze_sha256", "status"}
IDENTITY_KEYS = {"geometry", "pid", "pixel_sha256", "start_ticks", "xid", "xres"}
XRES_KEYS = {"client_base", "pid", "resource_mask", "xid", "xres_major", "xres_minor"}


def _exact_keys(value, expected):
    return isinstance(value, dict) and set(value) == expected


def errors_for(result):
    errors = []
    if not _exact_keys(result, TOP_KEYS):
        return ["top-level schema mismatch"]
    events = result["events"]
    if not isinstance(events, list) or len(events) != len(EVENTS):
        return ["event count mismatch"]
    names = [e.get("event") if isinstance(e, dict) else None for e in events]
    if tuple(names) != EVENTS:
        errors.append("event sequence mismatch")
        return errors

    for row in events:
        if not isinstance(row, dict):
            return ["event row is not an object"]
    for row in events[:2]:
        if not _exact_keys(row, {"event", "identity"}) or not _exact_keys(row["identity"], IDENTITY_KEYS):
            errors.append("fixture_ready schema mismatch")
            continue
        identity = row["identity"]
        if not _exact_keys(identity["xres"], XRES_KEYS):
            errors.append("XRes schema mismatch")
        elif identity["xres"]["xid"] != identity["xid"] or identity["xres"]["pid"] != identity["pid"]:
            errors.append("XRes identity mismatch")

    old, new = (row.get("identity", {}) for row in events[:2])
    if _exact_keys(old, IDENTITY_KEYS) and _exact_keys(new, IDENTITY_KEYS):
        for key in ("xid", "geometry", "pixel_sha256"):
            if old[key] != new[key]:
                errors.append(f"identity mismatch: {key}")
        for key in ("pid", "start_ticks"):
            if old[key] == new[key]:
                errors.append(f"incarnation did not change: {key}")

    pre, stale, fresh = events[2:]
    if not _exact_keys(pre, {"event", "passed"}) or pre.get("passed") is not True:
        errors.append("pre-input precondition invalid")
    if not _exact_keys(stale, {"event", "admitted", "bridge_called", "would_call_bridge", "emissions", "effect_exists"}):
        errors.append("stale-admission schema mismatch")
    elif (stale["admitted"] is not False or stale["bridge_called"] is not False
          or stale["would_call_bridge"] is not False or stale["emissions"] != 0
          or stale["effect_exists"] is not False):
        errors.append("stale alias was not refused before emission/effect")
    if not _exact_keys(fresh, {"event", "admitted", "bridge_called", "click", "effect"}):
        errors.append("fresh-control schema mismatch")
    else:
        click, effect = fresh["click"], fresh["effect"]
        if not _exact_keys(click, {"emissions", "button1_down_after"}) or (
            click.get("emissions") != 1 or click.get("button1_down_after") is not False
        ):
            errors.append("fresh click evidence invalid")
        if not _exact_keys(effect, {"count", "pid"}) or (
            effect.get("count") != 1 or effect.get("pid") != new.get("pid")
        ):
            errors.append("fresh effect evidence invalid")
        if fresh["admitted"] is not True or fresh["bridge_called"] is not True:
            errors.append("fresh control not admitted/called")

    if result["allocation"] != "issue3555-xres-guard-orbstack-v2-formal-01":
        errors.append("allocation mismatch")
    if result["status"] != "PASS_SCOPED_STALE_REFUSAL_AND_FRESH_CONTROL":
        errors.append("runner status mismatch")
    if result["final_emissions"] != 1:
        errors.append("final emission count mismatch")
    if not isinstance(result["freeze_sha256"], str) or len(result["freeze_sha256"]) != 64:
        errors.append("freeze digest malformed")
    return errors


def verify_source_hashes(study_freeze_path):
    manifest = json.loads(Path(study_freeze_path).read_text(encoding="utf-8"))
    errors = []
    for relative, expected in manifest["source_sha256"].items():
        source = Path(__file__).resolve().parent / relative
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"source hash mismatch: {relative}")
    return errors


def audit(raw_path, freeze_path, study_freeze_path):
    raw_bytes = Path(raw_path).read_bytes()
    freeze_bytes = Path(freeze_path).read_bytes()
    raw = json.loads(raw_bytes)
    errors = errors_for(raw) + verify_source_hashes(study_freeze_path)
    freeze_sha = hashlib.sha256(freeze_bytes).hexdigest()
    if raw.get("freeze_sha256") != freeze_sha:
        errors.append("raw result is not bound to supplied freeze manifest")
    controls = {}
    if not errors:
        changes = (
            ("mutate_xid", lambda r: r["events"][1]["identity"].__setitem__("xid", -1)),
            ("admit_stale", lambda r: r["events"][3].__setitem__("admitted", True)),
            ("hide_emission", lambda r: r["events"][4]["click"].__setitem__("emissions", 0)),
            ("unexpected_event", lambda r: r["events"].append({"event": "unexpected"})),
            ("duplicate_stale", lambda r: r["events"].append(copy.deepcopy(r["events"][3]))),
            ("contradictory_would_call_bridge", lambda r: r["events"][3].__setitem__("would_call_bridge", True)),
            ("reordered_transitions", lambda r: r["events"].__setitem__(slice(2, 5), [r["events"][3], r["events"][2], r["events"][4]])),
            ("unsupported_extra_field", lambda r: r["events"][0].__setitem__("extra", True)),
            ("missing_transition", lambda r: r["events"].pop(3)),
        )
        for label, mutate in changes:
            damaged = copy.deepcopy(raw)
            mutate(damaged)
            controls[label] = bool(errors_for(damaged))
        if not all(controls.values()):
            errors.append("a corruption challenge escaped strict checks")
    return {
        "status": "PASS_OFFLINE_STRUCTURAL_AUDIT" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "corruption_controls_rejected": controls,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_json", type=Path)
    parser.add_argument("--freeze", required=True, type=Path)
    parser.add_argument("--study-freeze", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    result = audit(args.raw_json, args.freeze, args.study_freeze)
    rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

# mutation copy only
