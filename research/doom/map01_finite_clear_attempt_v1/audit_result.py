"""Independent conservative audit for the finite MAP01 baseline."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("root", type=Path); args = ap.parse_args()
    rows = json.loads((args.root / "controller-events.json").read_text())
    allocation = json.loads((args.root / "allocation.json").read_text())
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
        "controller_scope": "fixed bounded OS-input baseline; no model call",
        "claims_excluded": ["model competence", "general gameplay", "human speed", "token efficiency"],
    }
    (args.root / "audit-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if outcome != "HOLD_INFRASTRUCTURE" else 2

if __name__ == "__main__":
    raise SystemExit(main())
