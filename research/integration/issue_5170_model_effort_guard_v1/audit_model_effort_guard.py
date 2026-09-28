"""Independent standard-library audit of model/effort identity in a trace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def audit(trace: dict) -> dict:
    identities = []
    errors = []
    preflights = trace.get("preflight_calls")
    arms = trace.get("arms")
    if type(preflights) is not dict or type(arms) is not dict:
        return {"decision": "HOLD_SCHEMA", "errors": ["missing arm/preflight maps"]}
    for arm in ("plain", "ephemeral", "persistent"):
        preflight = preflights.get(arm)
        rows = arms.get(arm)
        if type(preflight) is not dict or type(rows) is not list:
            errors.append(f"missing arm records: {arm}")
            continue
        identities.append((arm, "preflight", preflight.get("requested_model"),
                           preflight.get("requested_effort")))
        for task_index, row in enumerate(rows):
            calls = row.get("model_calls") if type(row) is dict else None
            if type(calls) is not list:
                errors.append(f"malformed task calls: {arm}/{task_index}")
                continue
            for call_index, call in enumerate(calls):
                if type(call) is not dict:
                    errors.append(f"malformed model call: {arm}/{task_index}/{call_index}")
                    continue
                identities.append((arm, f"task:{task_index}:{call_index}",
                                   call.get("requested_model"),
                                   call.get("requested_effort")))
    distinct = {(model, effort) for _, _, model, effort in identities}
    if any(type(model) is not str or not model or type(effort) is not str or not effort
           for _, _, model, effort in identities):
        errors.append("missing or invalid model/effort identity")
    if len(distinct) != 1:
        errors.append("model/effort identity differs within comparison")
    return {"decision": "PASS_MATCHED_MODEL_EFFORT" if not errors else "FAIL_MODEL_EFFORT_MISMATCH",
            "identity_records": len(identities), "distinct_identities": len(distinct),
            "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.trace.read_text(encoding="utf-8")))
    print(json.dumps(result, sort_keys=True))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
