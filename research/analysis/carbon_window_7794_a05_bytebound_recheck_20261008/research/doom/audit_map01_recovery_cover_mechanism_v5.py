"""Decision-audit adapter for MAP01 bounded-recovery mechanism v5.

V5 preserves every v4 scientific threshold. The only experimental-harness change
is non-destructive event waiting in the runner. Reuse v4's reviewed audit logic
under the new one-shot allocation identity and version its output schema.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ALLOCATION_ID = "map01-recovery-cover-mechanism-live-v5-01"


def audit(root: Path) -> dict:
    import audit_map01_recovery_cover_mechanism_v4 as base
    previous = base.ALLOCATION_ID
    try:
        base.ALLOCATION_ID = ALLOCATION_ID
        result = dict(base.audit(Path(root)))
    finally:
        base.ALLOCATION_ID = previous
    result["schema"] = "map01-recovery-cover-mechanism-v5-audit"
    result["allocation_id"] = ALLOCATION_ID
    result["harness_change"] = "preserve unmatched session events during waits; scientific condition unchanged from v4"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = audit(args.root)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    return 0 if result.get("valid_experiment") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
