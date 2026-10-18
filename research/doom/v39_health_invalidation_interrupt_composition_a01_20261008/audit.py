"""Independent source and event-order oracle for the retained composition result."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def verify_sources():
    for name, spec in FREEZE["sources"].items():
        data = subprocess.check_output(["git", "show", f"{FREEZE['main_commit']}:{spec['path']}"])
        blob = subprocess.check_output(["git", "rev-parse", f"{FREEZE['main_commit']}:{spec['path']}"], text=True).strip()
        if hashlib.sha256(data).hexdigest() != spec["sha256"] or blob != spec["git_blob"]:
            raise ValueError(f"source provenance mismatch: {name}")


def validate(result):
    verify_sources()
    if set(result) != {"schema", "status", "main_commit", "pending_model", "cases", "scope"}:
        raise ValueError("result field set mismatch")
    if (result["schema"] != "issue59-health-invalidation-interrupt-composition-result-v1" or
            result["status"] != "CONSTRUCTION_OBSERVATION" or
            result["main_commit"] != FREEZE["main_commit"] or result["pending_model"] is not True or
            result["scope"] != "Synthetic typed HUD and fake transport composition only; no live timing, key state, task effect, or recovery efficacy."):
        raise ValueError("result identity/scope mismatch")
    if len(result["cases"]) != 3:
        raise ValueError("expected three composition cases")
    expected = {
        "hard-crossing-cancel-first": (12, 84, 88, "health:below_hard_minimum"),
        "soft-change-preserves-cover": (16, 84, 84, None),
        "hard-crossing-cancel-write-failure": (12, 84, 88, "health:below_hard_minimum"),
    }
    for row in result["cases"]:
        if row["case"] not in expected:
            raise ValueError("unexpected case")
        loss, health, floor, invalidation = expected[row["case"]]
        if (row["maximum_health_loss"], row["health"], row["hard_minimum"], row["invalidation"]) != (loss, health, floor, invalidation):
            raise ValueError(f"monitor boundary mismatch: {row['case']}")
        events = [item["event"] for item in row["events"]]
        if row["case"] == "soft-change-preserves-cover":
            if row["answer_eligible"] is not True or row["answer"] != {"action": "stale"}:
                raise ValueError("soft change should preserve pending answer eligibility")
            if any(kind in events for kind in ("executor_cancel_write", "planner_interrupt_transport", "cover_terminal")):
                raise ValueError("soft change unexpectedly cancelled or interrupted")
            continue
        expected_order = ["monitor_disposition", "executor_cancel_write",
                          "planner_interrupt_transport", "cover_terminal",
                          "answer_arrived", "answer_classified"]
        if any(kind not in events for kind in expected_order):
            raise ValueError("hard-crossing trace is missing an ordered event")
        positions = [events.index(kind) for kind in expected_order]
        if positions != sorted(positions):
            raise ValueError("monitor/cancel/interrupt/terminal/answer order mismatch")
        terminal = row["terminal"]
        if (terminal != {"event": "terminal", "id": "cover-1", "status": "cancelled",
                         "release": {"verified": True, "keys_down": [], "buttons_down": []}}):
            raise ValueError("terminal must confirm empty release")
        if row["answer_eligible"] is not False or row["answer"] is not None:
            raise ValueError("invalidated pending answer was admitted")
        if row["case"] == "hard-crossing-cancel-first":
            if row["cancel_fails"] is not False or row["helper_error"] is not None:
                raise ValueError("successful cancel case unexpectedly errored")
            if not (events.index("cover_terminal") < events.index("helper_returned") <
                    events.index("answer_arrived")):
                raise ValueError("successful helper return must follow terminal and precede answer")
        else:
            if row["cancel_fails"] is not True or not row["helper_error"] or "cancel write failed" not in row["helper_error"]:
                raise ValueError("cancel-write failure was not retained as an error")
            if "planner_interrupt_transport" not in events:
                raise ValueError("planner interrupt was not attempted after local cancel failure")
            if not (events.index("cover_terminal") < events.index("helper_error") <
                    events.index("answer_arrived")):
                raise ValueError("cancel failure must be retained after terminal and before answer")
    return True


def main():
    result_path = HERE / "RESULT.json"
    output_path = HERE / "AUDIT_V3.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    validate(result)
    if output_path.exists():
        raise SystemExit(f"refusing to overwrite {output_path}")
    audit = {"schema": "issue59-health-invalidation-interrupt-composition-audit-v3",
             "status": "PASS_CONSTRUCTION_COMPOSITION",
             "checks": {"frozen_source_identities": True,
                        "hard_health_crossing_reaches_current_cancel_helper": True,
                        "monitor_cancel_interrupt_terminal_answer_order": True,
                        "empty_terminal_required_and_retained": True,
                        "invalidated_answer_rejected_after_completion": True,
                        "soft_change_does_not_interrupt": True,
                        "cancel_failure_preserved_after_interrupt_attempt": True},
             "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest()}
    output_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, separators=(",", ":")))


if __name__ == "__main__":
    main()
