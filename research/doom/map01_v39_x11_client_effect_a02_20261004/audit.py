"""Independent raw-only auditor for the A02 focused-client effect."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(raw: dict, freeze: dict) -> list[str]:
    errors: list[str] = []
    if raw.get("schema") != "v39-x11-client-effect-a02-v1":
        errors.append("schema mismatch")
    if raw.get("source_sha256") != freeze.get("input_owner_v10_sha256"):
        errors.append("source hash mismatch")
    if raw.get("xvfb_running_before_stop") is not True:
        errors.append("Xvfb not live before cleanup")
    if raw.get("xvfb_returncode_after_stop") not in (0, -15):
        errors.append("missing Xvfb stop receipt")
    if raw.get("cleanup_errors") != []:
        errors.append("candidate cleanup error")
    if raw.get("app_counter_final") != 2:
        errors.append("final client counter is not two")
    cycles = raw.get("cycles")
    if not isinstance(cycles, list) or len(cycles) != 2:
        errors.append("expected exactly two cycles")
        return errors
    ids = [c.get("occurrence_id") for c in cycles if isinstance(c, dict)]
    if len(ids) != 2 or any(not isinstance(x, str) or not x for x in ids) or len(set(ids)) != 2:
        errors.append("occurrence IDs missing or duplicated")
    keycode = raw.get("keycode")
    window_id = raw.get("window_id")
    owner_id = cycles[0].get("owner_id") if cycles and isinstance(cycles[0], dict) else None
    if type(keycode) is not int or not 0 <= keycode < 256:
        errors.append("invalid keycode")
        return errors
    if type(window_id) is not int or window_id <= 1:
        errors.append("invalid focused client window")
    if not isinstance(owner_id, str) or not owner_id:
        errors.append("owner identity missing")
    initial = raw.get("initial_owner_state")
    if (not isinstance(initial, dict) or initial.get("owner_id") != owner_id
            or initial.get("focus") != window_id or initial.get("owned_keycodes") != []):
        errors.append("initial owner focus or empty-state mismatch")

    for index, cycle in enumerate(cycles):
        if not isinstance(cycle, dict):
            errors.append("cycle is not an object")
            continue
        occurrence = cycle.get("occurrence_id")
        if cycle.get("key") != "w" or cycle.get("keycode") != keycode:
            errors.append(f"{occurrence}: key identity mismatch")
        if cycle.get("owner_id") != owner_id:
            errors.append(f"{occurrence}: owner identity mismatch")
        if cycle.get("intent_token") != "a02:" + str(occurrence):
            errors.append(f"{occurrence}: intent mismatch")

        for name, expected_down in (("pre_down", False), ("post_down", True), ("post_up", False)):
            sample = cycle.get(name)
            if not isinstance(sample, dict):
                errors.append(f"{occurrence}: {name} missing")
                continue
            try:
                bitmap = bytes.fromhex(sample["bitmap_hex"])
                observed = bool(bitmap[keycode // 8] & (1 << (keycode % 8)))
            except (KeyError, TypeError, ValueError, IndexError):
                errors.append(f"{occurrence}: {name} malformed keymap")
                continue
            if (sample.get("bitmap_length") != 32 or len(bitmap) != 32
                    or sample.get("keycode") != keycode
                    or sample.get("key_down") is not expected_down
                    or observed is not expected_down
                    or sample.get("source") != "independent Xlib Display.query_keymap"
                    or sample.get("physical_key_up_claimed") is not False):
                errors.append(f"{occurrence}: {name} keymap mismatch")
            start, finish = sample.get("sample_started_ns"), sample.get("sample_finished_ns")
            if type(start) is not int or type(finish) is not int or start > finish:
                errors.append(f"{occurrence}: {name} sample interval invalid")

        admission = cycle.get("admission")
        if not isinstance(admission, dict) or admission.get("event") != "input_admission":
            errors.append(f"{occurrence}: input admission missing")
            continue
        press = cycle.get("client_keypress")
        release = cycle.get("client_keyrelease")
        if not isinstance(press, dict) or not isinstance(release, dict):
            errors.append(f"{occurrence}: client events missing")
            continue
        for label, event, expected_type in (("keypress", press, 2), ("keyrelease", release, 3)):
            if (event.get("event_type") != expected_type or event.get("keycode") != keycode
                    or event.get("window_id") != window_id or event.get("send_event") is not False
                    or type(event.get("received_ns")) is not int):
                errors.append(f"{occurrence}: client {label} identity mismatch")

        before = cycle.get("pre_down", {}).get("sample_finished_ns")
        down = cycle.get("post_down", {}).get("sample_started_ns")
        after_down = cycle.get("post_down", {}).get("sample_finished_ns")
        press_ns = press.get("received_ns")
        up_start = cycle.get("up_started_ns")
        release_call_start = cycle.get("up_returned_ns")
        release_call_finish = cycle.get("owner_release_returned_ns")
        post_up = cycle.get("post_up", {}).get("sample_started_ns")
        down_start = cycle.get("down_started_ns")
        admitted = admission.get("admitted_ns")
        ack = admission.get("input_ack_ns")
        down_return = cycle.get("down_returned_ns")
        if not all(type(x) is int for x in (before, down, after_down, press_ns, up_start,
                release_call_start, release_call_finish, post_up, down_start,
                admitted, ack, down_return)):
            errors.append(f"{occurrence}: operation chronology missing")
        elif not (before <= down_start <= admitted <= ack <= down_return <= down
                <= after_down <= press_ns <= up_start <= release_call_start
                <= release_call_finish <= release.get("received_ns") <= post_up):
            errors.append(f"{occurrence}: operation and client event chronology invalid")

        for phase, expected_keys in (("owner_after_down", [keycode]), ("owner_after_up", [])):
            state = cycle.get(phase)
            if (not isinstance(state, dict) or state.get("owner_id") != owner_id
                    or state.get("owned_keycodes") != expected_keys):
                errors.append(f"{occurrence}: {phase} owner state mismatch")
        if cycle.get("app_counter_after_press") != index + 1:
            errors.append(f"{occurrence}: client counter did not increment once")
        if cycle.get("up_result") is not None:
            errors.append(f"{occurrence}: v10 up did not return None")
        receipt = cycle.get("owner_release_result")
        if (not isinstance(receipt, dict) or receipt.get("event") != "owner_release"
                or receipt.get("verified") is not True or receipt.get("keys_down") != []
                or receipt.get("buttons_down") != []):
            errors.append(f"{occurrence}: explicit owner release not verified empty")

    terminal = [row for row in raw.get("owner_records", [])
                if isinstance(row, dict) and row.get("event") == "owner_release"]
    if (len(terminal) != 3 or terminal[-1].get("reason") != "close"
            or any(row.get("verified") is not True or row.get("keys_down") != []
                   or row.get("buttons_down") != [] for row in terminal)):
        errors.append("expected two empty explicit releases and one verified close")
    return errors


def audit(raw_path: Path, freeze_path: Path = HERE / "FREEZE.json") -> dict:
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = validate(raw, freeze)
    for relative, expected in freeze.get("artifact_sha256", {}).items():
        path = HERE / relative
        if not path.is_file() or digest(path) != expected:
            errors.append("frozen artifact mismatch: " + relative)
    return {
        "schema": "v39-x11-client-effect-audit-a02-v1",
        "raw_sha256": digest(raw_path),
        "source_sha256": raw.get("source_sha256"),
        "checks_failed": len(errors),
        "errors": errors,
        "status": "PASS_X11_CLIENT_EVENT_AND_COUNTER_EFFECT" if not errors else "FAIL_AUDIT",
        "scope": "focused minimal Xlib client only; no game or production GUI",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.raw)
    if args.out.exists():
        raise FileExistsError(args.out)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"audit_exit": 0 if not result["errors"] else 1,
                      "status": result["status"], "checks_failed": result["checks_failed"]},
                     sort_keys=True))
    raise SystemExit(0 if not result["errors"] else 1)
