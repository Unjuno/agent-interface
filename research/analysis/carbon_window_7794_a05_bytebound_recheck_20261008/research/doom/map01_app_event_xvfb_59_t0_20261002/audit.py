"""Independent raw-only audit for the Issue #59 X11 delivery experiment."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURE_PATH = ROOT / "fixture.json"
FREEZE_PATH = ROOT / "FREEZE.json"
EXPECTED_IMAGE = "sha256:fc3022d265f465748e0a39491e28f8447d0066266e00d2a8a9144e866bf148ed6"


def key_bit(sample):
    bitmap = bytes.fromhex(sample["bitmap_hex"])
    code = sample["keycode"]
    if len(bitmap) != 32 or not isinstance(code, int) or not 0 <= code < 256:
        raise ValueError("invalid full XQueryKeymap bitmap or keycode")
    return bool(bitmap[code // 8] & (1 << (code % 8)))


def validate(raw, fixture, freeze):
    errors = []
    if raw.get("schema") != "issue59-x11-app-delivery-raw-v1":
        errors.append("wrong raw schema")
    if raw.get("allocation_id") != fixture.get("allocation_id"):
        errors.append("allocation identity mismatch")
    if raw.get("source_main_sha") != fixture.get("main_sha"):
        errors.append("source main identity mismatch")
    if raw.get("image_digest") != EXPECTED_IMAGE:
        errors.append("image digest mismatch")
    freeze_hash = hashlib.sha256(FREEZE_PATH.read_bytes()).hexdigest()
    if raw.get("freeze_sha256") != freeze_hash:
        errors.append("freeze document hash mismatch")
    if raw.get("candidate_sha256") != freeze.get("candidate_sha256"):
        errors.append("candidate source hash differs from freeze")
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != freeze.get("auditor_sha256"):
        errors.append("auditor source hash differs from freeze")
    if hashlib.sha256((ROOT / "test_contract.py").read_bytes()).hexdigest() != freeze.get("construction_tests_sha256"):
        errors.append("construction-test source hash differs from freeze")
    if hashlib.sha256((ROOT / "PLAN.md").read_bytes()).hexdigest() != freeze.get("plan_sha256"):
        errors.append("plan source hash differs from freeze")
    if raw.get("fixture_sha256") != hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest():
        errors.append("fixture source hash differs from freeze")
    if raw.get("candidate_invocations") != 1 or raw.get("retries") != 0:
        errors.append("formal invocation/retry count mismatch")
    if raw.get("xvfb_tcp_enabled") is not False:
        errors.append("Xvfb TCP must be disabled")
    if raw.get("xvfb_exit_code_after_controlled_terminate") != 0:
        errors.append("private Xvfb did not exit cleanly")
    if raw.get("xvfb_socket_removed") is not True or raw.get("xvfb_lock_removed") is not True:
        errors.append("private Xvfb socket/lock cleanup incomplete")
    if raw.get("xvfb_stderr_fatal") is not False:
        errors.append("Xvfb reported fatal stderr")

    aid, bid, keycode = (raw.get("window_a_id"), raw.get("window_b_id"),
                         raw.get("keycode"))
    if not all(isinstance(x, int) for x in (aid, bid, keycode)) or aid == bid:
        errors.append("window/keycode identity invalid")
        return errors
    samples = raw.get("samples")
    if not isinstance(samples, list):
        errors.append("samples is not a list")
        return errors
    wanted = {
        "stable_focus_positive_control": ["pre_down", "post_down", "post_up"],
        "focus_transfer_while_key_down": ["pre_down", "post_down_a_focused",
                                          "still_down_b_focused", "post_up_b_focused"],
    }
    by_key = {(row.get("scenario"), row.get("label")): row for row in samples}
    if len(by_key) != len(samples):
        errors.append("duplicate sample key")
    for scenario, labels in wanted.items():
        if [label for (name, label) in by_key if name == scenario] != labels:
            errors.append(f"sample order/coverage mismatch for {scenario}")
            continue
        for label in labels:
            row = by_key[(scenario, label)]
            if row.get("keycode") != keycode:
                errors.append(f"sample keycode mismatch at {scenario}/{label}")
            if row.get("focus_window_id") != row.get("expected_focus_window_id"):
                errors.append(f"sample focus mismatch at {scenario}/{label}")
            try:
                decoded = key_bit(row)
                if decoded is not row.get("key_down"):
                    errors.append(f"bitmap/key_down mismatch at {scenario}/{label}")
            except (ValueError, KeyError, TypeError):
                errors.append(f"invalid full bitmap at {scenario}/{label}")

    expected_states = {
        ("stable_focus_positive_control", "pre_down"): False,
        ("stable_focus_positive_control", "post_down"): True,
        ("stable_focus_positive_control", "post_up"): False,
        ("focus_transfer_while_key_down", "pre_down"): False,
        ("focus_transfer_while_key_down", "post_down_a_focused"): True,
        ("focus_transfer_while_key_down", "still_down_b_focused"): True,
        ("focus_transfer_while_key_down", "post_up_b_focused"): False,
    }
    for key, expected in expected_states.items():
        row = by_key.get(key)
        if row is not None and row.get("key_down") is not expected:
            errors.append(f"unexpected global key state at {key[0]}/{key[1]}")
    b_focus = by_key.get(("focus_transfer_while_key_down", "still_down_b_focused"))
    if b_focus and b_focus.get("focus_window_id") != bid:
        errors.append("focus transfer did not reach B")

    events = raw.get("application_events")
    if not isinstance(events, list):
        errors.append("application_events is not a list")
        return errors
    # Core X11 event codes: KeyPress=2, KeyRelease=3.
    def has_event(scenario, typ, window):
        return any(e.get("scenario") == scenario and e.get("type") == typ
                   and e.get("window_id") == window and e.get("detail") == keycode
                   for e in events)

    if not has_event("stable_focus_positive_control", 2, aid):
        errors.append("positive-control A did not receive W KeyPress")
    if not has_event("stable_focus_positive_control", 3, aid):
        errors.append("positive-control A did not receive W KeyRelease")
    if not has_event("focus_transfer_while_key_down", 2, aid):
        errors.append("transfer scenario A did not receive W KeyPress before focus shift")
    b_press_events = [e for e in events
                      if e.get("scenario") == "focus_transfer_while_key_down"
                      and e.get("type") == 2 and e.get("window_id") == bid
                      and e.get("detail") == keycode]
    if b_press_events or raw.get("b_keypress_count_while_down") != 0:
        errors.append("B received W KeyPress while the global key remained down")
    if raw.get("event_checks", {}).get("a_positive_keypress") is not True:
        errors.append("positive-control event receipt flag is false")
    if raw.get("event_checks", {}).get("a_positive_keyrelease") is not True:
        errors.append("positive-control release receipt flag is false")
    if raw.get("event_checks", {}).get("a_transfer_keypress") is not True:
        errors.append("transfer A press receipt flag is false")
    if raw.get("samples"):
        times = [row.get("observed_ns") for row in samples]
        if any(not isinstance(t, int) for t in times) or times != sorted(times):
            errors.append("keymap sample monotonic order invalid")
    actions = raw.get("actions")
    if not isinstance(actions, list) or len(actions) != 7:
        errors.append("expected seven recorded focus/key actions")
    else:
        if [row.get("ordinal") for row in actions] != list(range(1, 8)):
            errors.append("action ordinal sequence mismatch")
        expected_actions = [
            ("stable_focus_positive_control", "set_focus", None),
            ("stable_focus_positive_control", "fake_key", 2),
            ("stable_focus_positive_control", "fake_key", 3),
            ("focus_transfer_while_key_down", "set_focus", None),
            ("focus_transfer_while_key_down", "fake_key", 2),
            ("focus_transfer_while_key_down", "set_focus", None),
            ("focus_transfer_while_key_down", "fake_key", 3),
        ]
        observed_actions = [(row.get("scenario"), row.get("action"),
                             row.get("event_type")) for row in actions]
        if observed_actions != expected_actions:
            errors.append("frozen focus/key action sequence mismatch")
        action_times = [row.get("started_ns") for row in actions]
        if any(not isinstance(t, int) for t in action_times) or action_times != sorted(action_times):
            errors.append("action monotonic order invalid")
        if any(not isinstance(row.get("sync_returned_ns"), int)
               or row["sync_returned_ns"] < row.get("started_ns", 0)
               for row in actions):
            errors.append("action sync-return timestamp invalid")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default="/tmp/formal-01-raw.json")
    parser.add_argument("--out", default="/tmp/formal-01-audit.json")
    args = parser.parse_args()
    fixture_bytes = FIXTURE_PATH.read_bytes()
    fixture = json.loads(fixture_bytes)
    freeze = json.loads(FREEZE_PATH.read_bytes())
    raw_bytes = Path(args.raw).read_bytes()
    raw = json.loads(raw_bytes)
    errors = validate(raw, fixture, freeze)
    controls = {}
    mutations = {
        "wrong_window_focus": lambda value: value["samples"][5].update(
            focus_window_id=value["window_a_id"]),
        "missing_global_down_sample": lambda value: value["samples"].pop(5),
        "invented_b_keypress": lambda value: value["application_events"].append({
            "scenario": "focus_transfer_while_key_down", "type": 2,
            "detail": value["keycode"], "window_id": value["window_b_id"]}),
        "missing_key_release_sample": lambda value: value["samples"].pop(2),
        "bad_bitmap": lambda value: value["samples"][5].update(bitmap_hex="00"),
    }
    for name, mutate in mutations.items():
        changed = copy.deepcopy(raw)
        mutate(changed)
        controls[name] = len(validate(changed, fixture, freeze)) > 0
    mutation_rejections = sum(controls.values())
    verdict = ("PASS_X11_APP_DELIVERY_BOUNDARY_SCOPED"
               if not errors and mutation_rejections == len(mutations)
               else "FAIL_AUDIT")
    result = {
        "schema": "issue59-x11-app-delivery-audit-v1",
        "allocation_id": fixture["allocation_id"],
        "auditor_invocations": 1,
        "retries": 0,
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "candidate_sha256": raw.get("candidate_sha256"),
        "verdict": verdict,
        "errors": errors,
        "positive_control_a_received_press_release": (
            has_event_from_result(raw, "stable_focus_positive_control", 2,
                                  raw.get("window_a_id"), raw.get("keycode")) and
            has_event_from_result(raw, "stable_focus_positive_control", 3,
                                  raw.get("window_a_id"), raw.get("keycode"))),
        "focus_transfer_global_down": (
            next((s.get("key_down") for s in raw.get("samples", [])
                  if s.get("scenario") == "focus_transfer_while_key_down"
                  and s.get("label") == "still_down_b_focused"), None)),
        "focus_transfer_b_keypress_count": raw.get("b_keypress_count_while_down"),
        "mutations_rejected": mutation_rejections,
        "mutation_count": len(mutations),
        "mutation_controls": controls,
    }
    Path(args.out).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                              encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


def has_event_from_result(raw, scenario, typ, window, keycode):
    return any(e.get("scenario") == scenario and e.get("type") == typ
               and e.get("window_id") == window and e.get("detail") == keycode
               for e in raw.get("application_events", []))


if __name__ == "__main__":
    main()
