"""Independent raw-only replay auditor; intentionally does not import candidate.py."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read_json(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def read_raw(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"))


def avg(xs):
    return sum(xs) / len(xs) if xs else None


def replay_summary(case, episodes, refs):
    arms = {arm: [r for r in episodes if r["route"] == arm] for arm in ("direct", "guarded")}
    means = {arm: avg([r["primary_observed"] for r in data if r["primary_observed"] is not None]) for arm, data in arms.items()}
    effect = None if any(v is None for v in means.values()) else means["guarded"] - means["direct"]
    primary = {"route_means": means, "guarded_minus_direct": effect, "effect_signal": bool(effect is not None and effect != 0)}
    failed_refs = sum(r["observed"] != r["expected"] for r in refs)
    reference = {"checks": len(refs), "failed": failed_refs, "alert": bool(failed_refs)}

    missing = {arm: sum(not r["outcome_record_present"] for r in data) for arm, data in arms.items()}
    rates = {arm: missing[arm] / len(arms[arm]) for arm in arms}
    mismatch = sum(r["assigned_task_id"] != r["observed_task_id"] for r in episodes)
    changes = {arm: avg([r["sentinel_after_observed"] - r["sentinel_before_observed"] for r in data]) for arm, data in arms.items()}
    contrast = changes["guarded"] - changes["direct"]
    reasons = []
    if mismatch:
        reasons.append("TASK_ID_OR_JOIN_MISMATCH")
    if rates["direct"] != rates["guarded"]:
        reasons.append("ROUTE_DIFFERENTIAL_MISSINGNESS")
    if contrast != 0:
        reasons.append("SAME_COHORT_SENTINEL_CONTRAST")
    cohort = {"missing_by_route": missing, "missing_rate_by_route": rates, "id_mismatch_rows": mismatch,
              "sentinel_change_rate_by_route": changes, "sentinel_change_contrast": contrast,
              "reason_codes": reasons, "gate": "NEEDS_INDEPENDENT_AUDIT" if reasons else "CLEAR"}
    return {"kind": "summary", "case": case, "primary_only": primary, "pre_post_reference_deck": reference, "same_cohort_control": cohort}


def expected_class(case, truths):
    pairs = {(r["case"], r["route"], r["assigned_task_id"]): r for r in truths}
    direct = [pairs[(case, "direct", f"{case}-task-{n}")] for n in range(1, 5)]
    guarded = [pairs[(case, "guarded", f"{case}-task-{n}")] for n in range(1, 5)]
    if any(not r["sentinel_is_route_null"] or r["sentinel_after_true"] != r["sentinel_before_true"] for r in guarded + direct):
        return "COLLATERAL_FAIL"
    if case == "true_primary_benefit":
        return "TRUE_PRIMARY_BENEFIT"
    if case == "route_missingness":
        return "ROUTE_SPECIFIC_MISSINGNESS"
    if case == "task_id_swap":
        return "TASK_ID_MISJOIN"
    if case == "joint_export_error":
        return "OUTCOME_EXPORT_BIAS"
    return "NO_SIGNAL"


def verify(events, mutation_checks=True):
    freeze = read_json("FREEZE.json")
    for name, digest in freeze["frozen_sha256"].items():
        if name == "audit.py":
            continue  # Auditor self-identity is verified from GitHub readback by the launcher.
        raw = (ROOT / name).read_bytes().replace(b"\r\n", b"\n")
        actual = hashlib.sha256(raw.replace(b"\n", b"\r\n")).hexdigest()
        if actual != digest:
            raise ValueError(f"frozen source/input hash mismatch: {name}")
    expected_rows = read_json("reported_rows.json")
    expected_refs = read_json("reference_deck.json")
    truths = read_json("oracle.json")
    runs = [x for x in events if x.get("kind") == "run"]
    episodes = [x for x in events if x.get("kind") == "episode"]
    refs = [x for x in events if x.get("kind") == "reference"]
    summaries = [x for x in events if x.get("kind") == "summary"]
    if len(runs) != 1 or runs[0].get("freeze_id") != freeze["freeze_id"]:
        raise ValueError("run/freeze identity mismatch")
    if runs[0].get("candidate_sha256") != freeze["frozen_sha256"]["candidate.py"]:
        raise ValueError("candidate source identity mismatch")
    if runs[0].get("reported_rows_sha256") != hashlib.sha256((ROOT / "reported_rows.json").read_bytes()).hexdigest():
        raise ValueError("reported input hash mismatch")
    if runs[0].get("reference_deck_sha256") != hashlib.sha256((ROOT / "reference_deck.json").read_bytes()).hexdigest():
        raise ValueError("reference input hash mismatch")
    if [canonical(x) for x in episodes] != [canonical(x) for x in expected_rows]:
        raise ValueError("episode rows differ from frozen all-attempt schedule")
    if [canonical(x) for x in refs] != [canonical(x) for x in expected_refs]:
        raise ValueError("reference rows differ from frozen deck")
    if len(summaries) != len(freeze["case_order"]):
        raise ValueError("summary count mismatch")
    reconstructed = [replay_summary(case, [r for r in episodes if r["case"] == case], [r for r in refs if r["case"] == case]) for case in freeze["case_order"]]
    if [canonical(x) for x in summaries] != [canonical(x) for x in reconstructed]:
        raise ValueError("candidate summary does not replay")
    if len(truths) != len(expected_rows):
        raise ValueError("oracle row count mismatch")
    truth_keys = [(r["case"], r["route"], r["assigned_task_id"]) for r in truths]
    if len(set(truth_keys)) != len(truth_keys) or set(truth_keys) != {(r["case"], r["route"], r["assigned_task_id"]) for r in expected_rows}:
        raise ValueError("oracle assignment identity mismatch")
    for case in freeze["case_order"]:
        case_truth = [r for r in truths if r["case"] == case]
        for route in ("direct", "guarded"):
            arm = [r for r in case_truth if r["route"] == route]
            if len(arm) != 4:
                raise ValueError("oracle arm population mismatch")
        direct = [r for r in case_truth if r["route"] == "direct"]
        guarded = [r for r in case_truth if r["route"] == "guarded"]
        true_effect = avg([r["primary_true"] for r in guarded]) - avg([r["primary_true"] for r in direct])
        expected_effect = 0.25 if case == "true_primary_benefit" else 0.0
        if true_effect != expected_effect:
            raise ValueError("oracle primary truth differs from the frozen scenario")
        real_sentinel_rows = [r for r in case_truth if r["sentinel_after_true"] != r["sentinel_before_true"]]
        expected_sentinel_rows = 1 if case == "real_sentinel_collateral" else 0
        if len(real_sentinel_rows) != expected_sentinel_rows:
            raise ValueError("oracle sentinel truth differs from the frozen scenario")
    by_case = {case: [r for r in summaries if r["case"] == case][0] for case in freeze["case_order"]}
    audit_labels = {case: expected_class(case, truths) for case in freeze["case_order"]}
    required_alert = {"route_missingness", "task_id_swap", "joint_export_error", "real_sentinel_collateral"}
    if {c for c, s in by_case.items() if s["same_cohort_control"]["gate"] != "CLEAR"} != required_alert:
        raise ValueError("same-cohort warnings differ from preregistered case set")
    if any(by_case[c]["same_cohort_control"]["gate"] != "CLEAR" for c in ("clean_null", "true_primary_benefit")):
        raise ValueError("clean or true-benefit case falsely quarantined")
    if audit_labels["real_sentinel_collateral"] != "COLLATERAL_FAIL":
        raise ValueError("real sentinel mutation misclassified")
    if audit_labels["joint_export_error"] != "OUTCOME_EXPORT_BIAS":
        raise ValueError("known joint export error not independently classified")
    if mutation_checks:
        probes = []
        for mutate in (
            lambda x: x.pop(next(i for i, e in enumerate(x) if e.get("kind") == "episode")),
            lambda x: next(e for e in x if e.get("kind") == "summary")["same_cohort_control"].update(gate="CLEAR"),
            lambda x: next(e for e in x if e.get("case") == "task_id_swap" and e.get("kind") == "episode").update(observed_task_id="task-forged"),
            lambda x: next(e for e in x if e.get("case") == "route_missingness" and e.get("kind") == "episode" and not e["outcome_record_present"]).update(primary_observed=1, outcome_record_present=True),
            lambda x: next(e for e in x if e.get("case") == "joint_export_error" and e.get("kind") == "episode").update(sentinel_after_observed=0),
            lambda x: x.pop(next(i for i, e in enumerate(x) if e.get("kind") == "reference")),
        ):
            mutated = json.loads(json.dumps(events))
            mutate(mutated)
            try:
                verify(mutated, mutation_checks=False)
            except (ValueError, KeyError, StopIteration):
                probes.append("REJECTED")
            else:
                probes.append("ACCEPTED")
        if probes != ["REJECTED"] * 6:
            raise ValueError("one or more corruption controls escaped")
    else:
        probes = []
    return {"status": "PASS_METHOD_SCOPED", "episode_rows": len(episodes), "reference_rows": len(refs),
            "summaries": len(summaries), "same_cohort_warning_cases": sorted(required_alert),
            "independent_ground_truth": audit_labels, "mutation_controls": {"rejected": len(probes), "total": len(probes)}}


def main():
    events = read_raw(sys.argv[1] if len(sys.argv) > 1 else ROOT / "candidate_raw.jsonl")
    result = verify(events)
    result["raw_sha256"] = hashlib.sha256(Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "candidate_raw.jsonl").read_bytes()).hexdigest()
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()

