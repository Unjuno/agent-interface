"""Raw-only auditor for A03 event routing and client state changes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check_sample(row, stage, keycode, down, occurrence, errors):
    if not isinstance(row, dict):
        errors.append(f"{stage}: missing sample")
        return
    if row.get("stage") != stage or row.get("keycode") != keycode:
        errors.append(f"{stage}: identity mismatch")
    if row.get("physical_key_up_claimed") is not False:
        errors.append(f"{stage}: physical input claim")
    if row.get("source") != "independent Xlib Display.query_keymap":
        errors.append(f"{stage}: observer source mismatch")
    try:
        bitmap = bytes.fromhex(row["bitmap_hex"])
        bit = bool(bitmap[keycode // 8] & (1 << (keycode % 8)))
        if len(bitmap) != 32 or row.get("bitmap_length") != 32 or bit is not down or row.get("key_down") is not down:
            errors.append(f"{stage}: keymap bit mismatch")
    except (KeyError, TypeError, ValueError, IndexError):
        errors.append(f"{stage}: malformed keymap")
    start, finish = row.get("sample_started_ns"), row.get("sample_finished_ns")
    if type(start) is not int or type(finish) is not int or start > finish:
        errors.append(f"{stage}: invalid sample interval")


def _events(route, keycode, window_id, errors, label):
    down = route.get("client_events_after_down")
    up = route.get("client_events_after_up")
    if not isinstance(down, list) or not isinstance(up, list):
        errors.append(f"{label}: client event lists missing")
        return None, None
    all_events = down + up
    if len(all_events) != 2:
        errors.append(f"{label}: expected exactly two received key events")
    presses = [e for e in down if isinstance(e, dict) and e.get("event_type") == 2
               and e.get("keycode") == keycode and e.get("window_id") == window_id]
    releases = [e for e in up if isinstance(e, dict) and e.get("event_type") == 3
                and e.get("keycode") == keycode and e.get("window_id") == window_id]
    if len(presses) != 1 or len(releases) != 1:
        errors.append(f"{label}: matching client press/release not observed exactly once")
        return None, None
    for event in all_events:
        if (not isinstance(event, dict) or event.get("target_match") is not True
                or event.get("send_event") is not False or type(event.get("received_ns")) is not int):
            errors.append(f"{label}: unexpected or synthetic client key event")
    return presses[0], releases[0]


def validate(raw: dict, freeze: dict) -> list[str]:
    errors: list[str] = []
    if raw.get("schema") != "v39-x11-event-routing-a03-v1":
        errors.append("schema mismatch")
    if raw.get("candidate_invocations") != 1 or raw.get("candidate_complete") is not True or raw.get("failure") is not None:
        errors.append("candidate did not complete exactly once")
    if raw.get("source_sha256") != freeze.get("input_owner_v10_sha256"):
        errors.append("InputOwner v10 source mismatch")
    if raw.get("xvfb_running_before_stop") is not True or raw.get("xvfb_returncode_after_stop") not in (0, -15):
        errors.append("Xvfb cleanup receipt invalid")
    if raw.get("cleanup_errors") != []:
        errors.append("cleanup errors present")
    code, window = raw.get("keycode"), raw.get("window_id")
    if type(code) is not int or not 0 <= code < 256 or type(window) is not int or window <= 1:
        errors.append("focused client identity invalid")
        return errors
    if raw.get("focus_id") != window:
        errors.append("candidate did not retain matching focused window")
    routes = raw.get("routes")
    if not isinstance(routes, dict) or set(routes) != {"direct_xtest", "input_owner_v10"}:
        errors.append("route pair missing")
        return errors
    prior_counter = 0
    for name in ("direct_xtest", "input_owner_v10"):
        route = routes[name]
        label = name
        if not isinstance(route, dict) or not route.get("occurrence_id"):
            errors.append(f"{label}: route identity missing")
            continue
        if route.get("counter_before") != prior_counter:
            errors.append(f"{label}: starting counter mismatch")
        _check_sample(route.get("pre_down"), "pre_down", code, False, route["occurrence_id"], errors)
        _check_sample(route.get("post_down"), "post_down", code, True, route["occurrence_id"], errors)
        _check_sample(route.get("post_up"), "post_up", code, False, route["occurrence_id"], errors)
        press, release = _events(route, code, window, errors, label)
        if route.get("counter_after_down") != prior_counter + 1 or route.get("counter_after_up") != prior_counter + 1:
            errors.append(f"{label}: client counter did not increment exactly once")
        if press is not None and release is not None:
            bounds = (route["pre_down"]["sample_finished_ns"], route.get("down_started_ns"),
                      route.get("down_returned_ns"), route["post_down"]["sample_started_ns"],
                      route["post_down"]["sample_finished_ns"], press["received_ns"],
                      route.get("up_started_ns"), route.get("up_returned_ns"),
                      release["received_ns"], route["post_up"]["sample_started_ns"])
            if not all(type(v) is int for v in bounds) or sorted(bounds) != list(bounds):
                errors.append(f"{label}: down/event/up chronology invalid")
        if name == "direct_xtest":
            if route.get("method") != "direct XTEST control":
                errors.append("direct route method mismatch")
        else:
            if route.get("method") != "InputOwner v10":
                errors.append("owner route method mismatch")
            owner_id = route.get("owner_id")
            admission = route.get("admission")
            if not isinstance(owner_id, str) or not owner_id:
                errors.append("owner route identity missing")
            if (not isinstance(admission, dict) or admission.get("event") != "input_admission"
                    or admission.get("key") != "w"):
                errors.append("owner admission missing")
            elif not (route["down_started_ns"] <= admission.get("admitted_ns", -1)
                      <= admission.get("input_ack_ns", -1) <= route["down_returned_ns"]):
                errors.append("owner admission chronology invalid")
            for phase, held in (("owner_after_down", [code]), ("owner_after_up", [])):
                state = route.get(phase)
                if not isinstance(state, dict) or state.get("owner_id") != owner_id or state.get("owned_keycodes") != held:
                    errors.append(f"{phase}: owner-held state mismatch")
            receipt = route.get("release_result")
            if (not isinstance(receipt, dict) or receipt.get("event") != "owner_release"
                    or receipt.get("verified") is not True or receipt.get("keys_down") != []
                    or receipt.get("buttons_down") != []):
                errors.append("explicit owner release not verified empty")
            if route.get("up_result") is not None:
                errors.append("v10 up result mismatch")
            release_returned = route.get("release_returned_ns")
            if (type(release_returned) is not int or release is None
                    or release.get("received_ns", -1) < release_returned):
                errors.append("owner release/client event chronology invalid")
            records = [r for r in raw.get("owner_records", [])
                       if isinstance(r, dict) and r.get("event") == "owner_release"]
            if len(records) != 2 or records[-1].get("reason") != "close" or any(
                r.get("verified") is not True or r.get("keys_down") != [] or r.get("buttons_down") != []
                for r in records):
                errors.append("owner release/close record sequence invalid")
        prior_counter += 1
    if raw.get("app_counter_final") != 2:
        errors.append("final app counter mismatch")
    return errors


def audit(raw_path: Path, freeze_path: Path = HERE / "FREEZE.json") -> dict:
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = validate(raw, freeze)
    for relative, expected in freeze.get("artifact_sha256", {}).items():
        path = HERE / relative
        if not path.is_file() or digest(path) != expected:
            errors.append("frozen artifact mismatch: " + relative)
    return {"schema": "v39-x11-event-routing-audit-a03-v1",
            "raw_sha256": digest(raw_path), "errors": errors,
            "status": "PASS_EVENT_ROUTING_CONTROL" if not errors else "FAIL_AUDIT",
            "scope": "two Xvfb client routing methods and minimal counter only"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.raw)
    if args.out.exists():
        raise FileExistsError(args.out)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"audit_exit": 0 if not report["errors"] else 1,
                      "status": report["status"], "error_count": len(report["errors"])}, sort_keys=True))
    raise SystemExit(0 if not report["errors"] else 1)
