#!/usr/bin/env python3
"""Independent raw-only audit; intentionally does not import candidate code."""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

from spec import exact_spec


def outcome(events: list[str], seed: int, stratum: int, spec: dict) -> str:
    mandatory = set(spec["mandatory_events"])
    present = set(events)
    if len(present) != len(events) or not present <= set(spec["base_trace"]):
        return "INVALID_AUTHORITY_OR_DEPENDENCY"
    if events != [e for e in spec["base_trace"] if e in present]:
        return "INVALID_AUTHORITY_OR_DEPENDENCY"
    if not mandatory <= present:
        return "INVALID_AUTHORITY_OR_DEPENDENCY"
    if any(not set(parents) <= present for event, parents in spec["dependencies"].items() if event in present):
        return "INVALID_AUTHORITY_OR_DEPENDENCY"
    digest = lambda salt: int.from_bytes(hashlib.sha256(f"{seed}|{salt}".encode()).digest()[:8], "big") / 2**64
    if "competing_fault" in present and digest("competitor") < spec["competing_failure_rate"]:
        return spec["competing_fingerprint"]
    if {"observation", "commit", "timing_guard"} <= present:
        rates = spec["warm_target_rates_by_stratum"] if "warmup" in present else spec["cold_target_rates_by_stratum"]
        if digest("target") < rates[stratum]:
            return spec["target_fingerprint"]
    return "NO_FAILURE"


def cp_lower(k: int, n: int, alpha: float) -> float:
    if n <= 0 or k <= 0:
        return 0.0
    lo, hi = 0.0, k / n
    for _ in range(64):
        p = (lo + hi) / 2
        term = math.exp(math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)+k*math.log(p)+(n-k)*math.log1p(-p))
        tail = term
        for j in range(k, n):
            term *= (n-j)/(j+1) * p/(1-p)
            tail += term
        if tail > alpha:
            hi = p
        else:
            lo = p
    return lo


def cp_upper(k: int, n: int, alpha: float) -> float:
    if n <= 0 or k >= n:
        return 1.0
    lo, hi = k / n, 1.0
    for _ in range(64):
        p = (lo + hi) / 2
        term = math.exp(math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)+k*math.log(p)+(n-k)*math.log1p(-p))
        tail = term
        for j in range(k, 0, -1):
            term *= j/(n-j+1) * (1-p)/p
            tail += term
        if tail > alpha:
            lo = p
        else:
            hi = p
    return hi


