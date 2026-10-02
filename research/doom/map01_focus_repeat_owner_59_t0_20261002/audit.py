"""Independent raw-record classifier and separate-process CLI for Issue #59."""

import argparse
from collections.abc import Mapping
import json
from pathlib import Path
import sys


SCHEMA = "issue59-focus-repeat-owner-raw-v1"
FROZEN_BASE_MAIN = "a25f7c5da72e8d16094efe491424b6e8d63d1a8b"
EXPECTED_SOURCE_SHA256 = {
    "input_owner_v10.py": "ceae7d9983cd0ba13a35e01ce2ce7dbbf03a0397b23ddc123b0110b4d4de670b",
    "executor_v3.py": "ea3fa8c9751a6a41b4814ad6e0d03bec85166765b0a41d2488a51750d17b3a4a",
    "lease.py": "e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f",
}
EXPECTED_SOURCE_GIT_BLOBS = {
    "input_owner_v10.py": "341b3c01649943ddaad5f28431a792c4889cc36e",
    "executor_v3.py": "2b072454fd81c41bf9e025217afc78020c7059de",
    "lease.py": "b9dac6bb4063928354733d79bf371909a288a3d1",
}


def _is_ns(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _invalid():
    return {"status": "HOLD_RAW_RECORD_INVALID", "new_focus_keypresses_before_release": 0}


def classify(raw):
    """Classify raw event records; summary labels are deliberately not inputs."""
    if not isinstance(raw, Mapping) or raw.get("schema") != SCHEMA:
        return _invalid()
    hashes = raw.get("source_sha256")
    if (raw.get("allocation_id") != "ISSUE59-FOCUS-REPEAT-OWNER-T0-20261002-01"
            or raw.get("base_main_sha") != FROZEN_BASE_MAIN
            or raw.get("candidate_invocations") != 1 or raw.get("retries") != 0
            or raw.get("xvfb_exit_code") != 0
            or raw.get("xvfb_socket_removed") is not True
            or raw.get("xvfb_lock_removed") is not True
            or not isinstance(hashes, Mapping) or dict(hashes) != EXPECTED_SOURCE_SHA256
            or raw.get("source_git_blobs") != EXPECTED_SOURCE_GIT_BLOBS):
        return _invalid()

    control, trial = raw.get("positive_control"), raw.get("trial")
    if not isinstance(control, Mapping) or not isinstance(trial, Mapping):
        return _invalid()
    control_window, control_key = control.get("window"), control.get("keycode")
    repeats = control.get("repeat_events")
    if not isinstance(control_window, str) or not isinstance(control_key, int) or isinstance(control_key, bool):
        return _invalid()
    if not isinstance(repeats, list):
        return _invalid()
    for event in repeats:
        if (not isinstance(event, Mapping) or event.get("type") != "KeyPress"
                or event.get("window") != control_window or event.get("keycode") != control_key
                or not _is_ns(event.get("time_ns"))):
            return _invalid()
    if control.get("verified_release") is not True or len(repeats) < 2:
        return {"status": "STOP_REPEAT_STIMULUS_NOT_ESTABLISHED", "new_focus_keypresses_before_release": 0}
    if any(a["time_ns"] >= b["time_ns"] for a, b in zip(repeats, repeats[1:])):
        return _invalid()

    admission, transfer = trial.get("owner_admission"), trial.get("focus_change")
    release, samples, pump = (trial.get("owner_release"), trial.get("owner_focus_samples"),
                              trial.get("new_focus_event_pump"))
    if not all(isinstance(x, Mapping) for x in (admission, transfer, release, pump)) or not isinstance(samples, list):
        return _invalid()
    source, target = transfer.get("from"), transfer.get("to")
    key = admission.get("keycode")
    admitted, ack = admission.get("admitted_ns"), admission.get("ack_ns")
    request, focus_done = transfer.get("request_ns"), transfer.get("sync_returned_ns")
    focus_observed = transfer.get("observed_ns")
    verified = release.get("verified_ns")
    if (not isinstance(source, str) or not isinstance(target, str) or source == target
            or not isinstance(key, int) or isinstance(key, bool)
            or admission.get("window") != source or key != control_key or control_window != source
            or not all(_is_ns(x) for x in (admitted, ack, request, focus_done, focus_observed,
                                             verified))
            or transfer.get("observed_focus") != target
            or not (admitted <= ack < request <= focus_done <= focus_observed <= verified)
            or release.get("keycode") != key or release.get("reason") != "focus_changed"):
        return _invalid()
    saw_old = saw_new = False
    previous_end = -1
    for sample in samples:
        if not isinstance(sample, Mapping):
            return _invalid()
        start, end = sample.get("started_ns"), sample.get("finished_ns")
        focus = sample.get("focus")
        if not _is_ns(start) or not _is_ns(end) or start > end or start < previous_end or not isinstance(focus, str):
            return _invalid()
        previous_end = end
        if focus == source and end <= request:
            saw_old = True
        if focus == target and start >= request and end <= verified:
            saw_new = True
    if not (saw_old and saw_new):
        return _invalid()
    if (release.get("verified_empty") is not True or release.get("verified") is False
            or release.get("keys_down") != []):
        return {"status": "HOLD_RELEASE_NOT_VERIFIED", "new_focus_keypresses_before_release": 0}

    if (pump.get("window") != target or pump.get("complete") is not True
            or not _is_ns(pump.get("started_ns")) or not _is_ns(pump.get("stopped_ns"))
            or pump["started_ns"] > request or pump["stopped_ns"] < verified):
        return {"status": "HOLD_EVENT_COVERAGE_INCOMPLETE", "new_focus_keypresses_before_release": 0}
    events = pump.get("events")
    if not isinstance(events, list):
        return _invalid()
    for event in events:
        if not isinstance(event, Mapping) or event.get("type") not in ("KeyPress", "KeyRelease"):
            return _invalid()
        if (not isinstance(event.get("window"), str)
                or not isinstance(event.get("keycode"), int) or isinstance(event.get("keycode"), bool)
                or not _is_ns(event.get("time_ns"))):
            return _invalid()
    ordered = sorted(events, key=lambda e: e["time_ns"])
    if events != ordered:
        return _invalid()
    count = sum(1 for e in events if e["type"] == "KeyPress" and e["window"] == target
                and e["keycode"] == key and request <= e["time_ns"] < verified)
    status = ("COUNTEREXAMPLE_REPEAT_BEFORE_VERIFIED_RELEASE" if count
              else "PASS_OWNER_FOCUS_RELEASE_SCOPED")
    return {"status": status, "new_focus_keypresses_before_release": count}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True, help="candidate raw.json input")
    parser.add_argument("--out", type=Path, required=True, help="new classification JSON path")
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error(f"refusing to overwrite auditor output: {args.out}")
    try:
        raw = json.loads(args.raw.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(f"cannot read candidate raw JSON: {exc}")
    result = classify(raw)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
