#!/usr/bin/env python3
"""Deterministic, theorem-free simulator for GitHub Issue #5322."""
from __future__ import annotations

import argparse
import hashlib
import math
import json
import math
import random
from pathlib import Path

POLICIES = ("metadata_only", "outcome_scoring", "proper_score_random_audit", "peer_prediction", "adversarial_audit")
SCENARIOS = ("independent_calibrated", "common_source_disclosed", "constant_collusion", "selective_omission", "false_independence", "responsive_overclaim", "shared_error_undisclosed")
AVAILABILITY = (0.95, 0.50, 0.15, 0.00)
SEEDS = (269208469, 490136210, 794448238)
N_TASKS = 80
AUDIT_BUDGET = 2
RANDOM_AUDIT_P = 0.20


def _clamp(p: float) -> float:
    return min(0.999, max(0.001, p))


def _binary(rng: random.Random, p: float) -> int:
    return int(rng.random() < p)


def _expected_brier(q: float, p: float) -> float:
    return q * (1 - p) ** 2 + (1 - q) * p ** 2


def _random_audit_inclusion_probability(candidate_count: int) -> float:
    """Marginal selection probability after Bernoulli(.20) sampling and cap=2."""
    n_others = candidate_count - 1
    probability = 0.0
    for k in range(n_others + 1):
        mass = math.comb(n_others, k) * RANDOM_AUDIT_P**k * (1 - RANDOM_AUDIT_P)**(n_others - k)
        probability += RANDOM_AUDIT_P * mass * min(1.0, AUDIT_BUDGET / (k + 1))
    return probability


def _router(reports: list[dict], audited_bad: set[int] | None = None) -> str:
    audited_bad = audited_bad or set()
    eligible = [r for r in reports if r["status"] == "REPORT" and r["agent"] not in audited_bad and abs(r["p"] - 0.5) >= 0.40]
    for outcome in (1, 0):
        agreeing = [r for r in eligible if (r["p"] >= 0.90) == bool(outcome)]
        if len({r["declared_domain"] for r in agreeing}) >= 2:
            return "PASS" if outcome else "FAIL"
    return "UNKNOWN"


def _base_tasks(seeds=SEEDS, n_tasks=N_TASKS) -> list[dict]:
    tasks = []
    for seed in seeds:
        rng = random.Random(seed)
        for regime, availability_p in enumerate(AVAILABILITY):
            for scenario in SCENARIOS:
                for index in range(n_tasks):
                    truth = _binary(rng, 0.5)
                    reliabilities = [rng.uniform(0.55, 0.95) for _ in range(4)]
                    shared = scenario in ("false_independence", "shared_error_undisclosed", "common_source_disclosed", "constant_collusion")
                    common_correct = _binary(rng, sum(reliabilities[1:]) / 3) if shared else None
                    signals = []
                    for agent, reliability in enumerate(reliabilities):
                        if shared and agent in (1, 2, 3):
                            sig = truth if common_correct else 1 - truth
                        else:
                            sig = truth if _binary(rng, reliability) else 1 - truth
                        signals.append(sig)
                    tasks.append({"seed": seed, "regime": regime, "availability_p": availability_p, "scenario": scenario, "index": index,
                                  "truth": truth, "reliabilities": reliabilities, "signals": signals,
                                  "outcome_available": _binary(rng, availability_p), "source_shared": shared})
    return tasks


def _reported_p(q: float, action: str) -> tuple[str, float | None]:
    if action == "truthful": return "REPORT", _clamp(q)
    if action == "overconfident": return "REPORT", 0.99 if q >= 0.5 else 0.01
    if action == "underconfident": return "REPORT", _clamp(0.5 + 0.4 * (q - 0.5))
    if action == "constant": return "REPORT", 0.99
    if action == "unknown": return "UNKNOWN", None
    return "OMIT", None


