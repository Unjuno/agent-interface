"""Versioned completeness supplement, using retained raw only.

The first audit validates invariants but lacks exact reachability/completion
controls. This explicit finite oracle prevents always-stop from passing.
"""
import argparse
import hashlib
import json
from pathlib import Path

from audit import audit as invariant_audit

PRE_EXECUTION = {"initial", "observe:1", "admit:1", "journal.observation_recorded:1", "journal.branch_selected:1"}
ONE_PENDING = {"execute:1", "journal.action_terminal:1"}
ONE_VERIFIED = {"observe:2", "admit:2", "verify:1", "journal.observation_recorded:2", "journal.branch_selected:2", "journal.effect_checked:1"}
TWO_PENDING = {"execute:2"}
FINISHED = {"never", "observe:3", "verify:2", "journal.branch_selected:3"}


def audit(rows, pins):
    result = invariant_audit(rows, pins)
    errors = list(result["errors"])
    for index, row in enumerate(rows):
        schedule, terminal, receipt = row.get("schedule"), row.get("terminal"), row.get("receipt")
        if type(receipt) is not dict:
            continue
        if schedule in PRE_EXECUTION:
            executions, completed, verified = 0, 0, 0
            outcome, reason = "SAFE_YIELD", "cancelled"
        elif terminal != "completed":
            executions, completed, verified = 1, 0, 0
            outcome, reason = {"release_failed": ("RUNTIME_FAILED", "execution_failed"),
                               "delivery_uncertain": ("SAFE_YIELD", "delivery_uncertain"),
                               "refused_no_input": ("SAFE_YIELD", "execution_refused")}[terminal]
        elif schedule in ONE_PENDING:
            executions, completed, verified = 1, 1, 0
            outcome, reason = "SAFE_YIELD", "cancelled"
        elif schedule in ONE_VERIFIED:
            executions, completed, verified = 1, 1, 1
            outcome, reason = "SAFE_YIELD", "cancelled"
        elif schedule in TWO_PENDING:
            executions, completed, verified = 2, 2, 1
            outcome, reason = "SAFE_YIELD", "cancelled"
        elif schedule in FINISHED:
            executions, completed, verified = 2, 2, 2
            outcome, reason = "TASK_SUCCEEDED", "method_complete"
        else:
            errors.append({"row": index, "errors": ["unmodeled_schedule"]})
            continue
        trace = row["trace"]
        observed_exec = sum(event.get("event") == "callback_entry" and event.get("stage") == "execute" for event in trace)
        observed_verify = sum(event.get("event") == "verify_return" for event in trace)
        if (observed_exec, receipt.get("completed_transitions"), observed_verify,
                receipt.get("outcome"), receipt.get("reason")) != (executions, completed, verified, outcome, reason):
            errors.append({"row": index, "errors": ["finite_reachability_or_terminal"],
                           "expected": [executions, completed, verified, outcome, reason]})
    result["errors"] = errors
    result["audit_version"] = "v2-reachability"
    result["disposition"] = "PASS_FINITE_CANCELLATION_SCOPED" if not errors else "FAIL_FINITE_CANCELLATION"
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    base = Path(__file__).parent
    pins = {label: hashlib.sha256((base / "sources" / (label + ".py")).read_bytes()).hexdigest()
            for label in ("main", "pr6863")}
    result = audit([json.loads(line) for line in args.raw.read_text().splitlines()], pins)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(bool(result["errors"]))


if __name__ == "__main__":
    main()
