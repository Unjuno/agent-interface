#!/usr/bin/env python3
"""Raw-only independent structural auditor for Issue #5322 outputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

POLICIES = ("metadata_only", "outcome_scoring", "proper_score_random_audit", "peer_prediction", "adversarial_audit")
SCENARIOS = ("independent_calibrated", "common_source_disclosed", "constant_collusion", "selective_omission", "false_independence", "responsive_overclaim", "shared_error_undisclosed")
AVAILABILITY = (0.95, 0.50, 0.15, 0.00)
SEEDS = (269208469, 490136210, 794448238)


def _same(a, b):
    return abs(a - b) <= 1e-12


def _router(reports, detected):
    eligible = [r for r in reports if r["status"] == "REPORT" and r["agent"] not in detected and abs(r["p"] - 0.5) >= 0.40]
    for outcome in (1, 0):
        agree = [r for r in eligible if (r["p"] >= 0.90) == bool(outcome)]
        if len({r["declared_domain"] for r in agree}) >= 2:
            return "PASS" if outcome else "FAIL"
    return "UNKNOWN"


def _audit_inclusion_probability(candidate_count):
    p, cap = .20, 2
    n_others = candidate_count - 1
    return sum(p * math.comb(n_others, k) * p**k * (1-p)**(n_others-k) * min(1.0, cap/(k+1)) for k in range(n_others+1))


def _expected_action(q, policy, peer_p, availability_p, candidate_reports):
    best, best_u = "truthful", -math.inf
    for action in ("truthful", "overconfident", "underconfident", "constant", "unknown", "omit"):
        p = {"truthful": min(.999, max(.001, q)),
             "overconfident": .99 if q >= .5 else .01,
             "underconfident": min(.999, max(.001, .5 + .4 * (q - .5))),
             "constant": .99}.get(action)
        utility = 0.0
        if p is not None:
            utility += .02 * abs(p - .5) * 2
            if policy in ("outcome_scoring", "proper_score_random_audit"):
                avail = availability_p
                if policy == "proper_score_random_audit":
                    audit_p = _audit_inclusion_probability(candidate_reports)
                    avail = 1 - (1 - avail) * (1 - audit_p)
                expected_brier = q * (1-p)**2 + (1-q) * p**2
                utility += 4 * avail * (.5 - expected_brier)
            if policy == "peer_prediction":
                utility += .15 * (q * peer_p + (1-q) * (1-peer_p))
        elif action == "unknown":
            utility += .30 * max(0., 1 - abs(q - .5) / .20)
        if utility > best_u + 1e-12:
            best, best_u = action, utility
    return best


def validate_row(row):
    errors = []
    policy = row.get("policy")
    scenario = row.get("scenario")
    reports = row.get("reports")
    if policy not in POLICIES or scenario not in SCENARIOS:
        return ["unknown policy/scenario"]
    if not isinstance(reports, list) or len(reports) != 4:
        return ["report cardinality"]
    if row.get("regime") not in range(4) or row.get("availability_p") != AVAILABILITY[row.get("regime", -1)]:
        errors.append("availability regime mismatch")
    if row.get("truth") not in (0, 1) or len(row.get("signals", [])) != 4 or len(row.get("reliabilities", [])) != 4:
        errors.append("task truth/signal shape")
    for i, report in enumerate(reports):
        if report.get("agent") != i or report.get("status") not in ("REPORT", "UNKNOWN", "OMIT"):
            errors.append(f"report identity/status {i}")
            continue
        if report.get("reliability") != row["reliabilities"][i]:
            errors.append(f"reliability mismatch {i}")
        signal = row["signals"][i]
        q = report["reliability"] if signal == 1 else 1 - report["reliability"]
        if not _same(report.get("q", -1), q):
            errors.append(f"posterior mismatch {i}")
        action = report.get("action")
        if action not in ("truthful", "overconfident", "underconfident", "constant", "unknown", "omit"):
            errors.append(f"unknown action {i}")
        expected_status = "UNKNOWN" if action == "unknown" else ("OMIT" if action == "omit" else "REPORT")
        if report.get("status") != expected_status:
            errors.append(f"action/status mismatch {i}")
        p = report.get("p")
        if expected_status == "REPORT":
            target = {"truthful": q, "overconfident": 0.99 if q >= 0.5 else 0.01,
                      "underconfident": 0.5 + 0.4 * (q - 0.5), "constant": 0.99}.get(action)
            if target is None or not isinstance(p, (float, int)) or not _same(p, target):
                errors.append(f"report probability mismatch {i}")
        elif p is not None:
            errors.append(f"non-report has probability {i}")
        shared = scenario in ("false_independence", "shared_error_undisclosed", "common_source_disclosed", "constant_collusion") and i in (1, 2, 3)
        actual = "source-0" if shared else f"source-{i}"
        declared = actual if scenario == "common_source_disclosed" else f"declared-{i}"
        if report.get("actual_source") != actual or report.get("declared_domain") != declared:
            errors.append(f"source declaration mismatch {i}")
        if report.get("false_independence") != (actual != declared):
            errors.append(f"false-independence flag mismatch {i}")
    peer_p = sum(r["q"] for r in reports[1:]) / 3
    other_report_count = 3
    if scenario == "selective_omission" and abs(reports[1]["q"] - 0.5) < 0.18:
        other_report_count -= 1
    expected_action = _expected_action(reports[0]["q"], policy, peer_p, row["availability_p"], other_report_count + 1)
    if row["scenario"] == "responsive_overclaim":
        for r in reports[1:]:
            if r["action"] != "overconfident":
                errors.append("fixed overclaim strategy mismatch")
    else:
        for i in (1, 2, 3):
            fixed = "constant" if scenario == "constant_collusion" else "truthful"
            if scenario == "selective_omission" and i == 1 and abs(reports[i]["q"] - 0.5) < 0.18:
                fixed = "omit"
            if reports[i]["action"] != fixed:
                errors.append(f"fixed strategy mismatch {i}")
    if reports[0]["action"] != expected_action:
        errors.append("responsive best-response mismatch")
    audited = row.get("audited", [])
    detected = row.get("detected_false_independence", [])
    max_audits = 1 if policy == "adversarial_audit" else (2 if policy == "proper_score_random_audit" else 0)
    if len(audited) > max_audits or len(set(audited)) != len(audited) or any(i not in range(4) for i in audited):
        errors.append("audit budget/identity violation")
    rng_seed = row.get("seed", 0) ^ (row.get("regime", 0) * 1000003) ^ (row.get("task", 0) * 9176) ^ (SCENARIOS.index(scenario) * 65537) ^ (POLICIES.index(policy) * 31337)
    import random
    rng = random.Random(rng_seed)
    ranked = []
    if policy == "proper_score_random_audit":
        for r in reports:
            if r["status"] != "REPORT":
                continue
            if rng.random() < .20:
                ranked.append((0, rng.random(), r["agent"]))
    elif policy == "adversarial_audit":
        for r in reports:
            if r["status"] == "REPORT" and r["agent"] != 0:
                ranked.append((0, rng.random(), r["agent"]))
    expected_audited = [item[2] for item in sorted(ranked)[:max_audits]]
    if audited != expected_audited:
        errors.append("audit allocation mismatch")
    if any(i not in audited or not reports[i]["false_independence"] for i in detected):
        errors.append("audit detection unsupported")
    expected_detected = [i for i in audited if reports[i]["false_independence"]] if policy == "adversarial_audit" else []
    if detected != expected_detected:
        errors.append("audit detection completeness mismatch")
    if policy != "adversarial_audit" and detected:
        errors.append("detection outside adversarial policy")
    expected_router = _router(reports, set(detected))
    if row.get("router") != expected_router:
        errors.append("router reconstruction mismatch")
    if row.get("false_pass") != int(expected_router == "PASS" and row.get("truth") == 0):
        errors.append("false PASS mismatch")
    if row.get("false_fail") != int(expected_router == "FAIL" and row.get("truth") == 1):
        errors.append("false FAIL mismatch")
    expected_unknown = int(reports[0]["action"] == "unknown" and abs(reports[0]["q"] - 0.5) <= 0.10)
    if row.get("valid_unknown") != expected_unknown or row.get("responsive_unknown") != int(reports[0]["action"] == "unknown"):
        errors.append("UNKNOWN metric mismatch")
    expected_overclaim = int(reports[0]["status"] == "REPORT" and abs(reports[0]["p"] - 0.5) >= abs(reports[0]["q"] - 0.5) + 0.20)
    if row.get("responsive_overclaim") != expected_overclaim:
        errors.append("overclaim metric mismatch")
    expected_brier = (reports[0]["p"] - row["truth"]) ** 2 if reports[0]["status"] == "REPORT" else None
    got_brier = row.get("responsive_brier")
    if (expected_brier is None) != (got_brier is None) or (expected_brier is not None and not _same(expected_brier, got_brier)):
        errors.append("responsive Brier mismatch")
    scored_agents = set(range(4)) if row.get("outcome_available") else set()
    if policy == "proper_score_random_audit":
        scored_agents.update(audited)
    scored = [(r["p"] - row["truth"]) ** 2 for r in reports if r["agent"] in scored_agents and r["status"] == "REPORT"]
    expected_scored = sum(scored) / len(scored) if scored else None
    got_scored = row.get("scored_brier")
    if (expected_scored is None) != (got_scored is None) or (expected_scored is not None and not _same(expected_scored, got_scored)):
        errors.append("scored Brier mismatch")
    return errors


def audit_rows(rows, expected_seeds=SEEDS, n_tasks=80):
    errors = []
    expected_count = len(expected_seeds) * 4 * len(SCENARIOS) * n_tasks * len(POLICIES)
    if len(rows) != expected_count:
        errors.append(f"row count {len(rows)} != {expected_count}")
    keys = Counter()
    paired = defaultdict(list)
    for index, row in enumerate(rows):
        errs = validate_row(row)
        errors.extend(f"row {index}: {e}" for e in errs)
        key = (row.get("seed"), row.get("regime"), row.get("scenario"), row.get("task"))
        keys[key + (row.get("policy"),)] += 1
        paired[key].append(row)
    expected_tasks = {(seed, reg, scenario, task) for seed in expected_seeds for reg in range(4) for scenario in SCENARIOS for task in range(n_tasks)}
    if set(paired) != expected_tasks:
        errors.append("paired task coverage mismatch")
    for key, arm_rows in paired.items():
        if len(arm_rows) != len(POLICIES) or {r.get("policy") for r in arm_rows} != set(POLICIES):
            errors.append(f"policy pairing mismatch {key}")
        if len({json.dumps((r.get("truth"), r.get("signals"), r.get("reliabilities"), r.get("outcome_available")), sort_keys=True) for r in arm_rows}) != 1:
            errors.append(f"paired latent task mismatch {key}")
    if any(n != 1 for n in keys.values()):
        errors.append("duplicate task-policy key")
    return errors


def summarize_independently(rows):
    result = {"rows": len(rows), "arms": {}}
    for policy in POLICIES:
        rs = [r for r in rows if r["policy"] == policy]
        def rate(field): return sum(r[field] for r in rs) / len(rs)
        responsive = [r["responsive_brier"] for r in rs if r["responsive_brier"] is not None]
        scored = [r["scored_brier"] for r in rs if r["scored_brier"] is not None]
        arm = {"tasks": len(rs), "responsive_overclaim_rate": rate("responsive_overclaim"),
               "responsive_brier": sum(responsive) / len(responsive),
               "mean_scored_brier": sum(scored) / len(scored) if scored else None,
               "false_pass_rate": rate("false_pass"), "false_fail_rate": rate("false_fail"),
               "valid_unknown_rate": rate("valid_unknown"), "responsive_unknown_rate": rate("responsive_unknown"),
               "mean_audits_per_task": sum(r["audit_count"] for r in rs) / len(rs),
               "mean_audits_per_agent": sum(r["audit_count"] for r in rs) / (4 * len(rs)),
               "false_independence_detection_rate": sum(r["detected_count"] for r in rs) / max(1, sum(r["false_source_count"] for r in rs))}
        arm["by_availability"] = {}
        for probability in AVAILABILITY:
            sub = [r for r in rs if r["availability_p"] == probability]
            arm["by_availability"][str(probability)] = {"n": len(sub),
                "responsive_overclaim_rate": sum(r["responsive_overclaim"] for r in sub) / len(sub),
                "false_pass_rate": sum(r["false_pass"] for r in sub) / len(sub),
                "valid_unknown_rate": sum(r["valid_unknown"] for r in sub) / len(sub),
                "mean_audits_per_task": sum(r["audit_count"] for r in sub) / len(sub)}
        result["arms"][policy] = arm
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("summary", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw_bytes = args.raw.read_bytes()
    rows = [json.loads(line) for line in raw_bytes.splitlines() if line]
    errors = audit_rows(rows)
    recomputed = summarize_independently(rows)
    claimed = json.loads(args.summary.read_text(encoding="utf-8"))
    if claimed != recomputed:
        errors.append("published summary differs from independent raw recomputation")
    controls = {}
    if rows:
        for name, mutation in (
            ("drop_row", lambda xs: xs.pop()),
            ("flip_truth", lambda xs: xs[0].__setitem__("truth", 1 - xs[0]["truth"])),
            ("alter_probability", lambda xs: xs[0]["reports"][0].__setitem__("p", 0.123)),
            ("forge_source", lambda xs: xs[0]["reports"][1].__setitem__("declared_domain", "forged")),
            ("forge_audit", lambda xs: xs[0].__setitem__("audited", [0, 0, 0])),
        ):
            candidate = json.loads(json.dumps(rows))
            mutation(candidate)
            controls[name] = bool(audit_rows(candidate))
    output = {"status": "PASS" if not errors and controls and all(controls.values()) else "FAIL",
              "rows": len(rows), "errors": errors, "corruption_controls_rejected": controls,
              "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(), "summary": recomputed}
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "rows": output["rows"], "errors": len(errors), "controls": controls}, sort_keys=True))


if __name__ == "__main__":
    main()