def _best_action(q: float, policy: str, peer_p: float, availability_p: float, candidate_reports: int) -> str:
    actions = ("truthful", "overconfident", "underconfident", "constant", "unknown", "omit")
    best, best_u = "truthful", -math.inf
    for action in actions:
        status, p = _reported_p(q, action)
        utility = 0.0
        if status == "REPORT":
            utility += 0.02 * abs(p - 0.5) * 2
            if policy in ("outcome_scoring", "proper_score_random_audit"):
                score_prob = availability_p
                if policy == "proper_score_random_audit":
                    audit_p = _random_audit_inclusion_probability(candidate_reports)
                    score_prob = 1 - (1 - score_prob) * (1 - audit_p)
                utility += 4.0 * score_prob * (0.5 - _expected_brier(q, p))
            if policy == "peer_prediction":
                utility += 0.15 * (q * peer_p + (1 - q) * (1 - peer_p))
        elif status == "UNKNOWN":
            utility += 0.30 * max(0.0, 1 - abs(q - 0.5) / 0.20)
        # Stable tie break keeps truthful first; omission is costless but not rewarded.
        if utility > best_u + 1e-12:
            best, best_u = action, utility
    return best


def _make_reports(task: dict, policy: str) -> tuple[list[dict], int]:
    truth, scenario = task["truth"], task["scenario"]
    reports = []
    # Agent 0 is the responsive verifier; the peer arm's expected peer signal is
    # the precommitted mean of the three peer posteriors, not their outcomes.
    peer_ps = []
    for i, (sig, rel) in enumerate(zip(task["signals"], task["reliabilities"])):
        q = rel if sig == 1 else 1 - rel
        peer_ps.append(q)
    peer_p = sum(peer_ps[1:]) / 3
    other_report_count = 3
    if scenario == "selective_omission" and abs(peer_ps[1] - 0.5) < 0.18:
        other_report_count -= 1
    for i, (sig, rel) in enumerate(zip(task["signals"], task["reliabilities"])):
        q = rel if sig == 1 else 1 - rel
        actual = "source-0" if task["source_shared"] and i in (1, 2, 3) else f"source-{i}"
        declared = actual if scenario == "common_source_disclosed" else f"declared-{i}"
        false_independence = actual != declared
        action = _best_action(q, policy, peer_p, task["availability_p"], other_report_count + 1) if i == 0 else "truthful"
        if i > 0:
            if scenario == "constant_collusion": action = "constant"
            elif scenario == "selective_omission" and i == 1 and abs(q - 0.5) < 0.18: action = "omit"
            elif scenario == "responsive_overclaim": action = "overconfident"
        status, p = _reported_p(q, action)
        reports.append({"agent": i, "status": status, "p": p, "actual_source": actual,
                        "declared_domain": declared, "false_independence": false_independence,
                        "action": action, "q": q, "reliability": rel})
    return reports, sum(r["false_independence"] for r in reports)


def _audit(task: dict, reports: list[dict], policy: str) -> tuple[list[int], list[int]]:
    rng = random.Random(task["seed"] ^ (task["regime"] * 1000003) ^ (task["index"] * 9176) ^ (SCENARIOS.index(task["scenario"]) * 65537) ^ (POLICIES.index(policy) * 31337))
    candidates = [r for r in reports if r["status"] == "REPORT"]
    ranked = []
    selected = []
    for r in candidates:
        if policy == "proper_score_random_audit":
            if rng.random() >= RANDOM_AUDIT_P:
                continue
            priority = 0
        elif policy == "adversarial_audit":
            # Select a peer reporter without access to the hidden source truth;
            # the sampled source claim is then checked against the audit oracle.
            if r["agent"] == 0:
                continue
            priority = 0
        else:
            continue
        ranked.append((priority, rng.random(), r["agent"]))
    # The adversarial policy takes at most one peer report per task, so the
    # preregistered <=0.25 sampled-reports-per-agent cost bound is attainable.
    cap = 1 if policy == "adversarial_audit" else AUDIT_BUDGET
    audited = [x[2] for x in sorted(ranked)[:cap]]
    detected = [i for i in audited if reports[i]["false_independence"]] if policy == "adversarial_audit" else []
    return audited, detected


