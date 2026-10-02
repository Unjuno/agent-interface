"""Independent posthoc check of preregistered #6680 D gates.

This is deliberately separate from temporal_auditor.py. It qualifies an
already-retained construction raw/audit pair; it never invokes the candidate.
"""

import json
import sys
from pathlib import Path


def adjudicate(raw, fixture, oracle, audit):
    errors = []
    rows = raw.get("rows")
    if not isinstance(rows, list):
        return {"status": "FAIL_PREREGISTERED_GATE", "errors": ["raw rows missing"]}

    expected_keys = {(case["id"], policy) for case in fixture["cases"] for policy in fixture["policies"]}
    observed_keys = [(row.get("case_id"), row.get("policy")) for row in rows]
    if len(observed_keys) != len(set(observed_keys)) or set(observed_keys) != expected_keys:
        errors.append("case-policy coverage is incomplete, duplicated, or unexpected")
    if audit.get("status") != "PASS_METHOD_SCOPED" or audit.get("errors"):
        errors.append("retained raw-only audit did not pass cleanly")

    by_case = {case["id"]: case for case in fixture["cases"]}
    identifiable = set(oracle["identifiable_case_ids"])
    wrong = {p: 0 for p in ("bounded_diagnose", "always_reobserve", "always_reset", "immediate_yield")}
    recurrent = dict(wrong)
    useful = dict(wrong)
    release_latency = {}
    valid_rows = []

    for row in rows:
        cid, policy, action = row.get("case_id"), row.get("policy"), row.get("action")
        case = by_case.get(cid)
        truth = oracle["worlds"].get(cid) if cid is not None else None
        if case is None or truth is None or policy not in wrong:
            errors.append("row references unknown case or policy")
            continue
        if action not in truth["effects"]:
            errors.append("row action has no frozen effect outcome")
            continue

        lease, probe = case["lease"], case["probe_observation"]
        receipt = lease.get("release_receipt")
        count = row.get("diagnostic_observations")
        if not isinstance(count, int) or count < 0 or count > fixture["max_probe_observations"]:
            errors.append("diagnostic observation budget exceeded or malformed")
        probe_ok = bool(
            fixture["probe"]["admissible"]
            and not fixture["probe"]["effectful"]
            and not fixture["probe"]["extends_lease"]
            and case["probe_observation"]["admissible"]
            and case["probe_observation"].get("supported", True)
            and case["probe_observation"]["received_tick"] == fixture["probe"]["tick"]
            and case["probe_observation"]["source_tick"] <= case["probe_observation"]["received_tick"]
            and receipt
            and receipt.get("lease_id") == lease["id"]
            and receipt.get("tick") == lease.get("release_requested_tick")
            and receipt.get("tick") <= case["probe_observation"]["received_tick"]
        )
        if count and not probe_ok:
            errors.append("an arm consumed an ineligible, unsupported, or unsafe probe")
        if policy == "always_reobserve" and count != int(bool(probe_ok)):
            errors.append("fixed reobserve arm did not respect the shared probe eligibility gate")
        if policy == "always_reobserve" and action != ("reobserve" if probe_ok else "yield"):
            errors.append("fixed reobserve arm action differs from its frozen policy/eligibility")
        if policy == "always_reset" and action != "reset":
            errors.append("fixed reset arm action differs from its frozen policy")
        if policy == "immediate_yield" and action != "yield":
            errors.append("immediate-YIELD arm action differs from its frozen policy")
        if policy == "bounded_diagnose":
            alarm = case["pre_probe_observation"]
            alarm_signature = {"source_age": alarm["received_tick"] - alarm["source_tick"], "residual": abs(alarm["position"] - (fixture["predictor"]["intercept"] + fixture["predictor"]["velocity"] * alarm["received_tick"]))}
            prior_allows_probe = alarm_signature in fixture["diagnostic_alarm_signatures"]
            expected_count = int(bool(prior_allows_probe and probe_ok))
            if count != expected_count:
                errors.append("diagnosis consumed a probe without a preregistered discriminating prior or admissible observation")
            if cid in identifiable and action != truth["correct_recovery"]:
                errors.append("diagnosis did not select the oracle recovery in an identifiable case")
            if cid not in identifiable and action != "yield":
                errors.append("diagnosis acted rather than YIELD outside identifiable cases")
        if count and (
            not receipt
            or receipt.get("lease_id") != lease["id"]
            or receipt.get("tick") != lease.get("release_requested_tick")
            or receipt.get("tick") > probe.get("received_tick")
            or probe.get("received_tick") != fixture["probe"].get("tick")
            or probe.get("source_tick", fixture["probe"]["tick"] + 1) > probe.get("received_tick", -1)
        ):
            errors.append("probe preceded matching release or violated frozen timestamp boundary")
        if row.get("probe_source_age") is not None and row["probe_source_age"] != probe["received_tick"] - probe["source_tick"]:
            errors.append("reported probe age disagrees with frozen event timestamps")

        effect = truth["effects"][action]
        valid_rows.append(row)
        if policy in wrong:
            wrong[policy] += int(action in ("reobserve", "reset") and action != truth.get("correct_recovery"))
            residual = effect.get("post_recovery_residual")
            recurrent[policy] += int(residual is not None and residual >= fixture["alarm_threshold"])
            useful[policy] += int(bool(effect.get("useful")))
        release_latency[ (cid, policy) ] = None if not receipt else receipt["tick"] - lease["release_requested_tick"]

    diag_wrong = sum(1 for r in valid_rows if r.get("case_id") in identifiable and r.get("policy") == "bounded_diagnose" and r.get("action") in ("reobserve", "reset") and r.get("action") != oracle["worlds"][r["case_id"]]["correct_recovery"])
    diag_rec = sum(1 for r in valid_rows if r.get("case_id") in identifiable and r.get("policy") == "bounded_diagnose" and oracle["worlds"][r["case_id"]]["effects"][r["action"]].get("post_recovery_residual") is not None and oracle["worlds"][r["case_id"]]["effects"][r["action"]]["post_recovery_residual"] >= fixture["alarm_threshold"])
    fixed_wrong, fixed_rec = {}, {}
    for policy in ("always_reobserve", "always_reset"):
        rs = [r for r in valid_rows if r.get("case_id") in identifiable and r.get("policy") == policy]
        fixed_wrong[policy] = sum(r.get("action") in ("reobserve", "reset") and r.get("action") != oracle["worlds"][r["case_id"]]["correct_recovery"] for r in rs)
        fixed_rec[policy] = sum((lambda x: x is not None and x >= fixture["alarm_threshold"])(oracle["worlds"][r["case_id"]]["effects"][r["action"]].get("post_recovery_residual")) for r in rs)
    if not all(diag_wrong < value for value in fixed_wrong.values()):
        errors.append("diagnosis does not strictly reduce wrong recoveries against both fixed policies")
    if not all(diag_rec < value for value in fixed_rec.values()):
        errors.append("diagnosis does not strictly reduce next-state residual recurrence against both fixed policies")

    for case in fixture["cases"]:
        base = release_latency.get((case["id"], "immediate_yield"))
        for policy in fixture["policies"]:
            current = release_latency.get((case["id"], policy))
            if current is not None and base is not None and current > base:
                errors.append("release latency exceeds the immediate-YIELD baseline")
    return {
        "status": "PASS_PREREGISTERED_GATES_CONSTRUCTION_ONLY" if not errors else "FAIL_PREREGISTERED_GATE",
        "errors": errors,
        "coverage_rows": len(rows),
        "identifiable_counts": {
            "bounded_diagnose_wrong_recoveries": diag_wrong,
            "bounded_diagnose_post_recovery_residuals": diag_rec,
            "bounded_diagnose_useful_effects": useful["bounded_diagnose"],
            "always_reobserve_wrong_recoveries": fixed_wrong["always_reobserve"],
            "always_reset_wrong_recoveries": fixed_wrong["always_reset"],
            "always_reobserve_post_recovery_residuals": fixed_rec["always_reobserve"],
            "always_reset_post_recovery_residuals": fixed_rec["always_reset"],
            "immediate_yield_wrong_recoveries": sum(1 for r in valid_rows if r.get("case_id") in identifiable and r.get("policy") == "immediate_yield" and r.get("action") in ("reobserve", "reset") and r.get("action") != oracle["worlds"][r["case_id"]]["correct_recovery"]),
            "immediate_yield_useful_effects": sum(1 for r in valid_rows if r.get("case_id") in identifiable and r.get("policy") == "immediate_yield" and oracle["worlds"][r["case_id"]]["effects"][r["action"]].get("useful")),
        },
        "interpretation": "The D gates are met only for this deterministic authored fixture; this is not empirical causal evidence or formal container execution.",
    }


if __name__ == "__main__":
    root = Path(__file__).parent
    raw = json.loads(Path(sys.argv[1]).read_text())
    audit = json.loads(Path(sys.argv[2]).read_text())
    result = adjudicate(raw, json.loads((root / "temporal_fixture.json").read_text()), json.loads((root / "temporal_oracle.json").read_text()), audit)
    rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if len(sys.argv) > 3:
        Path(sys.argv[3]).write_text(rendered)
    print(rendered, end="")
    raise SystemExit(0 if result["status"] == "PASS_PREREGISTERED_GATES_CONSTRUCTION_ONLY" else 1)
