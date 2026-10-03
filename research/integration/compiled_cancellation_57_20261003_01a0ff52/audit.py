"""Independent raw-only checks: no runtime or candidate imports."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(rows, pins):
    stages = ["never", "initial"]
    stages += [f"observe:{i}" for i in (1, 2, 3)]
    stages += [f"{stage}:{i}" for stage in ("admit", "execute", "verify") for i in (1, 2)]
    stages += [f"journal.{stage}:{i}" for stage, values in (
        ("observation_recorded", (1, 2)), ("branch_selected", (1, 2, 3)),
        ("effect_checked", (1,)), ("action_terminal", (1,))) for i in values]
    terminals = {"completed", "delivery_uncertain", "release_failed", "refused_no_input"}
    expected = {(label, stage, terminal) for label in pins for stage in stages for terminal in terminals}
    seen, errors = set(), []
    latch_count = 0
    for index, row in enumerate(rows):
        local = []
        identity = (row.get("source"), row.get("schedule"), row.get("terminal"))
        if identity not in expected or identity in seen:
            local.append("identity_or_duplicate")
        seen.add(identity)
        if row.get("source_sha256") != pins.get(row.get("source")):
            local.append("source_pin")
        trace = row.get("trace", [])
        if [event.get("order") for event in trace] != list(range(len(trace))):
            local.append("trace_order")
        latches = [event for event in trace if event.get("event") == "cancel_latched"]
        matching = [event for event in trace if event.get("event") == "callback_entry"
                    and f"{event['stage']}:{event['occurrence']}" == row.get("schedule")]
        should_latch = row.get("schedule") == "initial" or bool(matching)
        if len(latches) != int(should_latch) or any(event.get("trigger") != row.get("schedule") for event in latches):
            local.append("latch_coverage")
        if matching and latches and latches[0]["order"] != matching[0]["order"] + 1:
            local.append("latch_position")
        if row.get("schedule") == "initial" and latches and latches[0]["order"] != 0:
            local.append("initial_latch_position")
        cutoff = latches[0]["order"] if latches else len(trace)
        latch_count += bool(latches)
        latched = False
        for event in trace:
            if event.get("event") == "cancel_latched":
                latched = True
            if event.get("event") == "cancel_checked" and event.get("value") is not latched:
                local.append("cancel_truth")
            if event.get("event") == "callback_entry" and event.get("stage") == "execute" and event["order"] > cutoff:
                local.append("post_cancel_execute")
        receipt = row.get("receipt")
        if row.get("error") is not None or type(receipt) is not dict:
            errors.append({"row": index, "errors": local + ["unexpected_runtime_error"]})
            continue
        returned = [event for event in trace if event.get("event") == "execute_return"]
        entries = [event for event in trace if event.get("event") == "callback_entry" and event.get("stage") == "execute"]
        if len(returned) != len(entries) or len(entries) > 2:
            local.append("execution_pairing_or_bound")
        complete = [event for event in returned if event["row"].get("status") == "completed"
                    and event["row"].get("release") == {"verified": True, "keys_down": [], "buttons_down": []}]
        transitions = receipt.get("transitions", [])
        if type(receipt.get("completed_transitions")) is not int or receipt["completed_transitions"] != len(complete):
            local.append("prefix_count")
        if len(transitions) != len(complete):
            local.append("transition_count")
        for transition, event in zip(transitions, complete):
            if any(transition.get(key) != event["row"].get(key) for key in ("action_id", "effect_ref")) or transition.get("action") != event["action"] or transition.get("release_verified") is not True:
                local.append("prefix_identity")
        verified = {event["action"] for event in trace if event.get("event") == "verify_return" and event["row"].get("status") == "succeeded"}
        pending = complete[-1] if complete and complete[-1]["action"] not in verified else None
        actual_pending = receipt.get("pending_effect")
        if pending is None:
            if actual_pending is not None:
                local.append("invented_pending")
        elif actual_pending != {"action": pending["action"], "effect_ref": pending["row"]["effect_ref"], "expected_effect": {"phase": len(complete)}}:
            local.append("pending_identity")
        terminal = row.get("terminal")
        if returned and terminal != "completed":
            expected_outcome, expected_reason = {
                "release_failed": ("RUNTIME_FAILED", "execution_failed"),
                "delivery_uncertain": ("SAFE_YIELD", "delivery_uncertain"),
                "refused_no_input": ("SAFE_YIELD", "execution_refused")}[terminal]
            if (receipt.get("outcome"), receipt.get("reason")) != (expected_outcome, expected_reason):
                local.append("terminal_truth")
        if receipt.get("outcome") == "TASK_SUCCEEDED" and (len(complete) != 2 or verified != {"enter", "save"}):
            local.append("premature_success")
        if local:
            errors.append({"row": index, "errors": local})
    if seen != expected:
        errors.append({"errors": ["denominator"], "missing": len(expected - seen), "extra": len(seen - expected)})
    return {"disposition": "PASS_FINITE_CANCELLATION_SCOPED" if not errors else "FAIL_FINITE_CANCELLATION",
            "rows": len(rows), "expected_rows": len(expected), "latched_rows": latch_count, "errors": errors}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("--source-dir", type=Path, default=Path(__file__).parent / "sources")
    parser.add_argument("--labels", nargs="+", default=["main", "pr6863"])
    args = parser.parse_args()
    pins = {label: hashlib.sha256((args.source_dir / (label + ".py")).read_bytes()).hexdigest() for label in args.labels}
    result = audit([json.loads(line) for line in args.raw.read_text().splitlines()], pins)
    print(json.dumps(result, sort_keys=True, indent=2))
    raise SystemExit(bool(result["errors"]))


if __name__ == "__main__":
    main()
