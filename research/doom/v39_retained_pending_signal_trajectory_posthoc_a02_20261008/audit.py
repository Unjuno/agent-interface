"""Independent structural and hash audit of the retained signal reconstruction."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from analyze import reconstruct


def audit(root: Path, result_path: Path) -> dict:
    actual = json.loads(result_path.read_text(encoding="utf-8"))
    expected = reconstruct(root)
    if actual != expected:
        raise ValueError("candidate result does not match independent reconstruction")
    if len(actual["decision_windows"]) != 6:
        raise ValueError("expected six decision windows")
    if not actual["typed_artifact_reconciliation_passed"] or actual["observation_count"] != 218:
        raise ValueError("typed observation/artifact reconciliation failed")
    if len(actual["authored_threshold_events"]) < 2:
        raise ValueError("expected the retained authored-policy threshold crossings")
    if not actual["authored_loss_guard_events"]:
        raise ValueError("expected the authored maximum-loss guard breach")
    if actual["recorded_policy_invalidations"] != 1:
        raise ValueError("unexpected retained invalidation count")
    if not actual.get("limitations"):
        raise ValueError("required limitations missing")
    return {
        "schema": "v39-retained-pending-signal-trajectory-audit-v1",
        "status": "PASS_RECONSTRUCTION",
        "checks_passed": 7,
        "checks_total": 7,
        "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).parent)
    parser.add_argument("--result", type=Path, default=Path(__file__).parent / "RESULT.json")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "AUDIT.json")
    args = parser.parse_args()
    args.output.write_text(json.dumps(audit(args.root, args.result), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