def audit(raw: dict, spec: dict | None = None, expected_freeze_digest: str | None = None) -> dict:
    spec = exact_spec() if spec is None else spec
    errors: list[str] = []
    runs = raw.get("runs")
    expected_keys = {(m, i) for m in ("single_run", "fixed_64", "sequential") for i in range(spec["instances"])}
    found_keys = {(r.get("method"), r.get("instance")) for r in runs or []}
    if found_keys != expected_keys or len(runs or []) != len(expected_keys):
        errors.append("run_matrix_mismatch")
    if (not expected_freeze_digest or raw.get("freeze_digest") != expected_freeze_digest
            or raw.get("expected_freeze_digest") != expected_freeze_digest):
        errors.append("freeze_digest_mismatch")
    search_seeds: set[int] = set()
    confirm_seeds_by_instance: dict[int, set[int]] = {}
    confirms: dict[tuple[str, int], list[dict]] = {}
    for r in runs or []:
        method, instance = r.get("method"), r.get("instance")
        if not isinstance(instance, int) or not 0 <= instance < spec["instances"]:
            errors.append("invalid_instance"); continue
        stratum = instance // 3
        for row in r.get("baseline_trials", []) + r.get("candidate_trials", []):
            seed = row.get("seed")
            expected_fp = outcome(row.get("events", []), seed, stratum, spec)
            expected_code = 17 if expected_fp in (spec["target_fingerprint"], spec["competing_fingerprint"], "INVALID_AUTHORITY_OR_DEPENDENCY") else 0
            if (row.get("stratum") != stratum or row.get("fingerprint") != expected_fp
                    or row.get("exit_code") != expected_code):
                errors.append("search_outcome_or_stratum_mismatch")
            search_seeds.add(seed)
        local_search_seeds = [x.get("seed") for x in r.get("baseline_trials", []) + r.get("candidate_trials", [])]
        if len(local_search_seeds) != len(set(local_search_seeds)):
            errors.append("search_seed_reuse")
        base = r.get("baseline_trials", [])
        if len(base) != spec["baseline_repetitions"]:
            errors.append("baseline_count_mismatch")
        if any(x.get("events") != spec["base_trace"] or x.get("stage") != "baseline" for x in base):
            errors.append("baseline_trace_mismatch")
        count = sum(x.get("fingerprint") == spec["target_fingerprint"] for x in base)
        alpha = spec["familywise_alpha"] / (spec["instances"] * 2)
        lower = cp_lower(count, len(base), alpha)
        threshold = max(0.0, lower - spec["noninferiority_margin"])
        if (r.get("baseline_target_successes") != count or abs(r.get("baseline_lower_bound", -9) - lower) > 1e-12
                or abs(r.get("screen_threshold", -9) - threshold) > 1e-12
                or abs(r.get("screen_threshold", -9) - max(0.0, lower-spec["noninferiority_margin"])) > 1e-12):
            errors.append("baseline_gate_mismatch")
        current = tuple(spec["base_trace"])
        candidates = r.get("candidate_trials", [])
        cursor = 0
        attempts = r.get("attempts", [])
        if [x.get("group") for x in attempts] != [name for name, _ in spec["removal_groups"]]:
            errors.append("removal_group_sequence_mismatch")
        for attempt in attempts:
            group = dict((name, tuple(events)) for name, events in spec["removal_groups"])[attempt.get("group")]
            proposed = tuple(e for e in current if e not in set(group))
            if tuple(attempt.get("trace_before", [])) != current:
                errors.append("trace_before_mismatch")
            if attempt.get("raw_trial_start") != cursor:
                errors.append("raw_attempt_offset_mismatch")
            if proposed != current and (tuple(attempt.get("proposed_trace", [])) != proposed
                                        or abs(attempt.get("threshold", -9)-threshold) > 1e-12):
                errors.append("candidate_proposal_or_threshold_mismatch")
            if "reset" not in proposed or "lease" not in proposed or "release" not in proposed:
                errors.append("authority_trace_violation")
            nraw = attempt.get("raw_trial_count", 0)
            batch = candidates[cursor:cursor+nraw]
            if nraw != len(batch):
                errors.append("omitted_raw_attempt")
            cursor += nraw
            for row in batch:
                if row.get("events") != list(proposed) or row.get("group") != attempt.get("group"):
                    errors.append("attempt_trace_mismatch")
                if row.get("fingerprint") == spec["competing_fingerprint"]:
                    pass  # Same exit code; only the named fingerprint counts as success.
            looks = attempt.get("looks", [])
            accepted = False
            expected_decision = "NO_OP" if proposed == current else None
            if proposed != current:
                if method == "single_run":
                    if len(batch) != 1 or len(looks) != 1 or looks[0].get("n") != 1:
                        errors.append("single_run_budget_mismatch")
                    accepted = bool(batch) and batch[0].get("fingerprint") == spec["target_fingerprint"]
                    expected_decision = "ACCEPT_ONE_HIT" if accepted else "REJECT_ONE_MISS"
                else:
                    if method == "fixed_64" and len(batch) != spec["fixed_repetitions_per_candidate"]:
                        errors.append("fixed_budget_mismatch")
                    if method == "sequential" and len(batch) > spec["sequential_maximum"]:
                        errors.append("sequential_budget_exceeded")
                    alpha = spec["familywise_alpha"] / (spec["instances"] * len(spec["removal_groups"]) * 2)
                    if method == "sequential":
                        alpha /= (spec["sequential_maximum"] - spec["sequential_minimum"]) // spec["sequential_increment"] + 1
                    last_n = 0
                    success_count = 0
                    expected_decision = "REJECT_INCONCLUSIVE"
                    stopped_early = False
                    for look_index, look in enumerate(looks):
                        n = look.get("n", 0)
                        maximum_n = spec["fixed_repetitions_per_candidate"] if method == "fixed_64" else spec["sequential_maximum"]
                        if n <= last_n or n > len(batch) or n > maximum_n:
                            errors.append("look_sequence_invalid"); break
                        required_n = (spec["fixed_repetitions_per_candidate"] if method == "fixed_64"
                                      else spec["sequential_minimum"] + look_index*spec["sequential_increment"])
                        if n != required_n:
                            errors.append("look_sequence_invalid")
                        success_count = sum(x.get("fingerprint") == spec["target_fingerprint"] for x in batch[:n])
                        bound_alpha = alpha
                        lo, hi = cp_lower(success_count, n, bound_alpha), cp_upper(success_count, n, bound_alpha)
                        if abs(look.get("lower", -9)-lo) > 1e-12 or abs(look.get("upper", -9)-hi) > 1e-12 or look.get("successes") != success_count:
                            errors.append("candidate_interval_mismatch")
                        last_n = n
                        if method == "fixed_64":
                            accepted = lo >= threshold
                            expected_decision = "ACCEPT_FIXED_BOUND" if accepted else "REJECT_FIXED_BOUND"
                        elif lo >= threshold:
                            accepted = True; expected_decision = "ACCEPT_SEQUENTIAL_BOUND"; stopped_early = True; break
                        elif hi < threshold:
                            expected_decision = "REJECT_SEQUENTIAL_BOUND"; stopped_early = True; break
                    if last_n != len(batch):
                        errors.append("raw_look_coverage_mismatch")
                    if method == "fixed_64" and len(looks) != 1:
                        errors.append("fixed_look_count_mismatch")
                    if method == "sequential":
                        expected_looks = ((last_n-spec["sequential_minimum"])//spec["sequential_increment"]+1) if stopped_early else ((spec["sequential_maximum"]-spec["sequential_minimum"])//spec["sequential_increment"]+1)
                        if len(looks) != expected_looks:
                            errors.append("sequential_look_count_mismatch")
            if attempt.get("decision") != expected_decision:
                errors.append("candidate_decision_mismatch")
            expected_n = looks[-1].get("n", 0) if looks else 0
            if attempt.get("n") != expected_n:
                errors.append("attempt_trial_count_mismatch")
            if accepted:
                current = proposed
            if tuple(attempt.get("trace_after", [])) != current:
                errors.append("trace_transition_mismatch")
        if cursor != len(candidates):
            errors.append("unaccounted_search_rows")
        if tuple(r.get("final_trace", [])) != current:
            errors.append("final_trace_mismatch")
        conf = r.get("confirmations", [])
        confirms[(method, instance)] = conf
        expected_n = spec["confirmation_repetitions_per_stratum"]
        if len(conf) != expected_n:
            errors.append("confirmation_count_mismatch")
        seen = set()
        for row in conf:
            seed = row.get("seed")
            seen.add(seed)
            before = outcome(spec["base_trace"], seed, stratum, spec)
            after = outcome(r.get("final_trace", []), seed, stratum, spec)
            delta = int(after == spec["target_fingerprint"]) - int(before == spec["target_fingerprint"])
            if (row.get("stratum"), row.get("original_fingerprint"), row.get("final_fingerprint"), row.get("delta")) != (stratum, before, after, delta):
                errors.append("confirmation_reconstruction_mismatch")
        if len(seen) != len(conf):
            errors.append("confirmation_seed_reuse")
        confirm_seeds_by_instance.setdefault(instance, seen)
    instance_ids = sorted(confirm_seeds_by_instance)
    for pos, first in enumerate(instance_ids):
        for second in instance_ids[pos+1:]:
            if confirm_seeds_by_instance[first] & confirm_seeds_by_instance[second]:
                errors.append("confirmation_instances_share_seed")
    if search_seeds.intersection(set().union(*confirm_seeds_by_instance.values()) if confirm_seeds_by_instance else set()):
        errors.append("search_confirmation_seed_overlap")
    decisions = {}
    for method in ("single_run", "fixed_64", "sequential"):
        per_instance = []
        for instance in range(spec["instances"]):
            conf = confirms.get((method, instance), [])
            n = len(conf)
            base_k = sum(x.get("original_fingerprint") == spec["target_fingerprint"] for x in conf)
            final_k = sum(x.get("final_fingerprint") == spec["target_fingerprint"] for x in conf)
            alpha = spec["familywise_alpha"] / (spec["instances"] * 2)
            base_upper, final_lower = cp_upper(base_k, n, alpha), cp_lower(final_k, n, alpha)
            neg = sum(x.get("delta") == -1 for x in conf)
            pos = sum(x.get("delta") == 1 for x in conf)
            competitor_k = sum(x.get("final_fingerprint") == spec["competing_fingerprint"] for x in conf)
            final_size = len(next((r.get("final_trace", []) for r in runs
                                   if r.get("method") == method and r.get("instance") == instance), []))
            per_instance.append({"instance": instance, "original_successes": base_k, "final_successes": final_k,
                                 "losses": neg, "gains": pos, "n": n,
                                 "original_upper": base_upper, "final_lower": final_lower,
                                 "difference_lower": final_lower-base_upper,
                                 "final_competing_failures": competitor_k, "final_trace_events": final_size,
                                 "original_rate": base_k/n if n else None, "final_rate": final_k/n if n else None,
                                 "competing_rate": competitor_k/n if n else None,
                                 "noninferiority": final_lower-base_upper >= -spec["noninferiority_margin"]})
        method_runs = [r for r in runs if r.get("method") == method]
        decisions[method] = {"instances": per_instance, "noninferiority_pass": all(x["noninferiority"] for x in per_instance),
                             "shorter_instances": sum(len(r.get("final_trace", [])) < len(r.get("initial_trace", [])) for r in method_runs),
                             "search_queries": sum(len(r.get("baseline_trials", [])) + len(r.get("candidate_trials", [])) for r in method_runs)}
    sequential_efficient = decisions["sequential"]["search_queries"] < decisions["fixed_64"]["search_queries"]
    scoped_pass = (not errors and all(decisions[m]["noninferiority_pass"] for m in ("fixed_64", "sequential"))
                   and sequential_efficient and decisions["sequential"]["shorter_instances"] > 0)
    return {"schema": "unjuno.issue8152.audit.v1", "valid": not errors, "errors": sorted(set(errors)),
            "sequential_query_advantage": sequential_efficient,
            "disposition": "METHOD_PASS_SCOPED" if scoped_pass else ("FAIL_METHOD" if errors else "HOLD"),
            "method_decisions": decisions}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 3:
        raise SystemExit("usage: audit.py RAW.json AUDIT.json FREEZE_SHA256")
    raw_path, out_path = map(Path, argv[:2])
    try:
        loaded = json.loads(raw_path.read_text())
        if not isinstance(loaded, dict):
            raise ValueError("raw_not_object")
        result = audit(loaded, expected_freeze_digest=argv[2])
    except (OSError, json.JSONDecodeError, ValueError):
        result = {"schema": "unjuno.issue8152.audit.v1", "valid": False,
                  "errors": ["raw_unparseable"], "disposition": "FAIL_METHOD",
                  "sequential_query_advantage": False, "method_decisions": {}}
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
