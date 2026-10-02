"""Independent raw-only audit for callback-state effects in Issue #59 T2."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMAGE = "sha256:fc3022d265f465748e0a39491e28f8447d0066266e00d2a8a9144e866bf148ed6"


def validate(raw, fixture, freeze, verify_sources=True):
    errors = []
    if raw.get("schema") != "issue59-x11-callback-effect-raw-v1": errors.append("raw schema mismatch")
    if raw.get("allocation_id") != fixture.get("allocation_id"): errors.append("allocation mismatch")
    if raw.get("main_sha") != fixture.get("main_sha"): errors.append("source main mismatch")
    if raw.get("image_digest") != IMAGE or freeze.get("image_digest") != IMAGE: errors.append("image digest mismatch")
    if raw.get("candidate_invocations") != 1 or raw.get("retries") != 0: errors.append("invocation/retry count mismatch")
    if raw.get("xvfb_tcp_enabled") is not False: errors.append("Xvfb TCP enabled")
    if raw.get("xvfb_exit_code") != 0 or raw.get("xvfb_socket_removed") is not True or raw.get("xvfb_lock_removed") is not True: errors.append("Xvfb cleanup incomplete")
    if raw.get("xvfb_stderr"): errors.append("unexpected Xvfb stderr")
    if verify_sources:
        for field, path in (("candidate_sha256", "candidate.py"), ("fixture_sha256", "fixture.json"),
                            ("auditor_sha256", "audit.py"), ("plan_sha256", "PLAN.md")):
            actual = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            if freeze.get(field) != actual: errors.append(f"freeze {field} mismatch")
            if field in ("candidate_sha256", "fixture_sha256") and raw.get(field) != actual:
                errors.append(f"raw {field} mismatch")
        if raw.get("freeze_sha256") != hashlib.sha256((ROOT / "FREEZE.json").read_bytes()).hexdigest(): errors.append("freeze file hash mismatch")
    code, aid, bid = raw.get("keycode"), raw.get("window_a_id"), raw.get("window_b_id")
    if not all(isinstance(x, int) for x in (code, aid, bid)) or aid == bid:
        errors.append("window/keycode identity invalid"); return errors
    expected = {"positive_pre": ("positive", aid, False), "positive_held": ("positive", aid, True),
        "positive_post": ("positive", aid, False), "transfer_pre": ("transfer", aid, False),
        "transfer_a_held": ("transfer", aid, True), "transfer_b_held": ("transfer", bid, True),
        "transfer_b_end": ("transfer", bid, True), "transfer_post": ("transfer", bid, False)}
    samples = raw.get("samples")
    if not isinstance(samples, list): errors.append("samples missing"); return errors
    by_label = {s.get("label"): s for s in samples if isinstance(s, dict)}
    if len(by_label) != len(samples) or set(by_label) != set(expected): errors.append("sample label/uniqueness mismatch")
    for label, (phase, focus, down) in expected.items():
        s = by_label.get(label)
        if not s: continue
        if s.get("phase") != phase or s.get("focus_window_id") != focus or s.get("expected_focus_window_id") != focus: errors.append(f"focus/phase mismatch at {label}")
        if s.get("keycode") != code: errors.append(f"keycode mismatch at {label}")
        try:
            bitmap = bytes.fromhex(s["bitmap_hex"])
            bit = bool(bitmap[code // 8] & (1 << (code % 8))) if len(bitmap) == 32 else None
        except (ValueError, KeyError, TypeError): bit = None
        if bit is not down or s.get("key_down") is not down: errors.append(f"bitmap/down mismatch at {label}")
    stimes = [s.get("observed_ns") for s in samples]
    if any(not isinstance(t, int) for t in stimes) or stimes != sorted(stimes): errors.append("sample timestamp order invalid")
    if raw.get("repeat_control", {}).get("global_auto_repeat") != 1: errors.append("global autorepeat not enabled")

    actions = raw.get("actions", [])
    shape = [(a.get("phase"), a.get("operation"), a.get("window_id"), a.get("event_type")) for a in actions]
    wanted = [("positive", "focus", aid, None), ("positive", "press", None, 2),
        ("positive", "release", None, 3), ("transfer", "focus", aid, None),
        ("transfer", "press", None, 2), ("transfer", "focus", bid, None),
        ("transfer", "release", None, 3)]
    if shape != wanted: errors.append("ordered XTEST/focus action ledger mismatch")
    atimes = [(a.get("started_ns"), a.get("sync_returned_ns")) for a in actions]
    if any(not isinstance(x, int) or not isinstance(y, int) or y < x for x, y in atimes): errors.append("action timestamps invalid")
    elif [x for pair in atimes for x in pair] != sorted(x for pair in atimes for x in pair): errors.append("action timestamps not monotonic")

    events, effects = raw.get("events"), raw.get("callback_effects")
    if not isinstance(events, list) or not isinstance(effects, list): errors.append("event/effect stream missing"); return errors
    if [e.get("event_id") for e in events] != list(range(len(events))): errors.append("event IDs not contiguous")
    event_by_id = {e.get("event_id"): e for e in events}
    press_events = [e for e in events if e.get("type") == 2 and e.get("detail") == code and e.get("window_id") in (aid, bid)]
    if len(effects) != len(press_events): errors.append("W KeyPress/callback effect count mismatch")
    if [x.get("event_id") for x in effects] != [e.get("event_id") for e in press_events]: errors.append("callback effects do not link one-to-one in event order")
    counters = {aid: 0, bid: 0}
    for idx, effect in enumerate(effects):
        event = event_by_id.get(effect.get("event_id"))
        window = effect.get("window_id")
        if event is None or window not in counters: errors.append(f"effect event/window identity invalid at {idx}"); continue
        if event.get("type") != 2 or event.get("detail") != code or event.get("window_id") != window: errors.append(f"effect linked to wrong event at {idx}")
        if effect.get("effect_id") != idx or effect.get("phase") != event.get("phase") or effect.get("keycode") != code: errors.append(f"effect identity mismatch at {idx}")
        if effect.get("before") != counters[window] or effect.get("after") != counters[window] + 1: errors.append(f"counter transition mismatch at {idx}")
        counters[window] += 1
        if effect.get("focus_window_id") != window or effect.get("key_down") is not True: errors.append(f"effect lacked focused/down evidence at {idx}")
        if effect.get("effect_ns", 0) < effect.get("event_received_ns", 0): errors.append(f"effect predates event receipt at {idx}")
        try:
            bitmap = bytes.fromhex(effect.get("bitmap_hex", ""))
            down = len(bitmap) == 32 and bool(bitmap[code // 8] & (1 << (code % 8)))
        except (ValueError, TypeError): down = False
        if not down: errors.append(f"effect full bitmap not down at {idx}")
    if raw.get("effects_final") != {str(k): v for k, v in counters.items()}: errors.append("final per-window counters mismatch")
    if raw.get("a_received_initial_transfer_press") is not True: errors.append("A transfer positive missing")
    if not any(e.get("phase") == "positive_held" and e.get("window_id") == aid for e in effects): errors.append("positive callback control missing")
    if not isinstance(raw.get("transfer_b_start_ns"), int) or not isinstance(raw.get("transfer_b_end_ns"), int) or not isinstance(raw.get("transfer_release_action_ns"), int): errors.append("B held interval timestamps missing")
    else:
        if not raw["transfer_b_start_ns"] <= raw["transfer_b_end_ns"] <= raw["transfer_release_action_ns"]: errors.append("B callback window invalid")
        if any(e.get("phase") == "transfer_b_held" and not raw["transfer_b_start_ns"] <= e["event_received_ns"] <= raw["transfer_b_end_ns"] for e in effects): errors.append("B effect outside held observation window")
    return errors


def result(raw, fixture, freeze, verify_sources=True):
    errors = validate(raw, fixture, freeze, verify_sources)
    if errors: return "STOP_OR_AUDIT_ERROR", errors
    aid, bid, code = raw["window_a_id"], raw["window_b_id"], raw["keycode"]
    a_count = sum(e.get("phase") == "positive_held" and e.get("window_id") == aid and e.get("keycode") == code for e in raw["callback_effects"])
    b_count = sum(e.get("phase") == "transfer_b_held" and e.get("window_id") == bid and e.get("keycode") == code for e in raw["callback_effects"])
    if a_count < fixture.get("minimum_positive_callback_effects", 2): return "STOP_POSITIVE_CONTROL_MISSING", []
    if b_count == 0: return "FAIL_NO_CALLBACK_EFFECT_IN_NEW_FOCUS", []
    return "PASS_X11_CALLBACK_EFFECT_MATCHES_DELIVERED_KEYPRESS", []


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--raw", required=True); parser.add_argument("--out", required=True); args = parser.parse_args()
    raw = json.loads(Path(args.raw).read_text()); fixture = json.loads((ROOT / "fixture.json").read_text()); freeze = json.loads((ROOT / "FREEZE.json").read_text())
    disposition, errors = result(raw, fixture, freeze)
    report = {"schema":"issue59-x11-callback-effect-audit-v1","allocation_id":fixture["allocation_id"],"disposition":disposition,"errors":errors,
        "positive_a_callback_effects":sum(x["phase"]=="positive_held" and x["window_id"]==raw["window_a_id"] for x in raw["callback_effects"]),
        "transfer_b_callback_effects":sum(x["phase"]=="transfer_b_held" and x["window_id"]==raw["window_b_id"] for x in raw["callback_effects"]),"auditor_invocations":1,"retries":0}
    Path(args.out).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n"); print(json.dumps(report,sort_keys=True))


if __name__ == "__main__": main()
