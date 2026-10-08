"""Independent source and raw-event auditor for the completed-future race probe."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
CASE_NAMES = {"positive-floor-soft-control", "zero-ammo-completed-future"}


def _repo_root():
    for parent in HERE.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("repository root not found")


def validate_result(result, events):
    for name, spec in FREEZE["sources"].items():
        data = subprocess.check_output(["git", "-C", str(_repo_root()), "show",
                                        f"{FREEZE['main_commit']}:{spec['path']}"])
        blob = subprocess.check_output(["git", "-C", str(_repo_root()), "rev-parse",
                                        f"{FREEZE['main_commit']}:{spec['path']}"], text=True).strip()
        if blob != spec["git_blob"] or hashlib.sha256(data).hexdigest() != spec["sha256"]:
            raise ValueError(f"frozen source identity mismatch: {name}")
    if not isinstance(result, dict) or set(result) != {
            "schema", "status", "main_commit", "main_order_lines", "cases", "scope"}:
        raise ValueError("result field set mismatch")
    if (result["schema"] != "issue59-v39-ammo-completed-future-drain-result-a08-v1" or
            result["status"] != "CONSTRUCTION_OBSERVATION" or
            result["main_commit"] != FREEZE["main_commit"] or
            result["scope"] != "Frozen current-main queue-drain, paired monitor, planner adapter, and final-admission composition with synthetic observations and deterministic fakes only."):
        raise ValueError("result identity or scope mismatch")
    positions = result["main_order_lines"]
    if (set(positions) != {"drain", "planner_result", "final_admission"} or
            not positions["drain"] < positions["planner_result"] < positions["final_admission"]):
        raise ValueError("main source-order claim mismatch")
    cases = result["cases"]
    if not isinstance(cases, list) or {c.get("case") for c in cases} != CASE_NAMES or len(cases) != 2:
        raise ValueError("case set must contain each expected case exactly once")
    if not isinstance(events, list):
        raise ValueError("raw events must be a list")
    flattened = []
    for case in cases:
        name = case["case"]
        flattened.extend({"case": name, **event} for event in case["events"])
        expected_ammo = 1 if name == "positive-floor-soft-control" else 0
        expected_disposition = "soft_change" if expected_ammo else "hard_invalidation"
        expected_reason = None if expected_ammo else "ammo:below_hard_minimum"
        expected_admission = "READY_FOR_ACTION_VALIDITY" if expected_ammo else "REJECTED_POLICY_INVALIDATED"
        if (case.get("source_health") != 100 or case.get("current_health") != 100 or
                case.get("source_ammo") != 50 or case.get("current_ammo") != expected_ammo or
                case.get("ammo_hard_minimum") != 1 or
                case.get("planner_future_done_before_drain") is not True or
                case.get("planner_status") != "completed" or
                case.get("planner_answer_eligible") is not True or
                case.get("monitor_disposition") != expected_disposition or
                case.get("invalidation_reason") != expected_reason or
                case.get("final_admission", {}).get("status") != expected_admission or
                case.get("final_admission", {}).get("input_authority_admitted") is not False or
                case.get("final_admission", {}).get("grants_input_authority") is not False or
                case.get("incoming_empty_after_drain") is not True):
            raise ValueError(f"case outcome mismatch: {name}")
        terminal = case.get("terminal")
        if (terminal != {"event": "terminal", "id": "cover-a08", "status": "completed",
                         "release": {"verified": True, "keys_down": [], "buttons_down": []}}):
            raise ValueError(f"terminal release mismatch: {name}")
        kinds = [row.get("event") for row in case["events"]]
        required = ["planner_future_completed", "future_done_checked", "actual_monitor_received",
                    "actual_monitor_disposition", "completed_terminal_validated",
                    "completed_answer_read", "final_admission"]
        indexes = []
        for event in required:
            if kinds.count(event) != 1:
                raise ValueError(f"{name}: expected exactly one {event}")
            indexes.append(kinds.index(event))
        if indexes != sorted(indexes):
            raise ValueError(f"event order mismatch: {name}")
        future = case["events"][kinds.index("actual_monitor_received")]
        monitor = case["events"][kinds.index("actual_monitor_disposition")]
        terminal_event = case["events"][kinds.index("completed_terminal_validated")]
        if future.get("future_done") is not True or terminal_event.get("verified_empty") is not True:
            raise ValueError(f"completed-future / empty-terminal evidence mismatch: {name}")
        if (monitor.get("reason") != expected_reason or
                monitor.get("requires_new_decision") is not bool(expected_ammo == 0) or
                monitor.get("grants_input_authority") is not False):
            raise ValueError(f"monitor disposition evidence mismatch: {name}")
    if flattened != events:
        raise ValueError("raw event stream differs from embedded case events")
    return True


def main():
    result_path, events_path = HERE / "RESULT.json", HERE / "events.jsonl"
    audit_path = HERE / "AUDIT.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    validate_result(result, events)
    if audit_path.exists():
        raise FileExistsError(f"refusing to overwrite {audit_path}")
    audit = {"schema": "issue59-v39-ammo-completed-future-drain-audit-a08-v1",
             "status": "PASS_CONSTRUCTION_RACE", "frozen_main": FREEZE["main_commit"],
             "case_count": len(result["cases"]), "event_rows": len(events),
             "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
             "events_sha256": hashlib.sha256(events_path.read_bytes()).hexdigest(),
             "checks": {"frozen_sources_verified": True, "unique_expected_cases": True,
                        "raw_events_bound_to_embedded_events": True,
                        "completed_future_drained_before_result_and_admission": True,
                        "positive_floor_remains_action_validity_only": True,
                        "zero_ammo_policy_rejected_without_input_authority": True,
                        "both_terminals_verified_empty": True}}
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, separators=(",", ":")))


if __name__ == "__main__":
    main()
