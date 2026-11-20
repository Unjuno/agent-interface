"""Inject adverse terminal receipts into V40 cancellation helpers."""
import importlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOOM = HERE.parent
PINNED = DOOM / "v16_visual_controller_59_4d74_20261004" / "source" / "research"
sys.path[:0] = [str(DOOM), str(PINNED / "doom"), str(PINNED / "live_control"),
                str(PINNED / "observation_gating")]
controller = importlib.import_module("map01_overlap_controller_v40")


class Process:
    def __init__(self):
        self.stdin = io.StringIO()


class Planner:
    def __init__(self):
        self.interrupted = []

    def interrupt(self, handle):
        self.interrupted.append(handle)
        return {"turn_id": handle, "interrupted": True}


BAD_TERMINALS = {
    "completed_instead_of_cancelled": {"status": "completed", "release": {
        "verified": True, "keys_down": [], "buttons_down": []}},
    "unverified_release": {"status": "cancelled", "release": {
        "verified": False, "keys_down": [], "buttons_down": []}},
    "key_still_down": {"status": "cancelled", "release": {
        "verified": True, "keys_down": ["d"], "buttons_down": []}},
    "button_still_down": {"status": "cancelled", "release": {
        "verified": True, "keys_down": [], "buttons_down": ["left"]}},
    "release_missing": {"status": "cancelled"},
}


def run_case(helper_name, case_name, terminal):
    identifier = "cover-t3"
    process = Process()
    planner = Planner()

    def wait(predicate, timeout=40):
        event = {"event": "terminal", "id": identifier, **terminal}
        if not predicate(event):
            raise AssertionError("terminal did not match requested cover")
        return event

    try:
        if helper_name == "initial":
            controller.cancel_unplanned_invalidated_cover(process, wait, identifier)
        else:
            controller.cancel_invalidated_cover(
                planner, "turn-t3", process, wait, identifier)
    except RuntimeError as exc:
        disposition = "rejected"
        error = str(exc)
    else:
        disposition = "accepted"
        error = None
    command = json.loads(process.stdin.getvalue())
    expected_error = ("invalidated cover before planning did not verify empty release"
                      if helper_name == "initial" else
                      "invalidated cover did not verify empty release")
    return {
        "helper": helper_name,
        "case": case_name,
        "disposition": disposition,
        "error": error,
        "cancel_command": command,
        "planner_interrupts": planner.interrupted,
        "expected_error": expected_error,
    }


def main():
    rows = []
    valid = {"status": "cancelled", "release": {
        "verified": True, "keys_down": [], "buttons_down": []}}
    for helper in ("initial", "renewal"):
        rows.append(run_case(helper, "valid_empty_release", valid))
        for name, terminal in BAD_TERMINALS.items():
            rows.append(run_case(helper, name, terminal))
    result = {
        "schema": "v40-release-receipt-fault-injection-v1",
        "scope": "host-side cancellation helper construction only",
        "cases": rows,
    }
    out = HERE / "experiment-result.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    rejected = sum(row["disposition"] == "rejected" for row in rows)
    print(f"cases={len(rows)} rejected={rejected} accepted={len(rows)-rejected}")
    print(f"result={out.name}")
    if rejected != 10 or len(rows) != 12:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