def run(seeds=SEEDS, n_tasks=N_TASKS) -> list[dict]:
    rows = []
    for task in _base_tasks(seeds, n_tasks):
        for policy in POLICIES:
            reports, false_sources = _make_reports(task, policy)
            audited, detected = _audit(task, reports, policy)
            outcome_observed = bool(task["outcome_available"] or (audited and policy == "proper_score_random_audit"))
            # Outcome scoring only uses naturally available outcomes; audit arms
            # additionally reveal truth for sampled reports after commitment.
            scored_agents = set(range(4)) if task["outcome_available"] else set()
            if policy == "proper_score_random_audit":
                scored_agents.update(audited)
            overclaim = int(reports[0]["status"] == "REPORT" and abs(reports[0]["p"] - 0.5) >= abs(reports[0]["q"] - 0.5) + 0.20)
            brier_values = [(r["p"] - task["truth"]) ** 2 for r in reports if r["agent"] in scored_agents and r["status"] == "REPORT"]
            router = _router(reports, set(detected))
            false_pass = int(router == "PASS" and task["truth"] == 0)
            false_fail = int(router == "FAIL" and task["truth"] == 1)
            valid_unknown = int(reports[0]["action"] == "unknown" and abs(reports[0]["q"] - 0.5) <= 0.10)
            rows.append({"seed": task["seed"], "regime": task["regime"], "availability_p": task["availability_p"],
                         "scenario": task["scenario"], "task": task["index"], "policy": policy,
                         "truth": task["truth"], "signals": task["signals"], "reliabilities": task["reliabilities"],
                         "outcome_available": task["outcome_available"], "reports": reports, "audited": audited,
                         "detected_false_independence": detected, "router": router, "false_pass": false_pass,
                         "false_fail": false_fail, "valid_unknown": valid_unknown, "responsive_unknown": int(reports[0]["action"] == "unknown"), "responsive_overclaim": overclaim,
                         "responsive_brier": (reports[0]["p"] - task["truth"]) ** 2 if reports[0]["status"] == "REPORT" else None,
                         "scored_brier": sum(brier_values) / len(brier_values) if brier_values else None,
                         "audit_count": len(audited), "false_source_count": false_sources,
                         "detected_count": len(detected), "outcome_observed": outcome_observed})
    return rows


def summarize(rows: list[dict]) -> dict:
    summary = {"rows": len(rows), "arms": {}}
    for policy in POLICIES:
        rs = [r for r in rows if r["policy"] == policy]
        valid_scores = [r["scored_brier"] for r in rs if r["scored_brier"] is not None]
        responsive_briers = [r["responsive_brier"] for r in rs if r["responsive_brier"] is not None]
        base = {"tasks": len(rs), "responsive_overclaim_rate": sum(r["responsive_overclaim"] for r in rs) / len(rs),
                "responsive_brier": sum(responsive_briers) / len(responsive_briers),
                "mean_scored_brier": sum(valid_scores) / len(valid_scores) if valid_scores else None,
                "false_pass_rate": sum(r["false_pass"] for r in rs) / len(rs),
                "false_fail_rate": sum(r["false_fail"] for r in rs) / len(rs),
                "valid_unknown_rate": sum(r["valid_unknown"] for r in rs) / len(rs),
                "responsive_unknown_rate": sum(r["responsive_unknown"] for r in rs) / len(rs),
                "mean_audits_per_task": sum(r["audit_count"] for r in rs) / len(rs),
                "mean_audits_per_agent": sum(r["audit_count"] for r in rs) / (4 * len(rs)),
                "mean_audits_per_agent": sum(r["audit_count"] for r in rs) / (4 * len(rs)),
                "false_independence_detection_rate": sum(r["detected_count"] for r in rs) / max(1, sum(r["false_source_count"] for r in rs))}
        base["by_availability"] = {}
        for probability in AVAILABILITY:
            sub = [r for r in rs if r["availability_p"] == probability]
            base["by_availability"][str(probability)] = {
                "n": len(sub), "responsive_overclaim_rate": sum(r["responsive_overclaim"] for r in sub) / len(sub),
                "false_pass_rate": sum(r["false_pass"] for r in sub) / len(sub),
                "valid_unknown_rate": sum(r["valid_unknown"] for r in sub) / len(sub),
                "mean_audits_per_task": sum(r["audit_count"] for r in sub) / len(sub)}
        summary["arms"][policy] = base
    return summary


def write_outputs(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    rows = run()
    raw_path = output / "raw.jsonl"
    with raw_path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    (output / "summary.json").write_text(json.dumps(summarize(rows), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    (output / "raw.sha256").write_text(f"{digest}  raw.jsonl\n", encoding="ascii")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_outputs(args.output)


if __name__ == "__main__":
    main()
