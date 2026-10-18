"""Independent source and result audit for the ammo-to-cancellation composition."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def validate(result):
    for name, spec in FREEZE["sources"].items():
        data = subprocess.check_output(["git", "show", f"{FREEZE['main_commit']}:{spec['path']}"])
        blob = subprocess.check_output(["git", "rev-parse", f"{FREEZE['main_commit']}:{spec['path']}"], text=True).strip()
        if hashlib.sha256(data).hexdigest() != spec["sha256"] or blob != spec["git_blob"]:
            raise ValueError(f"frozen source mismatch: {name}")
    expected_top = {"schema": "issue59-v39-ammo-cancel-composition-result-v1",
                    "status": "CONSTRUCTION_OBSERVATION",
                    "main_commit": FREEZE["main_commit"],
                    "scope": "Synthetic paired HUD and fake transport composition only; no live timing, key state, tactical policy, or task effect."}
    if set(result) != set(expected_top) | {"cases"}:
        raise ValueError("top-level fields differ")
    for key, value in expected_top.items():
        if result.get(key) != value:
            raise ValueError(f"top-level mismatch: {key}")
    if len(result["cases"]) != 3:
        raise ValueError("expected three composition cases")
    for row in result["cases"]:
        events = [item["event"] for item in row["events"]]
        if row["source_ammo"] != 50 or row["ammo_hard_minimum"] != 1 or row["health"] != 100:
            raise ValueError("source or guard boundary changed")
        if row["case"] == "positive-floor-soft-control":
            if (row["ammo"] != 1 or row["disposition"] != "soft_change" or
                    row["invalidation_reason"] is not None or row["answer_eligible"] is not True or
                    row["answer"] != {"action": "stale"} or row["cancellation_requested"] is not False or
                    any(event in events for event in ("executor_cancel_write", "planner_interrupt_transport", "cover_terminal"))):
                raise ValueError("positive floor must preserve the pending answer without cancellation")
            continue
        if row["ammo"] != 0 or row["disposition"] != "hard_invalidation" or row["invalidation_reason"] != "ammo:below_hard_minimum":
            raise ValueError("zero-ammo invalidation boundary mismatch")
        if (row["answer_eligible"] is not False or row["answer"] is not None or
                row["cancellation_requested"] is not True):
            raise ValueError("invalidated answer was admitted")
        expected_order = ["monitor_disposition", "executor_cancel_write",
                          "planner_interrupt_transport", "cover_terminal",
                          "answer_arrived", "answer_classified"]
        if any(event not in events for event in expected_order):
            raise ValueError("hard case lacks a required event")
        positions = [events.index(event) for event in expected_order]
        if positions != sorted(positions):
            raise ValueError("monitor/cancel/interrupt/terminal/answer order mismatch")
        terminal = row["terminal"]
        if terminal != {"event": "terminal", "id": "cover-1", "status": "cancelled",
                        "release": {"verified": True, "keys_down": [], "buttons_down": []}}:
            raise ValueError("terminal must verify cancelled empty release")
        if row["case"] == "zero-ammo-cancel-first":
            if row["cancel_fails"] is not False or row["helper_error"] is not None:
                raise ValueError("ordinary hard case unexpectedly failed")
            if not (events.index("cover_terminal") < events.index("helper_returned") < events.index("answer_arrived")):
                raise ValueError("helper must return after terminal and before answer")
        elif row["case"] == "zero-ammo-cancel-write-failure":
            if row["cancel_fails"] is not True or not row["helper_error"] or "cancel write failed" not in row["helper_error"]:
                raise ValueError("cancel-write failure not retained")
            if not (events.index("planner_interrupt_transport") < events.index("cover_terminal") <
                    events.index("helper_error") < events.index("answer_arrived")):
                raise ValueError("failure must still interrupt, verify terminal, and remain an error")
        else:
            raise ValueError("unexpected case")
    return True


def main():
    result_path = HERE / "RESULT.json"
    output_path = HERE / "AUDIT.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    validate(result)
    if output_path.exists():
        raise SystemExit(f"refusing to overwrite {output_path}")
    audit = {"schema": "issue59-v39-ammo-cancel-composition-audit-v1",
             "status": "PASS_CONSTRUCTION_COMPOSITION",
             "checks": {"frozen_sources_match": True,
                        "positive_floor_preserves_pending_answer": True,
                        "zero_ammo_invalidates_pending_answer": True,
                        "executor_cancel_precedes_planner_interrupt": True,
                        "cancelled_terminal_verifies_empty_release": True,
                        "cancel_write_failure_still_interrupts_and_surfaces": True},
             "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest()}
    output_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, separators=(",", ":")))


if __name__ == "__main__":
    main()
