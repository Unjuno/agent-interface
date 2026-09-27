#!/usr/bin/env python3
"""Exact-byte and strict-type audit for the retained Issue #3675 trace."""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

EVENTS = (
    "fixture_ready", "fixture_ready", "preinput_precondition",
    "stale_admission", "fresh_positive_control",
)
TOP = {"allocation", "events", "final_emissions", "freeze_sha256", "status"}
IDENTITY = {"geometry", "pid", "pixel_sha256", "start_ticks", "xid", "xres"}
XRES = {"client_base", "pid", "resource_mask", "xid", "xres_major", "xres_minor"}


def _exact(value, keys):
    return type(value) is dict and set(value) == keys


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load(data):
    return json.loads(data, object_pairs_hook=_strict_object)


def errors_for(result):
    errors = []
    if not _exact(result, TOP):
        return ["top-level schema mismatch"]
    events = result["events"]
    if type(events) is not list or len(events) != len(EVENTS):
        return ["event count mismatch"]
    if any(type(row) is not dict for row in events):
        return ["event row is not an object"]
    if tuple(row.get("event") for row in events) != EVENTS:
        return ["event sequence mismatch"]

    identities = []
    for row in events[:2]:
        if not _exact(row, {"event", "identity"}) or not _exact(row["identity"], IDENTITY):
            errors.append("fixture_ready schema mismatch")
            identities.append(None)
            continue
        ident = row["identity"]
        identities.append(ident)
        if (type(ident["geometry"]) is not list or len(ident["geometry"]) != 5
                or any(type(n) is not int for n in ident["geometry"])):
            errors.append("geometry type/shape mismatch")
        for key in ("pid", "start_ticks", "xid"):
            if type(ident[key]) is not int or ident[key] <= 0:
                errors.append(f"{key} must be a positive integer")
        if type(ident["pixel_sha256"]) is not str or re.fullmatch(r"[0-9a-f]{64}", ident["pixel_sha256"]) is None:
            errors.append("pixel_sha256 malformed")
        xres = ident["xres"]
        if not _exact(xres, XRES):
            errors.append("XRes schema mismatch")
        else:
            for key in XRES:
                if type(xres[key]) is not int or xres[key] < 0:
                    errors.append(f"XRes {key} must be a nonnegative integer")
            if xres["xid"] != ident["xid"] or xres["pid"] != ident["pid"]:
                errors.append("XRes identity mismatch")
    old, new = identities
    if old is not None and new is not None:
        for key in ("xid", "geometry", "pixel_sha256"):
            if old[key] != new[key]:
                errors.append(f"identity mismatch: {key}")
        for key in ("pid", "start_ticks"):
            if old[key] == new[key]:
                errors.append(f"incarnation did not change: {key}")

    pre, stale, fresh = events[2:]
    if not _exact(pre, {"event", "passed"}) or type(pre.get("passed")) is not bool or pre["passed"] is not True:
        errors.append("pre-input precondition invalid")
    stale_keys = {"event", "admitted", "bridge_called", "would_call_bridge", "emissions", "effect_exists"}
    if not _exact(stale, stale_keys):
        errors.append("stale-admission schema mismatch")
    else:
        for key in ("admitted", "bridge_called", "would_call_bridge", "effect_exists"):
            if type(stale[key]) is not bool or stale[key] is not False:
                errors.append(f"stale {key} must be false")
        if type(stale["emissions"]) is not int or stale["emissions"] != 0:
            errors.append("stale emissions must be integer zero")
    fresh_keys = {"event", "admitted", "bridge_called", "click", "effect"}
    if not _exact(fresh, fresh_keys):
        errors.append("fresh-control schema mismatch")
    else:
        if type(fresh["admitted"]) is not bool or fresh["admitted"] is not True:
            errors.append("fresh admitted must be true")
        if type(fresh["bridge_called"]) is not bool or fresh["bridge_called"] is not True:
            errors.append("fresh bridge_called must be true")
        click, effect = fresh["click"], fresh["effect"]
        if not _exact(click, {"emissions", "button1_down_after"}):
            errors.append("fresh click schema mismatch")
        else:
            if type(click["emissions"]) is not int or click["emissions"] != 1:
                errors.append("fresh emissions must be integer one")
            if type(click["button1_down_after"]) is not bool or click["button1_down_after"] is not False:
                errors.append("button1_down_after must be false")
        if not _exact(effect, {"count", "pid"}):
            errors.append("fresh effect schema mismatch")
        else:
            if type(effect["count"]) is not int or effect["count"] != 1:
                errors.append("effect count must be integer one")
            if type(effect["pid"]) is not int or effect["pid"] <= 0:
                errors.append("effect pid must be a positive integer")
            if new is not None and effect["pid"] != new["pid"]:
                errors.append("effect PID does not match new incarnation")
    if result["allocation"] != "issue3555-xres-guard-orbstack-v2-formal-01":
        errors.append("allocation mismatch")
    if result["status"] != "PASS_SCOPED_STALE_REFUSAL_AND_FRESH_CONTROL":
        errors.append("runner status mismatch")
    if type(result["final_emissions"]) is not int or result["final_emissions"] != 1:
        errors.append("final_emissions must be integer one")
    digest = result["freeze_sha256"]
    if type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        errors.append("freeze digest malformed")
    return errors


