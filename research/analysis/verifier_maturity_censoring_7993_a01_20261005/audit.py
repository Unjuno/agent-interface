#!/usr/bin/env python3
"""Independent raw-only verifier. It never imports candidate.py."""
from __future__ import annotations

import argparse
import copy
import json
from fractions import Fraction
from pathlib import Path

PROTOCOL = "issue-7993-t0-a01-v1"
ROOT = Path(__file__).parent


def reference_record(s: dict, alpha: Fraction) -> dict:
    rows = s["rows"]
    n = len(rows)
    resolved = [r for r in rows if r["status"] == "resolved"]
    unresolved = [r for r in rows if r["status"] != "resolved"]
    errors = sum(r["loss"] for r in resolved)
    cc = Fraction(errors, len(resolved)) if resolved else None
    low = Fraction(errors, n)
    high = Fraction(errors + len(unresolved), n)
    counts = {k: sum(r["status"] == k for r in rows)
              for k in ("permanent_loss_unknown_cause", "pending", "resolved", "safe_terminal_stop")}
    m = s["model"]
    status, reason, estimate = "ELIGIBLE", "known verified outcome-independent follow-up with positive support", None
    if not m.get("known"):
        status, reason = "UNKNOWN", "censor model not known"
    elif m.get("independence") != "verified":
        status, reason = "UNKNOWN", "outcome-independence assumption not verified"
    elif any(r["status"] in {"safe_terminal_stop", "permanent_loss_unknown_cause"} for r in rows):
        status, reason = "UNKNOWN", "typed terminal/loss status is not ordinary censoring"
    else:
        pis = m.get("pi_by_stratum", {})
        row_pis = [Fraction(pis.get(r["stratum"], "0")) for r in rows]
        if any(pi <= 0 or pi > 1 for pi in row_pis):
            status, reason = "UNKNOWN", "zero/invalid follow-up probability violates positivity"
        else:
            estimate = sum((Fraction(r["loss"]) / Fraction(pis[r["stratum"]])
                            for r in resolved), Fraction(0, 1)) / n
    return {
        "snapshot_id": s["snapshot_id"], "case_id": s["case_id"], "checkpoint": s["checkpoint"],
        "n_assigned": n, "status_counts": counts,
        "complete_case": {"risk": None if cc is None else str(cc),
                           "naive_le_alpha": None if cc is None else cc <= alpha},
        "all_assigned_bounds": {"lower": str(low), "upper": str(high),
                                "supports_le_alpha": high <= alpha},
        "censor_adjusted": {
            "status": status, "reason": reason,
            "estimator": "horvitz_thompson_point_estimate" if estimate is not None else None,
            "point_estimate": None if estimate is None else str(estimate),
            "is_risk_certificate": False,
        },
    }


def observed_signature(s: dict) -> tuple:
    return (s["model"], tuple((r["row_id"], r["stratum"], r["status"], r.get("loss"))
                               for r in s["rows"]))


