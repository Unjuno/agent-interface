from __future__ import annotations
import copy, json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent

def audit(row):
    errors = []
    def check(ok, label):
        if not ok: errors.append(label)
    transition = row.get("up_transition")
    events = row.get("fake_keyrelease", [])
    owner_id = row.get("owner_thread_id")
    cancel_ns = row.get("cancel_set_ns")
    dequeue_ns = row.get("queue_dequeue_ns")
    check(row.get("candidate_exit") == 0, "candidate exit")
    check(isinstance(transition, dict), "up transition present")
    check(len(events) == 1 and events[0].get("event") == "KeyRelease", "one keyrelease")
    check(type(cancel_ns) is int and type(dequeue_ns) is int and dequeue_ns <= cancel_ns,
          "cancel after queue dequeue")
    if isinstance(transition, dict):
        check(transition.get("cancel_requested_at_request") is False, "caller sampled uncancelled")
        check(transition.get("ordinary_release_candidate") is True, "ordinary candidate")
        check(transition.get("owner_thread_keyup_verified") is True, "owner receipt verified")
        check(transition.get("owner_thread_keyup_history_complete") is True, "history complete")
        check(transition.get("owner_thread_keyup_receipt_count") == 1, "one receipt joined")
        receipt = transition.get("owner_thread_keyup_receipt")
        check(isinstance(receipt, dict) and receipt.get("event") == "owner_explicit_keyup",
              "explicit owner keyup receipt")
    else:
        receipt = None
    check(len(events) == 1 and events[0].get("cancel_set_at_side_effect") is True,
          "cancel visible at keyrelease side effect")
    if events:
        check(type(cancel_ns) is int and cancel_ns < events[0].get("side_effect_ns", 0),
              "cancel precedes side effect")
    samples = [s for s in row.get("cancel_samples", [])
               if s.get("thread_id") == owner_id and s.get("value") is False
               and type(s.get("sample_ns")) is int]
    check(bool(samples) and type(cancel_ns) is int and max(s["sample_ns"] for s in samples) < cancel_ns,
          "owner sampled false before cancel")
    check(row.get("keycode_30_down_after_up") is False, "fake keymap empty")
    state = row.get("owner_state_after_up")
    check(isinstance(state, dict) and state.get("owned_keycodes") == [], "owner state empty")
    history = row.get("owner_records_after_close", [])
    keyups = [r for r in history if isinstance(r, dict) and r.get("event") == "owner_explicit_keyup"]
    check(len(keyups) == 1 and receipt == keyups[0], "one exact history receipt")
    check(row.get("owner_thread_stopped") is True, "owner thread stopped")
    return errors

result = json.loads((ROOT / "RESULT.json").read_text())
errors = audit(result)
mutations = {}
for name, change in {
    "cancel_after_keyrelease": lambda x: x["cancel_samples"].append({"thread_id": x["owner_thread_id"], "value": False, "sample_ns": x["fake_keyrelease"][0]["side_effect_ns"] + 1}),
    "ordinary_not_credited": lambda x: x["up_transition"].update(ordinary_release_candidate=False),
    "receipt_removed": lambda x: x["up_transition"].update(owner_thread_keyup_receipt=None),
}.items():
    copy_row = copy.deepcopy(result); change(copy_row); mutations[name] = bool(audit(copy_row))
if not all(mutations.values()): errors.append("negative control escaped")
summary = {"scope": "single deterministic fake-Xlib queue/cancellation ordering check",
           "errors": errors, "passed": not errors, "negative_controls_rejected": mutations,
           "classification": "REPRODUCED" if not errors else "NOT_REPRODUCED_OR_STOP"}
(ROOT / "AUDIT.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary))
raise SystemExit(bool(errors))
