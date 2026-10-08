"""Independent conservative audit for the finite MAP01 baseline."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("root", type=Path); args = ap.parse_args()
    events_path = args.root / "controller-events.json"
    allocation_path = args.root / "allocation.json"
    if not events_path.is_file() or not allocation_path.is_file():
        result = {
            "allocation_id": "map01-finite-clear-attempt-v1",
            "outcome": "HOLD_INFRASTRUCTURE",
            "reason": "allocation did not produce the required raw event/allocation files",
        }
        (args.root / "audit-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, sort_keys=True))
        return 2
    rows = json.loads(events_path.read_text())
    allocation = json.loads(allocation_path.read_text())
    terminals = [r for r in rows if r.get("event") == "terminal"]
    scores = [r for r in rows if r.get("event") == "post_control_score"]
    malformed = [r for r in rows if r.get("event") == "malformed_stdout"]
    # The baseline cannot establish a clear from hidden state. Only an explicit
    # controller-visible exit receipt can pass; otherwise retain a conservative
    # no-exit or infrastructure outcome.
    exit_receipts = [r for r in rows if r.get("event") in {"map_exit", "exit"} and r.get("status") == "verified"]
    if allocation.get("process_returncode") != 0 or not scores:
        outcome = "HOLD_INFRASTRUCTURE"
    elif exit_receipts:
        outcome = "PASS_FINITE_CLEAR_SCOPED"
    else:
        outcome = "FAIL_FINITE_CLEAR_NO_EXIT"
    result = {
        "allocation_id": "map01-finite-clear-attempt-v1",
        "outcome": outcome,
        "event_count": len(rows),
        "terminal_count": len(terminals),
        "score_receipt_count": len(scores),
        "malformed_stdout_count": len(malformed),
        "runner_failure": allocation.get("failure"),
        "session_stderr_present": bool(allocation.get("session_stderr")),
        "controller_scope": "fixed bounded OS-input baseline; no model call",
        "claims_excluded": ["model competence", "general gameplay", "human speed", "token efficiency"],
    }
    (args.root / "audit-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if outcome != "HOLD_INFRASTRUCTURE" else 2

if __name__ == "__main__":
    raise SystemExit(main())