def verify_source_hashes(study, source_dir):
    errors = []
    if type(study) is not dict:
        return ["study manifest must be an object"]
    sources = study.get("source_sha256")
    expected_names = {"audit.py", "test_integrity.py"}
    if type(sources) is not dict or set(sources) != expected_names:
        return ["source hash manifest schema mismatch"]
    for relative, expected in sources.items():
        if type(expected) is not str or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
            errors.append(f"source hash malformed: {relative}")
            continue
        path = source_dir / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(f"source hash mismatch: {relative}")
    return errors


def audit(raw_path, freeze_path, study_freeze_path, expected_study_sha256):
    raw_bytes = Path(raw_path).read_bytes()
    freeze_bytes = Path(freeze_path).read_bytes()
    study_bytes = Path(study_freeze_path).read_bytes()
    if type(expected_study_sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", expected_study_sha256) is None:
        return {"status": "FAIL_AUDIT", "errors": ["expected study-manifest SHA-256 is missing or malformed"],
                "corruption_controls_rejected": {}}
    if hashlib.sha256(study_bytes).hexdigest() != expected_study_sha256:
        return {"status": "FAIL_AUDIT", "errors": ["study manifest bytes do not match independently pinned digest"],
                "corruption_controls_rejected": {}}
    try:
        raw = _load(raw_bytes)
        study = _load(study_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return {"status": "FAIL_AUDIT", "errors": [f"invalid JSON: {exc}"], "corruption_controls_rejected": {}}
    errors = errors_for(raw)
    if type(study) is not dict:
        return {"status": "FAIL_AUDIT", "errors": errors + ["study manifest must be an object"],
                "corruption_controls_rejected": {}}
    expected_raw = study.get("predecessor_raw_sha256")
    expected_freeze = study.get("predecessor_freeze_sha256")
    if type(expected_raw) is not str or re.fullmatch(r"[0-9a-f]{64}", expected_raw) is None:
        errors.append("predecessor raw hash malformed")
    elif hashlib.sha256(raw_bytes).hexdigest() != expected_raw:
        errors.append("raw bytes do not match frozen predecessor hash")
    if type(expected_freeze) is not str or re.fullmatch(r"[0-9a-f]{64}", expected_freeze) is None:
        errors.append("predecessor freeze hash malformed")
    elif hashlib.sha256(freeze_bytes).hexdigest() != expected_freeze:
        errors.append("freeze bytes do not match frozen predecessor hash")
    errors.extend(verify_source_hashes(study, Path(__file__).resolve().parent))
    if type(raw) is dict and raw.get("freeze_sha256") != hashlib.sha256(freeze_bytes).hexdigest():
        errors.append("raw result is not bound to supplied predecessor freeze")
    controls = {}
    if not errors:
        mutations = (
            ("unexpected_event", lambda r: r["events"].append({"event": "unexpected"})),
            ("duplicate_stale", lambda r: r["events"].append(copy.deepcopy(r["events"][3]))),
            ("contradictory_would_call", lambda r: r["events"][3].__setitem__("would_call_bridge", True)),
            ("reordered_transitions", lambda r: r["events"].__setitem__(slice(2, 5), [r["events"][3], r["events"][2], r["events"][4]])),
            ("missing_transition", lambda r: r["events"].pop(3)),
            ("extra_field", lambda r: r["events"][0].__setitem__("extra", True)),
            ("final_emissions_bool", lambda r: r.__setitem__("final_emissions", True)),
            ("click_emissions_bool", lambda r: r["events"][4]["click"].__setitem__("emissions", True)),
            ("effect_count_bool", lambda r: r["events"][4]["effect"].__setitem__("count", True)),
        )
        for name, mutate in mutations:
            changed = copy.deepcopy(raw)
            mutate(changed)
            controls[name] = bool(errors_for(changed))
        replacement = copy.deepcopy(raw)
        replacement["events"][0]["identity"]["pixel_sha256"] = "0" * 64
        replacement["events"][1]["identity"]["pixel_sha256"] = "0" * 64
        replacement_bytes = json.dumps(replacement, sort_keys=True).encode("utf-8")
        controls["replacement_raw"] = hashlib.sha256(replacement_bytes).hexdigest() != study.get("predecessor_raw_sha256")
        replacement_freeze = freeze_bytes + b" "
        controls["replacement_freeze"] = hashlib.sha256(replacement_freeze).hexdigest() != study.get("predecessor_freeze_sha256")
        replacement_manifest = copy.deepcopy(study)
        replacement_manifest["predecessor_raw_sha256"] = hashlib.sha256(replacement_bytes).hexdigest()
        replacement_manifest["predecessor_freeze_sha256"] = hashlib.sha256(replacement_freeze).hexdigest()
        replacement_manifest_bytes = json.dumps(replacement_manifest, sort_keys=True).encode("utf-8")
        controls["replacement_study_manifest"] = hashlib.sha256(replacement_manifest_bytes).hexdigest() != expected_study_sha256
        if not all(controls.values()):
            errors.append("a frozen corruption control escaped rejection")
    return {"status": "PASS_OFFLINE_STRUCTURAL_AUDIT" if not errors else "FAIL_AUDIT",
            "errors": errors, "corruption_controls_rejected": controls}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_json", type=Path)
    parser.add_argument("--freeze", required=True, type=Path)
    parser.add_argument("--study-freeze", required=True, type=Path)
    parser.add_argument("--expected-study-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    result = audit(args.raw_json, args.freeze, args.study_freeze, args.expected_study_sha256)
    rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
    args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
