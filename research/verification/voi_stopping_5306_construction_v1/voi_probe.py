"""Deterministic construction probe for Issue #5306; not a formal allocation."""
from __future__ import annotations

import json
from pathlib import Path


CASES = [
    # Truth is a latent hazard bit. Evidence labels are deliberately explicit.
    {"id": "train-safe-redundant", "split": "plan", "hazard": 0, "ambiguous": 0, "stale": 0, "gap": 0, "deadline": 9, "checks": {"M": [0, 0, 1], "X": [0, 0, 4], "Y": [0, 0, 4]}},
    {"id": "train-hazard-critical", "split": "plan", "hazard": 1, "ambiguous": 1, "stale": 0, "gap": 0, "deadline": 9, "checks": {"M": [0, 0, 1], "X": [1, 1, 4], "Y": [1, 1, 4]}},
    {"id": "train-ambiguous-informative", "split": "plan", "hazard": 0, "ambiguous": 1, "stale": 0, "gap": 0, "deadline": 8, "checks": {"M": [0, 0, 1], "X": [0, 0, 2], "Y": [0, 0, 5]}},
    {"id": "heldout-safe-after-cheap", "split": "heldout", "hazard": 0, "ambiguous": 1, "stale": 0, "gap": 0, "deadline": 6, "checks": {"M": [0, 0, 1], "X": [0, 0, 2], "Y": [0, 0, 5]}},
    {"id": "heldout-hazard-after-cheap", "split": "heldout", "hazard": 1, "ambiguous": 1, "stale": 0, "gap": 0, "deadline": 6, "checks": {"M": [0, 0, 1], "X": [1, 1, 2], "Y": [1, 1, 5]}},
    {"id": "heldout-correlated-duplicate", "split": "heldout", "hazard": 1, "ambiguous": 1, "stale": 0, "gap": 0, "deadline": 8, "checks": {"M": [0, 0, 1], "X": [1, 1, 2], "Y": [1, 1, 2], "correlated": 1}},
    {"id": "heldout-stale", "split": "heldout", "hazard": 0, "ambiguous": 1, "stale": 1, "gap": 0, "deadline": 8, "checks": {"M": [0, 0, 1], "X": [0, 0, 2], "Y": [0, 0, 3]}},
    {"id": "heldout-ontology-gap", "split": "heldout", "hazard": 0, "ambiguous": 1, "stale": 0, "gap": 1, "deadline": 8, "checks": {"M": [0, 0, 1], "X": [0, 0, 2], "Y": [0, 0, 3]}},
    {"id": "heldout-deadline-infeasible", "split": "heldout", "hazard": 1, "ambiguous": 1, "stale": 0, "gap": 0, "deadline": 1, "checks": {"M": [1, 1, 2], "X": [1, 1, 3], "Y": [1, 1, 4]}},
]

FALSE_ALLOW = 100
FALSE_BLOCK = 5
UNKNOWN_LOSS = 12


def disposition(case: dict, observed: dict[str, int], stale: bool, gap: bool) -> str:
    """Independent hard reducer: mandatory evidence and ontology/freshness dominate."""
    if stale or gap or "M" not in observed:
        return "YIELD"
    if any(name != "M" and v == 1 for name, v in observed.items()):
        return "BLOCK"
    return "ALLOW"


def loss(case: dict, disp: str) -> int:
    if disp == "YIELD":
        return UNKNOWN_LOSS
    if disp == "ALLOW" and case["hazard"]:
        return FALSE_ALLOW
    if disp == "BLOCK" and not case["hazard"]:
        return FALSE_BLOCK
    return 0


def choose_checks(case: dict, policy: str) -> list[str]:
    if case["stale"] or case["gap"]:
        return []
    feasible = [name for name, values in case["checks"].items()
                if name in {"M", "X", "Y"} and values[2] <= case["deadline"]]
    if "M" not in feasible:
        return []
    if policy == "FIXED":
        return feasible
    if policy == "SELECTIVE":
        # Frozen threshold baseline observes ambiguity, then runs its full two-check bundle.
        return [name for name in ("M", "X", "Y") if name in feasible] if case["ambiguous"] else ["M"]
    # Planning rates are frozen separately: for an ambiguous item X has expected avoided loss 18;
    # Y has expected avoided loss 8. Select a feasible check only when its frozen net value > 0.
    selected = ["M"]
    if "X" in feasible and 18 - 2 > 0:
        selected.append("X")
    # Once X has been observed the fixed planning model assigns Y zero marginal value.
    # Do not add Y even when feasible: duplicates are also explicitly correlated in one held-out case.
    return selected


def run() -> dict:
    rows = []
    for case in CASES:
        for policy in ("FIXED", "SELECTIVE", "VOI"):
            checks = choose_checks(case, policy)
            observed = {}
            realized_checks = []
            # Sequential replay: after each check, the VOI policy recomputes whether any
            # unresolved information remains. Here X is contractually decisive in the
            # frozen toy model; held-out distribution validity is not asserted.
            for name in checks:
                observed[name] = case["checks"][name][0]
                realized_checks.append(name)
                if policy == "VOI" and name == "X" and observed[name] in (0, 1):
                    break
            checks = realized_checks
            stale = bool(case["stale"])
            gap = bool(case["gap"])
            disp = disposition(case, observed, stale, gap)
            rows.append({"case": case["id"], "split": case["split"], "policy": policy,
                         "checks": checks, "cost": sum(case["checks"][n][2] for n in checks),
                         "disposition": disp, "loss": loss(case, disp),
                         "hazard": case["hazard"], "stale": stale, "gap": gap,
                         "deadline": case["deadline"]})
    summary = {}
    for split in ("plan", "heldout"):
        summary[split] = {}
        for policy in ("FIXED", "SELECTIVE", "VOI"):
            rs = [r for r in rows if r["split"] == split and r["policy"] == policy]
            summary[split][policy] = {"calls": sum(len(r["checks"]) for r in rs),
                                      "cost": sum(r["cost"] for r in rs),
                                      "loss": sum(r["loss"] for r in rs),
                                      "false_allows": sum(r["disposition"] == "ALLOW" and r["hazard"] for r in rs),
                                      "yields_stale_or_gap": sum(r["disposition"] == "YIELD" and (r["stale"] or r["gap"]) for r in rs)}
    return {"schema": "voi-construction-probe-v1", "rows": rows, "summary": summary}


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
