"""Post-formal corrected scoring wrapper; v1 evidence and source stay immutable."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit import audit as audit_v1


def audit(root: Path) -> dict:
    result = audit_v1(root)
    # A valid but inaccurate localization is a scored miss, not an integrity fault.
    # Keep HOLD for malformed boxes and all other v1 integrity/GPU errors.
    rows = {row["case_id"]: row for row in result["rows"]}
    retained = []
    for error in result["errors"]:
        if not error.startswith("positive_box_invalid:"):
            retained.append(error)
            continue
        case_id = error.split(":", 1)[1]
        box = rows.get(case_id, {}).get("response", {}).get("box")
        valid_box = (isinstance(box, list) and len(box) == 4
                     and all(type(value) is int for value in box)
                     and box[0] >= 0 and box[1] >= 0
                     and box[2] > box[0] and box[3] > box[1])
        if not valid_box:
            retained.append(f"positive_box_malformed:{case_id}")
    result["errors"] = retained
    result["schema"] = "visual-encoding-570-local-r4-audit-v2-postformal"
    result["correction"] = "Valid positive boxes below IoU 0.5 count as localization misses, not integrity errors."
    complete = result["formal_complete"]
    positives = result["positive_hits"]
    absent = result["absent_abstentions"]
    result["decision"] = (
        "PASS_DIAGNOSTIC_SCOPED" if complete and not retained and positives >= 5 and absent == 2
        else "FAIL_EASY_LAYOUT_CAPABILITY_NOT_ESTABLISHED" if complete and not retained and positives < 5
        else "HOLD_AUDIT_OR_GPU_GATE"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    text = json.dumps(audit(args.root), indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()

