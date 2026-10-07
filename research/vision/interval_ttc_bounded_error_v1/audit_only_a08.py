"""A08 read-only decision audit of frozen Issue #8157 A02 raw JSONL."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import pathlib
import sys
from collections import defaultdict

IN_MODEL = {"approach", "iid", "correlated", "irregular_dropout"}
INVALID = {"passby", "stationary", "acceleration", "occlusion",
           "identity_swap", "understated_bound"}
PROFILES = IN_MODEL | INVALID
LIMIT_S = 2.0
MAX_LEAD_LOSS_S = 0.100
EPS = 1e-9


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def estimate_prefix(history):
    """Causal radius-TTC reconstruction using only this prefix."""
    if len(history) < 2 or any(not finite(x.get("t_s")) for x in history):
        return None, None
    if any(history[i]["t_s"] >= history[i + 1]["t_s"]
           for i in range(len(history) - 1)):
        return None, None
    if any(history[i].get("radius_px") is None and
           history[i + 1].get("radius_px") is None
           for i in range(len(history) - 1)):
        return None, None
    seen = [x for x in history if x.get("radius_px") is not None]
    if len(seen) < 2:
        return None, None
    if any(not finite(x.get("radius_px")) or not finite(x.get("bound_px"))
           or x["bound_px"] < 0 for x in seen):
        return None, None
    if len({x.get("track_id") for x in seen}) != 1:
        return None, None
    lower_speeds, upper_speeds = [], []
    for left, right in zip(seen, seen[1:]):
        dt = right["t_s"] - left["t_s"]
        if dt <= 0:
            return None, None
        llo, lhi = left["radius_px"] - left["bound_px"], left["radius_px"] + left["bound_px"]
        rlo, rhi = right["radius_px"] - right["bound_px"], right["radius_px"] + right["bound_px"]
        if llo <= 0 or rlo <= 0:
            return None, None
        lower_speeds.append((rlo - lhi) / dt)
        upper_speeds.append((rhi - llo) / dt)
    vlo, vhi = max(lower_speeds), min(upper_speeds)
    if vlo <= 0 or vhi < vlo:
        return None, None
    previous, current = seen[-2:]
    delta = current["radius_px"] - previous["radius_px"]
    point = (current["radius_px"] * (current["t_s"] - previous["t_s"]) / delta
             if delta > 0 else None)
    last = seen[-1]
    interval = [(last["radius_px"] - last["bound_px"]) / vhi,
                (last["radius_px"] + last["bound_px"]) / vlo]
    return point, interval


def close_number(a, b):
    return (a is None and b is None) or (finite(a) and finite(b) and
            math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12))


def validate_structure(public_rows, oracle_rows, candidate_rows):
    errors = []
    if any(len(rows) != 200 for rows in (public_rows, oracle_rows, candidate_rows)):
        errors.append("sequence_count")
    maps = [{r.get("id"): r for r in rows} for rows in
            (public_rows, oracle_rows, candidate_rows)]
    if any(len(m) != len(rows) for m, rows in zip(maps,
                                                   (public_rows, oracle_rows, candidate_rows))):
        errors.append("duplicate_id")
    public, truth, candidate = maps
    if not (set(public) == set(truth) == set(candidate)):
        errors.append("id_set")
        return errors
    counts = defaultdict(lambda: {"rows": 0, "hazards": 0,
                                  "calibration": 0, "evaluation": 0})
    for sid, label in truth.items():
        profile = label.get("profile")
        if profile not in PROFILES:
            errors.append("unknown_profile:" + str(sid))
            continue
        c = counts[profile]
        c["rows"] += 1
        c["hazards"] += int(bool(label.get("hazard")))
        split = label.get("split")
        if split not in ("calibration", "evaluation"):
            errors.append("unknown_split:" + str(sid))
        else:
            c[split] += 1
        expected = profile in IN_MODEL and label.get("hazard") is True
        if label.get("eligible_in_model") is not expected:
            errors.append("eligibility_label:" + str(sid))
        if len(label.get("truth", [])) != len(public[sid].get("history", [])):
            errors.append("oracle_prefix_count:" + str(sid))
    expected_count = {"rows": 20, "hazards": 10, "calibration": 10, "evaluation": 10}
    if set(counts) != PROFILES or any(x != expected_count for x in counts.values()):
        errors.append("profile_split_shape")
    return errors


def reconstruction_errors(public_rows, candidate_rows):
    pub = {r["id"]: r for r in public_rows}
    cand = {r["id"]: r for r in candidate_rows}
    errors = []
    if set(pub) != set(cand):
        return ["candidate_id_set"]
    for sid, row in pub.items():
        history = row["history"]
        estimates = cand[sid].get("estimates", [])
        if len(estimates) != len(history):
            errors.append("prefix_count:" + sid)
            continue
        for i, got in enumerate(estimates):
            point, interval = estimate_prefix(history[:i + 1])
            if not close_number(got.get("point_ttc_s"), point):
                errors.append(f"point:{sid}:{i}")
            actual_iv = got.get("interval_s")
            same = (actual_iv is None and interval is None) or (
                type(actual_iv) is list and interval is not None and len(actual_iv) == 2
                and close_number(actual_iv[0], interval[0])
                and close_number(actual_iv[1], interval[1]))
            if not same:
                errors.append(f"interval:{sid}:{i}")
    return errors


def threshold_for(candidate_rows, truth, method):
    controls = [r for r in candidate_rows
                if truth[r["id"]]["split"] == "calibration"
                and not truth[r["id"]]["hazard"]]
    values = {LIMIT_S}
    for row in controls:
        for estimate in row["estimates"]:
            value = (estimate.get("point_ttc_s") if method == "point" else
                     estimate["interval_s"][1] if estimate.get("interval_s") else None)
            if finite(value):
                values.add(value)
    acceptable = []
    for threshold in values:
        false = 0
        for row in controls:
            if any(((e.get("point_ttc_s") is not None and
                     e["point_ttc_s"] <= threshold) if method == "point" else
                    (e.get("interval_s") is not None and
                     e["interval_s"][1] <= threshold)) for e in row["estimates"]):
                false += 1
        if false == 0:
            acceptable.append(threshold)
    return max(acceptable) if acceptable else 0.0


def first_yield(row, threshold, method):
    for i, estimate in enumerate(row["estimates"]):
        value = (estimate.get("point_ttc_s") if method == "point" else
                 estimate["interval_s"][1] if estimate.get("interval_s") else None)
        if value is not None and value <= threshold:
            return i
    return None


def score(public_rows, oracle_rows, candidate_rows):
    truth = {r["id"]: r for r in oracle_rows}
    thresholds = {m: threshold_for(candidate_rows, truth, m)
                  for m in ("point", "interval")}
    stats = defaultdict(lambda: {
        "sequences": 0, "eligible_hazard_prefixes": 0,
        "numeric_intervals": 0, "containment_checked_prefixes": 0,
        "containment_misses": 0, "invalid_terminal_false_yield": 0,
        "evaluation_controls": 0, "point_false_yield": 0,
        "interval_false_yield": 0, "evaluation_eligible_hazards": 0,
        "point_hazard_yield": 0, "interval_hazard_yield": 0,
    })
    lead_failures, paired = [], 0
    candidate = {r["id"]: r for r in candidate_rows}
    public = {r["id"]: r for r in public_rows}
    for sid, label in truth.items():
        profile = label["profile"]
        stat = stats[profile]
        stat["sequences"] += 1
        row = candidate[sid]
        point_idx = first_yield(row, thresholds["point"], "point")
        interval_idx = first_yield(row, thresholds["interval"], "interval")
        for i, estimate in enumerate(row["estimates"]):
            interval = estimate.get("interval_s")
            if label["eligible_in_model"] and label["truth"][i]["observed"]:
                stat["eligible_hazard_prefixes"] += 1
                if interval is not None:
                    stat["numeric_intervals"] += 1
                    actual = label["truth"][i]["true_ttc_s"]
                    if actual is not None:
                        stat["containment_checked_prefixes"] += 1
                        if not interval[0] - EPS <= actual <= interval[1] + EPS:
                            stat["containment_misses"] += 1
            if i == len(row["estimates"]) - 1 and profile in INVALID and interval is not None:
                if interval[1] <= thresholds["interval"]:
                    stat["invalid_terminal_false_yield"] += 1
        if label["split"] != "evaluation":
            continue
        if not label["hazard"]:
            stat["evaluation_controls"] += 1
            stat["point_false_yield"] += point_idx is not None
            stat["interval_false_yield"] += interval_idx is not None
        elif label["eligible_in_model"]:
            stat["evaluation_eligible_hazards"] += 1
            stat["point_hazard_yield"] += point_idx is not None
            stat["interval_hazard_yield"] += interval_idx is not None
            if point_idx is not None:
                if interval_idx is None:
                    lead_failures.append(sid)
                else:
                    paired += 1
                    point_ttc = label["truth"][point_idx]["true_ttc_s"]
                    interval_ttc = label["truth"][interval_idx]["true_ttc_s"]
                    if (point_ttc is None or interval_ttc is None or
                            point_ttc - interval_ttc > MAX_LEAD_LOSS_S + EPS):
                        lead_failures.append(sid)
    profiles = {p: dict(stats[p]) for p in sorted(PROFILES)}
    coverage = {p: (profiles[p]["numeric_intervals"] /
                    profiles[p]["eligible_hazard_prefixes"]
                    if profiles[p]["eligible_hazard_prefixes"] else None)
                for p in sorted(IN_MODEL)}
    coverage_ok = all(v is not None and v >= .5 for v in coverage.values())
    contained = all(profiles[p]["containment_misses"] == 0 for p in IN_MODEL)
    invalid_ok = all(profiles[p]["invalid_terminal_false_yield"] == 0 for p in INVALID)
    improvement = {p: profiles[p]["interval_false_yield"] <
                   profiles[p]["point_false_yield"]
                   for p in ("iid", "correlated", "irregular_dropout")}
    hazard_yield = (any(profiles[p]["point_hazard_yield"] for p in IN_MODEL) and
                    any(profiles[p]["interval_hazard_yield"] for p in IN_MODEL))
    lead_ok = not lead_failures
    return {
        "thresholds_s": thresholds,
        "calibration_control_false_yields": {m: 0 for m in thresholds},
        "eligible_hazard_prefixes_by_profile": {
            p: profiles[p]["eligible_hazard_prefixes"] for p in sorted(IN_MODEL)},
        "numeric_intervals_by_profile": {
            p: profiles[p]["numeric_intervals"] for p in sorted(IN_MODEL)},
        "coverage_by_in_model_profile": coverage,
        "profiles": profiles,
        "decision_checks": {
            "coverage_at_least_50pct_each_in_model_profile": coverage_ok,
            "in_model_interval_containment": contained,
            "invalid_profile_terminal_interval_fail_closed": invalid_ok,
            "strict_false_yield_improvement": improvement,
            "both_methods_yield_on_an_eligible_hazard": hazard_yield,
            "paired_lead_rows": paired,
            "paired_lead_failures": lead_failures,
            "paired_lead_criterion": lead_ok,
        },
    }


def mutation_controls(public, oracle, candidate):
    controls = {}
    # Structural/profile eligibility corruption must be detected.
    mutated = copy.deepcopy(oracle)
    mutated[0]["eligible_in_model"] = not mutated[0]["eligible_in_model"]
    controls["profile_eligibility_flip_rejected"] = bool(validate_structure(public, mutated, candidate))
    # A missing/extra candidate output must fail prefix reconstruction.
    missing = copy.deepcopy(candidate)
    sid = next(r["id"] for r in missing if any(e.get("interval_s") is not None
                                                for e in r["estimates"]))
    target = next(r for r in missing if r["id"] == sid)
    idx = next(i for i, e in enumerate(target["estimates"])
               if e.get("interval_s") is not None)
    target["estimates"][idx]["interval_s"] = None
    controls["missing_numeric_interval_rejected"] = bool(reconstruction_errors(public, missing))
    extra = copy.deepcopy(candidate)
    oracle_by_id = {r["id"]: r for r in oracle}
    invalid_id = next(r["id"] for r in oracle if r["profile"] in INVALID)
    target = next(r for r in extra if r["id"] == invalid_id)
    target["estimates"][1]["interval_s"] = [0.0, 0.0]
    controls["extra_invalid_interval_rejected"] = bool(reconstruction_errors(public, extra))
    # False-YIELD and paired-lead controls exercise the scoring gate directly.
    mini_truth = [
        {"id": "control", "profile": "iid", "split": "evaluation", "hazard": False,
         "eligible_in_model": False, "truth": [{"observed": True, "true_ttc_s": None}]},
        {"id": "hazard", "profile": "iid", "split": "evaluation", "hazard": True,
         "eligible_in_model": True,
         "truth": [{"observed": True, "true_ttc_s": 1.0},
                   {"observed": True, "true_ttc_s": .7}]},
        {"id": "cal-control", "profile": "iid", "split": "calibration", "hazard": False,
         "eligible_in_model": False, "truth": [{"observed": True, "true_ttc_s": None}]},
    ]
    mini_pub = [{"id": "control", "history": [{}]}, {"id": "hazard", "history": [{}, {}]},
                {"id": "cal-control", "history": [{}]}]
    mini_cand = [
        {"id": "control", "estimates": [{"point_ttc_s": 1.0, "interval_s": [0.8, 1.1]}]},
        {"id": "hazard", "estimates": [{"point_ttc_s": 1.0, "interval_s": [0.9, 1.2]},
                                       {"point_ttc_s": .7, "interval_s": [.6, .8]}]},
        {"id": "cal-control", "estimates": [{"point_ttc_s": 2.5, "interval_s": [2.4, 2.5]}]},
    ]
    mini_score = score(mini_pub, mini_truth, mini_cand)
    controls["calibration_threshold_uses_controls_only"] = (
        threshold_for(mini_cand, {r["id"]: r for r in mini_truth}, "point") == LIMIT_S
        and mini_score["profiles"]["iid"]["point_false_yield"] == 1)
    # A deliberately late interval YIELD must fail the paired 100 ms limit.
    late = copy.deepcopy(mini_cand)
    late[1]["estimates"][0]["interval_s"] = [2.6, 2.7]
    late_score = score(mini_pub, mini_truth, late)
    controls["paired_lead_loss_over_100ms_detected"] = bool(
        late_score["decision_checks"]["paired_lead_failures"])
    controls["false_yield_tally_sensitive"] = (
        mini_score["profiles"]["iid"]["point_false_yield"] == 1)
    return controls


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def load_jsonl(path):
    return [json.loads(line) for line in pathlib.Path(path).read_text().splitlines()]


def main(repo, out_path):
    repo = pathlib.Path(repo)
    package = repo / "research/vision/interval_ttc_bounded_error_v1"
    freeze_a08 = json.loads((package / "FREEZE_A08_LOCAL.json").read_text())
    freeze_a04 = json.loads((package / "FREEZE_A04.json").read_text())
    freeze_a05 = json.loads((package / "FREEZE_A05.json").read_text())
    a04_report_path = package / "results/FORMAL_A04_AUDIT_ONLY/AUDIT_REPORT.json"
    a04_report = json.loads(a04_report_path.read_text())
    expected_source_hash = freeze_a08["auditor_sha256"]
    expected_protocol_hash = freeze_a08["protocol_sha256"]
    expected_test_hash = freeze_a08["test_sha256"]
    if sha(package / "audit_only_a08.py") != expected_source_hash:
        raise SystemExit("frozen A08 auditor hash mismatch")
    if sha(package / "PROTOCOL_A08_LOCAL_DECISION_AUDIT.md") != expected_protocol_hash:
        raise SystemExit("frozen A08 protocol hash mismatch")
    if sha(package / "test_audit_only_a08.py") != expected_test_hash:
        raise SystemExit("frozen A08 test hash mismatch")
    if a04_report.get("disposition") != "PASS_RAW_RECONCILIATION_ONLY":
        raise SystemExit("A04 disposition is not PASS_RAW_RECONCILIATION_ONLY")
    if sha(a04_report_path) != freeze_a05["a04_report_sha256"]:
        raise SystemExit("A04 report hash differs from prior freeze")
    paths = {name: package / f"results/FORMAL_A02/{name}/{name}.jsonl"
             for name in ("public", "oracle", "candidate")}
    hashes = {name: sha(path) for name, path in paths.items()}
    expected = freeze_a04["a02_artifact_sha256"]
    if any(hashes[name] != expected[name] for name in paths):
        raise SystemExit("A02 raw input hash differs from A04 freeze")
    if hashes != freeze_a08["a02_raw_sha256"]:
        raise SystemExit("A02 raw input hash differs from A08 freeze")
    if sha(a04_report_path) != freeze_a08["a04_report_sha256"]:
        raise SystemExit("A04 report hash differs from A08 freeze")
    public, oracle, candidate = (load_jsonl(paths[k]) for k in ("public", "oracle", "candidate"))
    structural = validate_structure(public, oracle, candidate)
    reconstruction = reconstruction_errors(public, candidate)
    score_result = score(public, oracle, candidate)
    mutations = mutation_controls(public, oracle, candidate)
    integrity_ok = not structural and not reconstruction and all(mutations.values())
    d = score_result["decision_checks"]
    score_pass = (d["coverage_at_least_50pct_each_in_model_profile"] and
                  d["in_model_interval_containment"] and
                  d["invalid_profile_terminal_interval_fail_closed"] and
                  all(d["strict_false_yield_improvement"].values()) and
                  d["both_methods_yield_on_an_eligible_hazard"] and
                  d["paired_lead_criterion"])
    no_value = (d["coverage_at_least_50pct_each_in_model_profile"] and
                d["in_model_interval_containment"] and
                d["invalid_profile_terminal_interval_fail_closed"] and
                (not all(d["strict_false_yield_improvement"].values()) or
                 not d["both_methods_yield_on_an_eligible_hazard"] or
                 not d["paired_lead_criterion"]))
    diagnostic = ("AUDIT_INTEGRITY_FAILURE" if not integrity_ok else
                  "INCREMENTAL_SIGNAL_ON_RETAINED_A02_RAW_UNSCORABLE" if score_pass else
                  "NO_INCREMENTAL_VALUE_SIGNAL_ON_RETAINED_A02_RAW" if no_value else
                  "MIXED_OR_INCOMPLETE_DIAGNOSTIC")
    result = {
        "schema": "issue-8157-a08-local-decision-audit-v1",
        "formal_a02_disposition_preserved": "FAIL_METHOD_UNSCORABLE",
        "a03_stop_preserved": "STOP_AUDITOR_RUNTIME_ERROR",
        "a05_stop_preserved": "STOP_BEFORE_INPUT_READ_ARGUMENT_ROOT_MISMATCH",
        "a06_stop_preserved": "STOP_BEFORE_INPUT_READ_FREEZE_SCHEMA_MISMATCH",
        "a07_stop_preserved": "AUDIT_INTEGRITY_FAILURE_MUTATION_CONTROLS",
        "diagnostic_disposition": diagnostic,
        "structural_errors": structural,
        "candidate_reconstruction_errors": reconstruction,
        **score_result,
        "mutation_controls": mutations,
        "integrity_pass": integrity_ok,
        "input_sha256": hashes,
        "a04_report_sha256": sha(a04_report_path),
        "a02_a03_a04_a05_a06_a07_auditor_invocations_in_a08": 0,
        "candidate_generator_container_runtime_invocations_in_a08": 0,
        "scope": "posthoc local score adjudication of immutable A02 synthetic raw; does not change its formal FAIL_METHOD",
    }
    pathlib.Path(out_path).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"diagnostic_disposition": diagnostic,
                      "structural_errors": len(structural),
                      "reconstruction_errors": len(reconstruction),
                      "thresholds_s": score_result["thresholds_s"]}, sort_keys=True))
    return 0 if integrity_ok else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
