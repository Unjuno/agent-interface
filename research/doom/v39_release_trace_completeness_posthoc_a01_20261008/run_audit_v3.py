"""Run the versioned independent full-result check; never rerun the allocation."""
import argparse
import hashlib
import json
from pathlib import Path

try:
    from .audit_result_v3 import (
        FREEZE_BLOB, FREEZE_COMMIT, FREEZE_SHA256, load_pinned_inputs,
        validate_result,
    )
except ImportError:
    from audit_result_v3 import (
        FREEZE_BLOB, FREEZE_COMMIT, FREEZE_SHA256, load_pinned_inputs,
        validate_result,
    )


HERE = Path(__file__).resolve().parent


def audit(result_path, output_path):
    result_path = Path(result_path)
    output_path = Path(output_path)
    if not result_path.is_absolute():
        result_path = HERE / result_path
    if not output_path.is_absolute():
        output_path = HERE / output_path
    freeze, events, owner_events, report, prior, prereg = load_pinned_inputs()
    result_bytes = result_path.read_bytes()
    result = json.loads(result_bytes)
    validate_result(result, events, owner_events, report, prior, prereg, freeze)
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite {output_path}")
    output = {
        "schema": "map01-v39-release-trace-completeness-audit-v3",
        "status": "PASS_FULL_RESULT_AND_PROVENANCE_BOUND_TO_RAW",
        "freeze": {
            "commit": FREEZE_COMMIT,
            "git_blob": FREEZE_BLOB,
            "sha256": FREEZE_SHA256,
        },
        "frozen_main": freeze["frozen_main"],
        "allocation_id": freeze["allocation_id"],
        "preregistration_allocation_id": prereg["allocation_id"],
        "raw_inputs_verified": freeze["inputs"],
        "event_rows_verified": len(events),
        "owner_rows_verified": len(owner_events),
        "result_sha256": hashlib.sha256(result_bytes).hexdigest(),
        "checks": {
            "all_result_fields_recomputed": True,
            "all_cancel_rows_bound_to_raw": True,
            "cancel_terminal_release_chronology": True,
            "prior_audit_provenance_bound": True,
            "per_key_field_names_match_v12_receipts": True,
            "unsupported_feedback_claim_remains_false": True,
        },
    }
    output_path.write_text(json.dumps(output, indent=2) + "\n",
                           encoding="utf-8", newline="\n")
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, default=HERE / "RESULT.json")
    parser.add_argument("--output", type=Path, default=HERE / "AUDIT_V3.json")
    args = parser.parse_args()
    print(json.dumps(audit(args.result, args.output), separators=(",", ":")))


if __name__ == "__main__":
    main()
