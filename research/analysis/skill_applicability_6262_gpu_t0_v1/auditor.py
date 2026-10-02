"""Independent pure-Python audit; intentionally imports no candidate code."""
import copy
import hashlib
import itertools
import json
import sys
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def expected(fixture):
    factors = list(fixture["factors"].items())
    names = [k for k, _ in factors]
    feasible = []
    for values in itertools.product(*(v for _, v in factors)):
        row = dict(zip(names, values))
        if row["mode"] == "dialog" and row["target"] == "alternate":
            continue
        feasible.append(row)
    trials = fixture["trials"]
    if len(trials) != len(feasible) or len({t["id"] for t in trials}) != len(trials):
        raise ValueError("offered-trial denominator or trial identity mismatch")
    for cell in feasible:
        if sum(all(t[n] == cell[n] for n in names) for t in trials) != 1:
            raise ValueError("feasible-cell trial mapping is not one-to-one")
    outcome = {}
    for t in trials:
        outcome[t["id"]] = (
            "FAIL" if t["effect"] == "FAIL" else
            "UNKNOWN" if t["effect"] != "PASS" or t["route_qualified"] is not True else
            "PASS"
        )
    projections = []
    for (left, _), (right, _) in itertools.combinations(factors, 2):
        keys = sorted({(c[left], c[right]) for c in feasible})
        projections.extend((left, lv, right, rv) for lv, rv in keys)
    rows = []
    for mask in range(1 << len(trials)):
        selected = [t for i, t in enumerate(trials) if mask & (1 << i)]
        selected_ids = {t["id"] for t in selected}
        passed = sum(outcome[t["id"]] == "PASS" for t in selected)
        flat = bool(selected) and passed / len(selected) >= fixture["flat_success_threshold"]
        factorwise = all(
            any(t[name] == level and outcome[t["id"]] == "PASS" for t in selected)
            for name, values in factors for level in values
        )
        missing, bad = [], []
        for left, lv, right, rv in projections:
            group = [t for t in selected if t[left] == lv and t[right] == rv]
            label = [left, lv, right, rv]
            if not group:
                missing.append(label)
            elif any(outcome[t["id"]] != "PASS" for t in group):
                bad.append(label)
        narrow_trial = fixture["narrow_claim_trial"]
        narrow = narrow_trial in selected_ids and outcome[narrow_trial] == "PASS"
        rows.append({
            "mask": mask,
            "observed": len(selected),
            "passed": passed,
            "flat_promotes": flat,
            "factorwise_promotes": factorwise,
            "wide_certificate_passes": not missing and not bad,
            "narrow_certificate_passes": narrow,
            "missing_pair_projections": missing,
            "nonpass_pair_projections": bad,
        })
    return {
        "experiment_id": fixture["experiment_id"],
        "fixture_sha256": hashlib.sha256(Path(sys.argv[1]).with_name("FIXTURE.json").read_bytes()).hexdigest(),
        "trial_count": len(trials),
        "feasible_cell_count": len(feasible),
        "feasible_pair_projection_count": len(projections),
        "effective_trial_outcomes": outcome,
        "all_subsets": rows,
    }


def verify(raw, fixture):
    exp = expected(fixture)
    for key, value in exp.items():
        if raw.get(key) != value:
            raise AssertionError(f"candidate mismatch at {key}")
    if raw.get("enumerated_evidence_subsets") != (1 << exp["trial_count"]):
        raise AssertionError("incomplete evidence-subset enumeration")
    return exp


def main():
    fixture = load(Path(sys.argv[1]).with_name("FIXTURE.json"))
    raw_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(sys.argv[1]).with_name("CANDIDATE_RAW.json")
    raw = load(raw_path)
    exp = verify(raw, fixture)
    controls = []

    # M1: fabricate PASS coverage for the structurally impossible dialog/alternate pair.
    m1 = copy.deepcopy(raw)
    m1["all_subsets"][-1]["wide_certificate_passes"] = True
    try:
        verify(m1, fixture)
        controls.append({"name": "fabricated_infeasible_edge", "rejected": False})
    except AssertionError:
        controls.append({"name": "fabricated_infeasible_edge", "rejected": True})

    # M2: silently hide one offered trial from the denominator.
    f2 = copy.deepcopy(fixture)
    f2["trials"].pop()
    try:
        verify(raw, f2)
        controls.append({"name": "hidden_offered_trial", "rejected": False})
    except (AssertionError, ValueError):
        controls.append({"name": "hidden_offered_trial", "rejected": True})

    # M3: treat authority grant as route qualification for t11.
    f3 = copy.deepcopy(fixture)
    next(t for t in f3["trials"] if t["id"] == "t11")["route_qualified"] = True
    try:
        verify(raw, f3)
        controls.append({"name": "grant_as_capability", "rejected": False})
    except AssertionError:
        controls.append({"name": "grant_as_capability", "rejected": True})

    # M4: promote an exact narrow claim when its supporting trial is absent.
    m4 = copy.deepcopy(raw)
    m4["all_subsets"][0]["narrow_certificate_passes"] = True
    try:
        verify(m4, fixture)
        controls.append({"name": "unsupported_narrow_promotion", "rejected": False})
    except AssertionError:
        controls.append({"name": "unsupported_narrow_promotion", "rejected": True})

    if not all(c["rejected"] for c in controls):
        raise AssertionError("one or more frozen mutations were accepted")
    both_naive = [r for r in exp["all_subsets"] if r["flat_promotes"] and r["factorwise_promotes"] and not r["wide_certificate_passes"]]
    exact = next(t for t in fixture["trials"] if t["id"] == fixture["narrow_claim_trial"])
    report = {
        "experiment_id": fixture["experiment_id"],
        "audit_disposition": "PASS_METHOD_SCOPED" if len(exp["all_subsets"]) == 4096 and controls else "FAIL_AUDIT",
        "candidate_exact_match": True,
        "subsets_independently_reconstructed": len(exp["all_subsets"]),
        "naive_joint_false_promotions": len(both_naive),
        "all_trials_flat_pass_fraction": sum(v == "PASS" for v in exp["effective_trial_outcomes"].values()) / len(fixture["trials"]),
        "wide_claim_full_ledger_passes": exp["all_subsets"][-1]["wide_certificate_passes"],
        "narrow_claim_t01_is_qualified_pass": exact["route_qualified"] and exact["effect"] == "PASS",
        "mutations": controls,
        "limitations": [
            "Constructed synthetic truth fixture only; no real reusable skill or GUI was tested.",
            "The chosen infeasibility constraint is stipulated by the fixture and not empirically validated.",
            "Two-way coverage does not establish higher-order or history-sensitive applicability.",
            "The result does not establish the value, cost, or performance of GPU computation."
        ]
    }
    Path(sys.argv[1]).with_name("AUDIT_RAW.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
