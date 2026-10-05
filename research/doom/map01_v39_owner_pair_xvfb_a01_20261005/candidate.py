"""One-shot Xvfb shared-display test for two V39 V12-backed input owners."""
from __future__ import annotations

import argparse
import json
import os
import threading
import time
import uuid
from pathlib import Path

from Xlib import XK, display
from input_transition_owner_v4 import InputOwner


class Lease:
    def __init__(self, expected_focus: int, label: str):
        self.intent_token = "owner-pair-a01-" + label
        self.deadline = time.perf_counter_ns() + 10_000_000_000
        self.cancel = threading.Event()
        self.expected_focus = expected_focus
        self.focus_invalid = False

    def check(self):
        if time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("test lease expired")


def observe(observer, keycode, stage):
    started = time.perf_counter_ns()
    bitmap = observer.query_keymap()
    finished = time.perf_counter_ns()
    if len(bitmap) != 32:
        raise RuntimeError("XQueryKeymap returned a non-32-byte bitmap")
    return {
        "stage": stage,
        "started_ns": started,
        "finished_ns": finished,
        "bitmap_hex": bitmap.hex(),
        "keycode": keycode,
        "key_down": bool(bitmap[keycode // 8] & (1 << (keycode % 8))),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--display", default=":99")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    os.environ["DISPLAY"] = args.display
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)

    observer = display.Display(args.display)
    focus = observer.get_input_focus().focus
    focus_id = focus.id if hasattr(focus, "id") else int(focus)
    keycode = observer.keysym_to_keycode(XK.string_to_keysym("W"))
    if not keycode:
        raise RuntimeError("Xvfb has no keycode for W")

    raw = {
        "schema": "v39-owner-pair-xvfb-a01-raw-v1",
        "run_id": uuid.uuid4().hex,
        "display": args.display,
        "key": "W",
        "keycode": keycode,
        "focus_id": focus_id,
        "source_pr_head": "1627581fddb84521e87942cca49ed40310683f65",
        "base_main": "6860b585305e539ec93896f5adcbf658cbbd8592",
        "scope": "Xvfb server keymap and local input-owner bookkeeping only",
    }
    owners = []
    cleanup_errors = []
    try:
        single = InputOwner(args.display)
        owners.append(single)
        single_lease = Lease(focus_id, "single")
        raw["single_owner_id"] = single.owner_id
        raw["control_samples"] = [observe(observer, keycode, "control_before")]
        single.call("down", single_lease, "W")
        raw["control_samples"].append(observe(observer, keycode, "control_after_down"))
        raw["control_up_receipt"] = single.call("up", single_lease, "W")
        raw["control_samples"].append(observe(observer, keycode, "control_after_up"))
        raw["control_state_after_up"] = single.call("input_state")
        single.close()
        owners.remove(single)

        owner_a = InputOwner(args.display)
        owner_b = InputOwner(args.display)
        owners.extend([owner_a, owner_b])
        lease_a = Lease(focus_id, "A")
        lease_b = Lease(focus_id, "B")
        raw["owner_ids"] = {"A": owner_a.owner_id, "B": owner_b.owner_id}
        raw["intent_tokens"] = {"A": lease_a.intent_token, "B": lease_b.intent_token}
        raw["pair_samples"] = [observe(observer, keycode, "pair_before")]
        raw["A_down"] = owner_a.call("down", lease_a, "W")
        raw["pair_samples"].append(observe(observer, keycode, "after_A_down"))
        raw["B_down"] = owner_b.call("down", lease_b, "W")
        raw["pair_samples"].append(observe(observer, keycode, "after_B_down"))
        raw["A_up_receipt"] = owner_a.call("up", lease_a, "W")
        raw["pair_samples"].append(observe(observer, keycode, "after_A_up"))
        raw["B_state_after_A_up"] = owner_b.call("input_state")
        raw["B_up_receipt"] = owner_b.call("up", lease_b, "W")
        raw["pair_samples"].append(observe(observer, keycode, "after_B_up"))
        raw["B_state_after_B_up"] = owner_b.call("input_state")
        raw["owner_records"] = {"A": owner_a.records, "B": owner_b.records}
    finally:
        for owner in reversed(owners):
            try:
                owner.close()
            except Exception as exc:  # preserve a cleanup failure in raw
                cleanup_errors.append(repr(exc))
        try:
            raw["final_sample"] = observe(observer, keycode, "final")
        except Exception as exc:
            cleanup_errors.append("final sample: " + repr(exc))
        raw["cleanup_errors"] = cleanup_errors
        observer.close()
        (out / "raw.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")

    if cleanup_errors:
        return 2
    if not raw.get("A_up_receipt", {}).get("owner_thread_keyup_verified"):
        return 3
    if raw.get("B_state_after_A_up", {}).get("owned_keycodes") != [keycode]:
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
