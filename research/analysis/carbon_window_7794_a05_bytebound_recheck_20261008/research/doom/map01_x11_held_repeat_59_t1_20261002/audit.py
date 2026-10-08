"""Independent raw-only audit for Issue #59 held-key repeat delivery."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMAGE = "sha256:fc3022d265f465748e0a39491e28f8447d0066266e00d2a8a9144e866bf148ed6"
X_KEY_PRESS = 2


def errors_for(raw, fixture, freeze, verify_sources=True):
    errors = []
    if raw.get("schema") != "issue59-x11-held-repeat-raw-v1":
        errors.append("raw schema mismatch")
    if raw.get("allocation_id") != fixture.get("allocation_id"):
        errors.append("allocation identity mismatch")
    if raw.get("main_sha") != fixture.get("main_sha"):
        errors.append("main identity mismatch")
    if raw.get("image_digest") != IMAGE or freeze.get("image_digest") != IMAGE:
        errors.append("image digest mismatch")
    if raw.get("candidate_invocations") != 1 or raw.get("retries") != 0:
        errors.append("formal invocation/retry count mismatch")
    if raw.get("xvfb_tcp_enabled") is not False:
        errors.append("Xvfb TCP must be disabled")
    if raw.get("xvfb_exit_code") != 0 or raw.get("xvfb_socket_removed") is not True or raw.get("xvfb_lock_removed") is not True:
        errors.append("private Xvfb cleanup incomplete")
    if raw.get("xvfb_stderr"):
        errors.append("unexpected Xvfb stderr")
    if verify_sources:
        hashes = {
            "candidate_sha256": hashlib.sha256((ROOT / "candidate.py").read_bytes()).hexdigest(),
            "fixture_sha256": hashlib.sha256((ROOT / "fixture.json").read_bytes()).hexdigest(),
            "auditor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "plan_sha256": hashlib.sha256((ROOT / "PLAN.md").read_bytes()).hexdigest(),
        }
        for key, value in hashes.items():
            if freeze.get(key) != value:
                errors.append(f"freeze {key} mismatch")
        if raw.get("candidate_sha256") != hashes["candidate_sha256"]:
            errors.append("raw candidate hash mismatch")
        if raw.get("fixture_sha256") != hashes["fixture_sha256"]:
            errors.append("raw fixture hash mismatch")
        if raw.get("freeze_sha256") != hashlib.sha256((ROOT / "FREEZE.json").read_bytes()).hexdigest():
            errors.append("raw freeze hash mismatch")
    code, aid, bid = raw.get("keycode"), raw.get("window_a_id"), raw.get("window_b_id")
    if not all(isinstance(x, int) for x in (code, aid, bid)) or aid == bid:
        errors.append("window/keycode identity invalid")
        return errors
    samples = raw.get("samples")
    if not isinstance(samples, list):
        errors.append("samples must be a list")
        return errors
    by_label = {s.get("label"): s for s in samples if isinstance(s, dict)}
    expected = {"positive_pre": ("positive", aid, False),
                "positive_held": ("positive", aid, True),
                "positive_post": ("positive", aid, False),
                "transfer_pre": ("transfer", aid, False),
                "transfer_a_held": ("transfer", aid, True),
                "transfer_b_held": ("transfer", bid, True),
                "transfer_b_end": ("transfer", bid, True),
                "transfer_post": ("transfer", bid, False)}
    if len(by_label) != len(samples) or set(by_label) != set(expected):
        errors.append("sample labels/uniqueness mismatch")
    for label, (phase, focus, down) in expected.items():
        sample = by_label.get(label)
        if not sample:
            continue
        if sample.get("phase") != phase or sample.get("keycode") != code:
            errors.append(f"sample identity mismatch at {label}")
        if sample.get("focus_window_id") != focus or sample.get("expected_focus_window_id") != focus:
            errors.append(f"focus mismatch at {label}")
        try:
            bitmap = bytes.fromhex(sample["bitmap_hex"])
            observed = bool(bitmap[code // 8] & (1 << (code % 8))) if len(bitmap) == 32 else None
        except (ValueError, KeyError, TypeError):
            observed = None
        if observed is None or observed != down or sample.get("key_down") is not down:
            errors.append(f"keymap state/bitmap mismatch at {label}")
    times = [s.get("observed_ns") for s in samples]
    if any(not isinstance(t, int) for t in times) or times != sorted(times):
        errors.append("sample monotonic timestamps invalid")
    repeat = raw.get("repeat_control", {})
    if repeat.get("global_auto_repeat") != 1:
        errors.append("X server global autorepeat was not enabled")
    events = raw.get("events")
    if not isinstance(events, list):
        errors.append("events must be a list")
        return errors
    if any(not isinstance(e.get("received_ns"), int) for e in events):
        errors.append("event timestamp missing")
    positive = [e for e in events if e.get("phase") == "positive_held" and
                e.get("type") == X_KEY_PRESS and e.get("window_id") == aid and
                e.get("detail") == code]
    transfer_a = [e for e in events if e.get("phase") == "transfer_a_held" and
                  e.get("type") == X_KEY_PRESS and e.get("window_id") == aid and
                  e.get("detail") == code]
    b_start, end, release = (raw.get("transfer_b_start_ns"),
                             raw.get("transfer_observe_end_ns"),
                             raw.get("transfer_release_action_ns"))
    if not all(isinstance(t, int) for t in (b_start, end, release)) or not b_start <= end <= release:
        errors.append("transfer observation interval invalid")
        b_events = []
    else:
        b_events = [e for e in events if e.get("phase") == "transfer_b_held" and
                    e.get("type") == X_KEY_PRESS and e.get("window_id") == bid and
                    e.get("detail") == code and b_start <= e["received_ns"] <= end]
    if raw.get("a_received_initial_transfer_press") is not True or not transfer_a:
        errors.append("A initial held-transfer press positive control missing")
    if len(positive) < fixture.get("minimum_positive_repeat_keypresses", 2):
        errors.append("positive repeat stream not established on A")
    if len(events) == 0:
        errors.append("no application events observed")
    # The scientific distinction: a well-formed run with zero B repeats is FAIL,
    # not an audit error. Construction validity and hypothesis outcome stay apart.
    return errors


def disposition(raw, fixture, freeze, verify_sources=True):
    errors = errors_for(raw, fixture, freeze, verify_sources)
    if errors:
        return "STOP_OR_AUDIT_ERROR", errors
    code, bid = raw["keycode"], raw["window_b_id"]
    start, end = raw["transfer_b_start_ns"], raw["transfer_observe_end_ns"]
    b_repeats = [e for e in raw["events"] if e.get("phase") == "transfer_b_held" and
        e.get("type") == X_KEY_PRESS and e.get("window_id") == bid and
        e.get("detail") == code and start <= e["received_ns"] <= end]
    if b_repeats:
        return "PASS_X11_HELD_REPEAT_REACHES_NEW_FOCUS", []
    return "FAIL_X11_HELD_REPEAT_NOT_OBSERVED_IN_BOUNDED_WINDOW", []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    raw = json.loads(Path(args.raw).read_text(encoding="utf-8"))
    fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    result, errors = disposition(raw, fixture, freeze)
    report = {"schema": "issue59-x11-held-repeat-audit-v1",
        "allocation_id": fixture["allocation_id"], "disposition": result,
        "errors": errors,
        "positive_repeat_count_a": sum(e.get("phase") == "positive_held" and
            e.get("type") == X_KEY_PRESS and e.get("window_id") == raw.get("window_a_id") and
            e.get("detail") == raw.get("keycode") for e in raw.get("events", [])),
        "transfer_repeat_count_b": sum(e.get("phase") == "transfer_b_held" and
            e.get("type") == X_KEY_PRESS and e.get("window_id") == raw.get("window_b_id") and
            e.get("detail") == raw.get("keycode") and raw.get("transfer_b_start_ns", 0) <= e.get("received_ns", -1) <= raw.get("transfer_observe_end_ns", -1) for e in raw.get("events", [])),
        "auditor_invocations": 1, "retries": 0}
    Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
