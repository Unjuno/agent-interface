"""One-shot candidate for the finite same-cohort negative-control T0."""
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def sha(path):
    raw = path.read_bytes()
    if not raw.endswith(b"\r\n"):
        raw += b"\r\n"
    return hashlib.sha256(raw).hexdigest()


def source_sha():
    supplied = os.environ.get("CANDIDATE_SOURCE")
    if supplied is None:
        return sha(ROOT / "candidate.py")
    actual = hashlib.sha256(supplied.encode("utf-8")).hexdigest()
    expected = os.environ.get("FROZEN_CANDIDATE_SHA256")
    if expected and expected != actual:
        raise RuntimeError("candidate source environment hash mismatch")
    return actual


def mean(values):
    return sum(values) / len(values) if values else None


def summarize(case, rows, refs):
    routes = {r: [x for x in rows if x["route"] == r] for r in ("direct", "guarded")}
    pmeans = {r: mean([x["primary_observed"] for x in group if x["primary_observed"] is not None]) for r, group in routes.items()}
    contrast = None if any(v is None for v in pmeans.values()) else pmeans["guarded"] - pmeans["direct"]
    primary = {"route_means": pmeans, "guarded_minus_direct": contrast, "effect_signal": bool(contrast is not None and contrast != 0)}

    reference_failures = [x for x in refs if x["observed"] != x["expected"]]
    reference = {"checks": len(refs), "failed": len(reference_failures), "alert": bool(reference_failures)}

    missing = {r: sum(not x["outcome_record_present"] for x in group) for r, group in routes.items()}
    rates = {r: missing[r] / len(routes[r]) for r in routes}
    id_mismatches = sum(x["assigned_task_id"] != x["observed_task_id"] for x in rows)
    delta_rates = {}
    for route, group in routes.items():
        deltas = [x["sentinel_after_observed"] - x["sentinel_before_observed"] for x in group]
        delta_rates[route] = mean(deltas)
    sentinel_contrast = delta_rates["guarded"] - delta_rates["direct"]
    reasons = []
    if id_mismatches:
        reasons.append("TASK_ID_OR_JOIN_MISMATCH")
    if rates["direct"] != rates["guarded"]:
        reasons.append("ROUTE_DIFFERENTIAL_MISSINGNESS")
    if sentinel_contrast != 0:
        reasons.append("SAME_COHORT_SENTINEL_CONTRAST")
    cohort = {
        "missing_by_route": missing,
        "missing_rate_by_route": rates,
        "id_mismatch_rows": id_mismatches,
        "sentinel_change_rate_by_route": delta_rates,
        "sentinel_change_contrast": sentinel_contrast,
        "reason_codes": reasons,
        "gate": "NEEDS_INDEPENDENT_AUDIT" if reasons else "CLEAR",
    }
    return {"kind": "summary", "case": case, "primary_only": primary, "pre_post_reference_deck": reference, "same_cohort_control": cohort}


def main():
    rows = load("reported_rows.json")
    refs = load("reference_deck.json")
    freeze = load("FREEZE.json")
    print(json.dumps({"kind": "run", "freeze_id": freeze["freeze_id"], "candidate_sha256": source_sha(), "reported_rows_sha256": sha(ROOT / "reported_rows.json"), "reference_deck_sha256": sha(ROOT / "reference_deck.json")}, sort_keys=True))
    for row in rows:
        print(json.dumps(row, sort_keys=True))
    for ref in refs:
        print(json.dumps(ref, sort_keys=True))
    for case in freeze["case_order"]:
        print(json.dumps(summarize(case, [x for x in rows if x["case"] == case], [x for x in refs if x["case"] == case]), sort_keys=True))


if __name__ == "__main__":
    main()

