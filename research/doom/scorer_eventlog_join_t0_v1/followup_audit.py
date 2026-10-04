"""Independent raw-only audit of the prior-policy regression output."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def audit():
    raw = json.loads((ROOT / "followup_raw.json").read_text(encoding="utf-8"))
    errors = []
    expected = {
        "schema": "scorer-eventlog-prior-policy-regression-raw-v1",
        "base_main": "b47d4d0b053f6e7d88c37e24be81777aa28feb6a",
        "prior_candidate_git_blob": "3a097172115b6d8c2cd482c37c80388b86404b25",
        "prior_candidate_sha256": "fecf7be7abe7a36111ec2df171461eb225d5c951b37c8d979d0a2ce2d0e7f4b9",
        "successor_candidate_sha256": "23727e925c3e27a171592b0a831ab29572647bc0309cb6f10b8d81c8104aa049",
        "prior_decision": "ADMISSION_BRACKETED_PROGRESS",
        "prior_baseline_ns": 105,
        "pre_input_progress_observed_ns": 115,
        "first_input_ns": 120,
        "unchanged_post_input_sample_ns": 130,
        "successor_decision": "POST_CANCELLATION_COOCCURRENCE",
        "successor_reason": "no_bounded_post_input_progress",
        "candidate_started_in_container": False,
    }
    for field, value in expected.items():
        if raw.get(field) != value:
            errors.append(f"{field}:expected={value!r}:actual={raw.get(field)!r}")
    if raw.get("causal_attribution") is not False:
        errors.append("causal_attribution")
    return {"schema": "scorer-eventlog-prior-policy-regression-audit-v1",
            "pass": not errors, "errors": errors,
            "claim_scope": "exact-source offline policy regression only"}


if __name__ == "__main__":
    result = audit()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (ROOT / "followup_audit.json").write_text(text, encoding="utf-8")
    print(text, end="")
    raise SystemExit(0 if result["pass"] else 1)
