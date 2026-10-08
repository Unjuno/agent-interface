#!/usr/bin/env python3
"""Deterministic offline evaluator for the GitHub-visible experiment-claim snapshot.

This checker is deliberately narrow. It does not query GitHub, infer semantic
similarity, acquire a distributed lock, or execute a research allocation.
"""
import json
import sys
from itertools import combinations
from pathlib import Path


def pair_reasons(a, b):
    reasons = []
    if a["task_id"] == b["task_id"]:
        reasons.append("task_id")
    if a["scope"] == b["scope"]:
        reasons.append("scope")
    if (
        a.get("successor")
        and a["successor"] == b.get("successor")
        and a.get("question_key")
        and a["question_key"] == b.get("question_key")
    ):
        reasons.append("semantic_successor")
    return reasons


def candidate_reasons(candidate, claims, consumed_ids, against_issue=None):
    reasons = []
    if candidate["task_id"] in consumed_ids:
        reasons.append("consumed_task_id")
    targets = claims
    if against_issue is not None:
        targets = [c for c in claims if c["issue"] == against_issue]
        if len(targets) != 1:
            raise ValueError(f"missing/ambiguous against_issue {against_issue}")
    for existing in targets:
        for reason in pair_reasons(candidate, existing):
            reasons.append(reason)
    return sorted(set(reasons))


def evaluate(snapshot):
    claims = snapshot["claims"]
    by_issue = {c["issue"]: c for c in claims}
    if len(by_issue) != len(claims):
        raise ValueError("duplicate issue identity in snapshot")

    consumed_ids = {x["task_id"] for x in snapshot["consumed_task_ids"]}
    active = [c for c in claims if c["state"] == "open" and c["category"] == "experiment"]
    active_pairs = []
    for left, right in combinations(active, 2):
        reasons = pair_reasons(left, right)
        if reasons:
            active_pairs.append({
                "issues": [left["issue"], right["issue"]],
                "reasons": reasons,
            })

    observed = []
    observed_ok = True
    for control in snapshot["observed_controls"]:
        if control["name"] == "recent_semantic_duplicate":
            left = by_issue[control["left_issue"]]
            right = by_issue[control["right_issue"]]
            reasons = pair_reasons(left, right)
            ok = control["expect_conflict"] == bool(reasons) and control["expect_reason"] in reasons
            observed.append({"name": control["name"], "reasons": reasons, "pass": ok})
        elif control["name"] == "current_distinct_active_set":
            selected = [by_issue[i] for i in control["issues"]]
            conflicts = []
            for left, right in combinations(selected, 2):
                reasons = pair_reasons(left, right)
                if reasons:
                    conflicts.append({"issues": [left["issue"], right["issue"]], "reasons": reasons})
            ok = len(conflicts) == control["expect_pairwise_conflicts"]
            observed.append({"name": control["name"], "conflicts": conflicts, "pass": ok})
        else:
            raise ValueError(f"unknown observed control {control['name']}")
        observed_ok = observed_ok and ok

    synthetic = []
    synthetic_ok = True
    for control in snapshot["synthetic_controls"]:
        reasons = candidate_reasons(
            control["candidate"],
            claims,
            consumed_ids,
            control.get("against_issue"),
        )
        actual_conflict = bool(reasons)
        ok = actual_conflict == control["expect_conflict"]
        if control.get("expect_reason") is not None:
            ok = ok and control["expect_reason"] in reasons
        synthetic.append({"name": control["name"], "reasons": reasons, "pass": ok})
        synthetic_ok = synthetic_ok and ok

    decision = (
        "PASS_SCOPED_PRE_FREEZE_CONFLICT_GATE"
        if observed_ok and synthetic_ok and not active_pairs
        else "FAIL_PRE_FREEZE_CONFLICT_GATE"
    )
    return {
        "schema": "formal_lease_conflict_gate_result_v1",
        "task": snapshot["task"],
        "publication_base": snapshot["publication_base"],
        "active_claim_issues": [c["issue"] for c in active],
        "active_pair_count": len(active) * (len(active) - 1) // 2,
        "active_conflicts": active_pairs,
        "observed_controls": observed,
        "synthetic_controls": synthetic,
        "observed_pass": observed_ok,
        "synthetic_pass": synthetic_ok,
        "decision": decision,
        "scope_limit": (
            "GitHub-visible structured metadata only; read-before-claim races, stale indexing, "
            "unpublished sessions and semantic paraphrase remain outside this gate."
        ),
    }


def main():
    root = Path(__file__).resolve().parent
    snapshot_path = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    result = evaluate(snapshot)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"] == "PASS_SCOPED_PRE_FREEZE_CONFLICT_GATE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