def validate(candidate_input: dict, oracle_input: dict, result: dict) -> list[str]:
    errors: list[str] = []
    if candidate_input.get("protocol") != PROTOCOL or oracle_input.get("protocol") != PROTOCOL:
        return ["protocol_identity_mismatch"]
    if result.get("protocol") != PROTOCOL:
        errors.append("candidate_protocol_mismatch")
    try:
        alpha = Fraction(candidate_input["alpha"])
        snapshots = candidate_input["snapshots"]
        oracle_rows = oracle_input["snapshots"]
        snap_ids = [s["snapshot_id"] for s in snapshots]
        oracle_ids = [o["snapshot_id"] for o in oracle_rows]
        if len(set(snap_ids)) != len(snap_ids) or len(set(oracle_ids)) != len(oracle_ids):
            errors.append("duplicate_snapshot_identity")
        if set(snap_ids) != set(oracle_ids):
            errors.append("candidate_oracle_snapshot_set_mismatch")
        actual_records = result.get("records", [])
        actual_by_id = {r.get("snapshot_id"): r for r in actual_records}
        if len(actual_by_id) != len(actual_records) or set(actual_by_id) != set(snap_ids):
            errors.append("candidate_result_snapshot_set_mismatch")
        if result.get("alpha") != str(alpha):
            errors.append("alpha_mismatch")
        oracle_by_id = {o["snapshot_id"]: o for o in oracle_rows}
        source_by_id = {s["snapshot_id"]: s for s in snapshots}

        for s in snapshots:
            sid = s["snapshot_id"]
            o = oracle_by_id.get(sid)
            if o is None:
                continue
            truth = o["loss_by_row"]
            ids = [r["row_id"] for r in s["rows"]]
            if len(set(ids)) != len(ids) or set(ids) != set(truth):
                errors.append(f"row_identity_mismatch:{sid}")
                continue
            if any(type(v) is not int or v not in (0, 1) for v in truth.values()):
                errors.append(f"nonbinary_oracle_loss:{sid}")
                continue
            for r in s["rows"]:
                if r["status"] == "resolved" and r.get("loss") != truth[r["row_id"]]:
                    errors.append(f"resolved_label_oracle_mismatch:{sid}:{r['row_id']}")
                if r["status"] != "resolved" and "loss" in r:
                    errors.append(f"lookahead_label_leak:{sid}:{r['row_id']}")
            exact_risk = Fraction(sum(truth.values()), len(truth))
            if Fraction(o["full_cohort_risk"]) != exact_risk:
                errors.append(f"oracle_risk_self_mismatch:{sid}")
            if o.get("mechanism_matches_declared_model") != (o.get("mechanism") == "independent_bernoulli_followup"):
                errors.append(f"oracle_mechanism_flag_mismatch:{sid}")
            if sid not in actual_by_id:
                continue
            expected = reference_record(s, alpha)
            if actual_by_id[sid] != expected:
                errors.append(f"candidate_record_reconstruction_mismatch:{sid}")
            bounds = actual_by_id[sid].get("all_assigned_bounds", {})
            if bounds:
                if not (Fraction(bounds["lower"]) <= exact_risk <= Fraction(bounds["upper"])):
                    errors.append(f"all_assigned_bound_excludes_truth:{sid}")
            adjusted = actual_by_id[sid].get("censor_adjusted", {})
            if adjusted.get("is_risk_certificate") is not False:
                errors.append(f"point_estimate_promoted_to_certificate:{sid}")

        ids_to_result = actual_by_id
        bad = ids_to_result.get("informative_delay_known_bad@interim")
        if bad:
            if (bad["complete_case"]["risk"] != "0" or
                bad["complete_case"]["naive_le_alpha"] is not True or
                Fraction(oracle_by_id["informative_delay_known_bad@interim"]["full_cohort_risk"]) != Fraction(1, 4) or
                bad["all_assigned_bounds"]["upper"] != "1/4" or
                bad["all_assigned_bounds"]["supports_le_alpha"] is not False):
                errors.append("informative_delay_undercoverage_witness_missing")
        elif snap_ids:
            errors.append("informative_delay_witness_missing")

        zero_support = ids_to_result.get("zero_support_error_stratum@interim")
        if zero_support and zero_support["censor_adjusted"]["status"] != "UNKNOWN":
            errors.append("zero_support_not_unknown")

        safe = ids_to_result.get("safe_terminal_stop@terminal")
        if safe and (safe["status_counts"]["safe_terminal_stop"] != 1 or
                     safe["censor_adjusted"]["point_estimate"] is not None or
                     safe["all_assigned_bounds"]["upper"] != "1/4"):
            errors.append("safe_terminal_stop_conflated")
        lost = ids_to_result.get("permanent_loss_unknown_cause@horizon")
        if lost and (lost["status_counts"]["permanent_loss_unknown_cause"] != 1 or
                     lost["censor_adjusted"]["point_estimate"] is not None or
                     lost["all_assigned_bounds"]["upper"] != "1/4"):
            errors.append("permanent_loss_conflated")

        early = ids_to_result.get("delayed_eventually_resolved@early")
        late = ids_to_result.get("delayed_eventually_resolved@late")
        if early and late:
            if (early["all_assigned_bounds"]["upper"] != "1/4" or
                late["all_assigned_bounds"]["lower"] != "1/4" or
                late["all_assigned_bounds"]["upper"] != "1/4"):
                errors.append("delayed_resolution_transition_mismatch")

        group = [o for o in oracle_rows if o.get("enumeration_group") == "independent_masks_16"]
        if len(group) != 16 or {o.get("design_probability") for o in group} != {"1/16"}:
            errors.append("independent_mask_enumeration_incomplete")
        else:
            risks = {Fraction(o["full_cohort_risk"]) for o in group}
            if risks != {Fraction(1, 4)}:
                errors.append("independent_mask_cohort_truth_mismatch")
            estimates = []
            for o in group:
                rec = ids_to_result.get(o["snapshot_id"])
                if not rec or rec["censor_adjusted"]["status"] != "ELIGIBLE":
                    errors.append(f"independent_mask_not_eligible:{o['snapshot_id']}")
                    continue
                estimates.append(Fraction(rec["censor_adjusted"]["point_estimate"]))
            if len(estimates) == 16 and sum(estimates, Fraction(0)) / 16 != Fraction(1, 4):
                errors.append("horvitz_thompson_exact_expectation_mismatch")

        # The hidden informative schedule is observationally indistinguishable
        # from an eligible independent mask. The point estimate is not a risk
        # certificate; the mismatch is a limitation, not a detectable PASS.
        hidden_id = "informative_delay_hidden_misspecification@interim"
        mask14_id = "independent_mask_14@interim"
        if hidden_id in source_by_id and mask14_id in source_by_id:
            hidden = source_by_id[hidden_id]
            mask14 = source_by_id[mask14_id]
            if observed_signature(hidden) != observed_signature(mask14):
                errors.append("hidden_misspecification_witness_not_observationally_matched")
            ho = oracle_by_id.get(hidden_id, {})
            if ho.get("mechanism_matches_declared_model") is not False:
                errors.append("hidden_misspecification_not_retained")
            hres = ids_to_result.get(hidden_id, {})
            if hres.get("censor_adjusted", {}).get("is_risk_certificate") is not False:
                errors.append("hidden_misspecification_overclaimed")
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        errors.append(f"malformed_evidence:{type(exc).__name__}:{exc}")
    return errors


