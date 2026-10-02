"""Independent raw-only audit for the Issue #5518 synthetic probe."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


EXPECTED = {
    "conforming_hidden_batch_retry": (True, None),
    "target_mutation": (False, 1),
    "stale_unauthorized": (False, 2),
    "semantic_failure_reported_success": (False, 3),
    "delayed_explicit_unknown": (True, None),
    "silent_missing_output": (False, 1),
}


def verify(document: dict) -> list[str]:
    errors: list[str] = []
    if document.get("study") != "issue-5518-ioco-t0-v1":
        errors.append("study_identity")
    if document.get("alphabet_version") != "frozen-v1":
        errors.append("alphabet_identity")
    if document.get("quiescence_policy") != "explicit UNKNOWN is allowed where listed; missing output is forbidden":
        errors.append("quiescence_policy")
    results = document.get("results")
    if not isinstance(results, list):
        return errors + ["results_not_list"]
    by_name = {r.get("scenario"): r for r in results if isinstance(r, dict)}
    if set(by_name) != set(EXPECTED):
        errors.append("scenario_inventory")
    for name, (accepted, prefix) in EXPECTED.items():
        row = by_name.get(name)
        if row is None:
            continue
        if row.get("accepted") is not accepted or row.get("expected_accepted") is not accepted or row.get("match") is not True:
            errors.append(name + ":verdict")
        ce = row.get("counterexample")
        if prefix is None and ce is not None:
            errors.append(name + ":unexpected_counterexample")
        elif prefix is not None and (not isinstance(ce, dict) or ce.get("prefix_length") != prefix):
            errors.append(name + ":counterexample_prefix")
        if row.get("internal_hidden_transitions") != ["BATCH", "RETRY"]:
            errors.append(name + ":hidden_transition_fixture")
        if name == "delayed_explicit_unknown" and row.get("terminal_state") != "UNKNOWN":
            errors.append(name + ":unknown_state")
    return errors


def main() -> int:
    source = Path(os.environ["RESULT_PATH"]).open(encoding="utf-8") if os.environ.get("RESULT_PATH") else sys.stdin
    document = json.load(source)
    errors = verify(document)
    print(json.dumps({"auditor": "independent-raw-only-v1", "checks": 3 + 3 * len(EXPECTED), "errors": errors}, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

