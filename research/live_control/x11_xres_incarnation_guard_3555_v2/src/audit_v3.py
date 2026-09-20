#!/usr/bin/env python3
"""Strict independent structural audit for the frozen XRes v2 allocation.

This successor intentionally leaves audit.py and every frozen artifact intact.
It validates the exact bounded event protocol, not general X11 correctness.
"""
import argparse
import hashlib
import json
from pathlib import Path


def _keys(value, expected, where, errors):
    if not isinstance(value, dict):
        errors.append(f"{where} is not an object")
    elif set(value) != set(expected):
        errors.append(f"{where} fields differ: expected {sorted(expected)}, got {sorted(value)}")


def _bool(value, expected, where, errors):
    if type(value) is not bool or value is not expected:
        errors.append(f"{where} must be {expected}")


def _int(value, expected, where, errors):
    if type(value) is not int or value != expected:
        errors.append(f"{where} must be integer {expected}")


def errors_for(result):
    errors = []
    _keys(result, {"allocation", "events", "final_emissions", "freeze_sha256", "status"}, "result", errors)
    if errors and not isinstance(result, dict):
        return errors
    if result.get("allocation") != "issue3555-xres-guard-orbstack-v2-formal-01":
        errors.append("unexpected allocation")
    if result.get("status") != "PASS_SCOPED_STALE_REFUSAL_AND_FRESH_CONTROL":
        errors.append("runner status not scoped PASS")
    _int(result.get("final_emissions"), 1, "final_emissions", errors)
    freeze = result.get("freeze_sha256")
    if not isinstance(freeze, str) or len(freeze) != 64 or any(c not in "0123456789abcdef" for c in freeze):
        errors.append("freeze_sha256 is not lowercase SHA-256 hex")

    events = result.get("events")
    if not isinstance(events, list):
        errors.append("events not a list")
        return errors
    kinds = [e.get("event") if isinstance(e, dict) else None for e in events]
    expected = ["fixture_ready", "fixture_ready", "preinput_precondition", "stale_admission", "fresh_positive_control"]
    if kinds != expected:
        errors.append("event sequence/cardinality differs from frozen protocol")
    if len(events) != 5:
        return errors

    ready = []
    for index, event in enumerate(events[:2]):
        _keys(event, {"event", "identity"}, f"events[{index}]", errors)
        identity = event.get("identity") if isinstance(event, dict) else None
        identity_keys = {"geometry", "pid", "pixel_sha256", "start_ticks", "xid", "xres"}
        _keys(identity, identity_keys, f"events[{index}].identity", errors)
        if not isinstance(identity, dict):
            continue
        ready.append(identity)
        for name in ("pid", "start_ticks", "xid"):
            value = identity.get(name)
            if type(value) is not int or value <= 0:
                errors.append(f"events[{index}].identity.{name} must be a positive integer")
        geometry = identity.get("geometry")
        if (not isinstance(geometry, list) or len(geometry) != 5
                or any(type(v) is not int for v in geometry)):
            errors.append(f"events[{index}].identity.geometry must be five integers")
        digest = identity.get("pixel_sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            errors.append(f"events[{index}].identity.pixel_sha256 is invalid")
        xres = identity.get("xres")
        _keys(xres, {"client_base", "pid", "resource_mask", "xid", "xres_major", "xres_minor"}, f"events[{index}].identity.xres", errors)
        if isinstance(xres, dict):
            if xres.get("xid") != identity.get("xid") or xres.get("pid") != identity.get("pid"):
                errors.append(f"events[{index}] XRes identity mismatch")
            if xres.get("xres_major") != 1 or xres.get("xres_minor") != 2:
                errors.append(f"events[{index}] unexpected XRes version")

    if len(ready) == 2:
        old, new = ready
        for name in ("xid", "geometry", "pixel_sha256"):
            if old.get(name) != new.get(name):
                errors.append(f"identity mismatch: {name}")
        for name in ("pid", "start_ticks"):
            if old.get(name) == new.get(name):
                errors.append(f"incarnation did not change: {name}")

    pre = events[2]
    _keys(pre, {"event", "passed"}, "preinput_precondition", errors)
    if isinstance(pre, dict):
        _bool(pre.get("passed"), True, "preinput_precondition.passed", errors)

    stale = events[3]
    _keys(stale, {"admitted", "bridge_called", "effect_exists", "emissions", "event", "would_call_bridge"}, "stale_admission", errors)
    if isinstance(stale, dict):
        for name in ("admitted", "bridge_called", "effect_exists", "would_call_bridge"):
            _bool(stale.get(name), False, f"stale_admission.{name}", errors)
        _int(stale.get("emissions"), 0, "stale_admission.emissions", errors)

    fresh = events[4]
    _keys(fresh, {"admitted", "bridge_called", "click", "effect", "event"}, "fresh_positive_control", errors)
    if isinstance(fresh, dict):
        _bool(fresh.get("admitted"), True, "fresh_positive_control.admitted", errors)
        _bool(fresh.get("bridge_called"), True, "fresh_positive_control.bridge_called", errors)
        click = fresh.get("click")
        _keys(click, {"button1_down_after", "emissions"}, "fresh_positive_control.click", errors)
        if isinstance(click, dict):
            _bool(click.get("button1_down_after"), False, "click.button1_down_after", errors)
            _int(click.get("emissions"), 1, "click.emissions", errors)
        effect = fresh.get("effect")
        _keys(effect, {"count", "pid"}, "fresh_positive_control.effect", errors)
        if isinstance(effect, dict):
            _int(effect.get("count"), 1, "effect.count", errors)
            if len(ready) == 2 and effect.get("pid") != ready[1].get("pid"):
                errors.append("effect PID is not the fresh incarnation")
    return errors


def audit(path, freeze_path=None, output_path=None):
    # Git may materialize committed LF text as CRLF on Windows. Bind hashes to
    # canonical repository bytes while preserving the parsed JSON semantics.
    raw_bytes = Path(path).read_bytes().replace(b"\r\n", b"\n")
    raw = json.loads(raw_bytes)
    errors = errors_for(raw)
    if freeze_path is not None:
        freeze_bytes = Path(freeze_path).read_bytes().replace(b"\r\n", b"\n")
        freeze = json.loads(freeze_bytes)
        freeze_sha = hashlib.sha256(freeze_bytes).hexdigest()
        if raw.get("freeze_sha256") != freeze_sha:
            errors.append("raw result is not bound to supplied freeze manifest")
        if freeze.get("allocation") != raw.get("allocation"):
            errors.append("freeze allocation does not match raw result")
    report = {"raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
              "status": "PASS_INDEPENDENT_AUDIT" if not errors else "FAIL_AUDIT",
              "errors": errors}
    rendered = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if output_path:
        Path(output_path).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if not errors else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw_json")
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    return audit(args.raw_json, args.freeze, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