def mutation_suite(candidate_input: dict, oracle_input: dict, result: dict) -> list[dict]:
    cases = []

    def mutate(name, target, fn):
        ci, oi, ri = copy.deepcopy(candidate_input), copy.deepcopy(oracle_input), copy.deepcopy(result)
        fn(ci, oi, ri)
        errors = validate(ci, oi, ri)
        cases.append({"mutation": name, "rejected": bool(errors), "error_count": len(errors)})

    def rec(result, sid):
        return next(r for r in result["records"] if r["snapshot_id"] == sid)

    mutate("drop_result_record", "result", lambda ci, oi, ri: ri["records"].pop())
    mutate("corrupt_upper_bound", "result", lambda ci, oi, ri: rec(ri, "independent_mask_00@interim")["all_assigned_bounds"].update(upper="0"))
    mutate("flip_complete_case_claim", "result", lambda ci, oi, ri: rec(ri, "informative_delay_known_bad@interim")["complete_case"].update(naive_le_alpha=False))
    mutate("corrupt_ht_estimate", "result", lambda ci, oi, ri: rec(ri, "independent_mask_14@interim")["censor_adjusted"].update(point_estimate="1/2"))
    mutate("accept_zero_support", "result", lambda ci, oi, ri: rec(ri, "zero_support_error_stratum@interim")["censor_adjusted"].update(status="ELIGIBLE"))
    mutate("erase_safe_stop_type", "result", lambda ci, oi, ri: rec(ri, "safe_terminal_stop@terminal")["status_counts"].update(safe_terminal_stop=0))
    mutate("promote_estimate_to_certificate", "result", lambda ci, oi, ri: rec(ri, "independent_mask_14@interim")["censor_adjusted"].update(is_risk_certificate=True))
    mutate("drop_assigned_denominator", "result", lambda ci, oi, ri: rec(ri, "pending_at_horizon@horizon").update(n_assigned=3))
    mutate("change_oracle_label", "oracle", lambda ci, oi, ri: next(o for o in oi["snapshots"] if o["snapshot_id"] == "independent_mask_14@interim")["loss_by_row"].update(e2=1))
    mutate("erase_oracle_row", "oracle", lambda ci, oi, ri: next(o for o in oi["snapshots"] if o["snapshot_id"] == "independent_mask_14@interim")["loss_by_row"].pop("e2"))
    return cases


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-input", type=Path, default=ROOT / "candidate_input.json")
    parser.add_argument("--oracle-input", type=Path, default=ROOT / "oracle_input.json")
    args = parser.parse_args()
    ci = json.loads(args.candidate_input.read_text(encoding="utf-8"))
    oi = json.loads(args.oracle_input.read_text(encoding="utf-8"))
    result = json.loads(args.candidate.read_text(encoding="utf-8"))
    errors = validate(ci, oi, result)
    mutations = mutation_suite(ci, oi, result)
    if not all(m["rejected"] for m in mutations):
        errors.append("mutation_escaped")
    report = {
        "protocol": PROTOCOL,
        "pass": not errors,
        "method_disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
        "snapshot_count": len(ci.get("snapshots", [])),
        "independent_mask_count": sum(o.get("enumeration_group") == "independent_masks_16" for o in oi.get("snapshots", [])),
        "all_assigned_bounds_contain_truth": not any(e.startswith("all_assigned_bound_excludes_truth") for e in errors),
        "informative_delay_witness": "pass" if not any("informative_delay" in e for e in errors) else "fail",
        "ht_exact_mask_mean": "1/4" if not any("horvitz_thompson" in e for e in errors) else "fail",
        "mutation_count": len(mutations),
        "mutation_rejections": mutations,
        "errors": errors,
    }
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
