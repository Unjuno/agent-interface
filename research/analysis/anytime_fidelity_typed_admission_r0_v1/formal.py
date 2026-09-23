from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

from candidate import BY_NAME, CATALOG, CURRENT, POLICIES, ROLES, State, TEMPORAL, VERIFY, feasible, safe_variant


def canonical_sha(obj) -> str:
    data = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def all_required_sets():
    ordered = [CURRENT, TEMPORAL, VERIFY]
    for bits in itertools.product([False, True], repeat=3):
        required = frozenset(role for role, keep in zip(ordered, bits) if keep)
        if required:
            yield required


def all_states():
    for slack in range(0, 11):
        for reserve in range(0, 5):
            for required in all_required_sets():
                yield State(slack=slack, reserve=reserve, required=required)


def classify(state: State, chosen_name):
    exists = feasible(state)
    if chosen_name is None:
        return {
            "deadline_violation": False,
            "evidence_violation": False,
            "unsafe": False,
            "false_defer": exists,
        }
    v = BY_NAME[chosen_name]
    deadline = v.cost + state.reserve > state.slack
    evidence = not state.required.issubset(v.evidence)
    return {
        "deadline_violation": deadline,
        "evidence_violation": evidence,
        "unsafe": deadline or evidence,
        "false_defer": False,
    }


def run(out_dir: Path):
    rows = []
    counts = {
        name: {
            "selected": {v.name: 0 for v in CATALOG} | {"DEFER": 0},
            "deadline_violation": 0,
            "evidence_violation": 0,
            "unsafe": 0,
            "false_defer": 0,
        }
        for name in POLICIES
    }
    temporal_false_defer_witness = None
    verify_false_defer_witness = None

    for index, state in enumerate(all_states()):
        decisions = {}
        metrics = {}
        for name, fn in POLICIES.items():
            chosen = fn(state)
            decision_name = chosen if chosen is not None else "DEFER"
            decisions[name] = decision_name
            c = classify(state, chosen)
            metrics[name] = c
            counts[name]["selected"][decision_name] += 1
            for k in ["deadline_violation", "evidence_violation", "unsafe", "false_defer"]:
                counts[name][k] += int(c[k])

        row = {
            "index": index,
            "slack": state.slack,
            "reserve": state.reserve,
            "required": sorted(state.required),
            "feasible": feasible(state),
            "decisions": decisions,
            "metrics": metrics,
        }
        rows.append(row)

        cur = metrics["CURRENT_ONLY"]
        if cur["false_defer"]:
            if TEMPORAL in state.required and temporal_false_defer_witness is None:
                temporal_false_defer_witness = row
            if VERIFY in state.required and verify_false_defer_witness is None:
                verify_false_defer_witness = row

    catalog = [
        {"name": v.name, "cost": v.cost, "evidence": sorted(v.evidence), "rank": v.rank}
        for v in CATALOG
    ]
    t = BY_NAME["TEMPORAL"]
    v = BY_NAME["VERIFY"]
    incomparable = (
        t.cost == v.cost
        and not t.evidence.issubset(v.evidence)
        and not v.evidence.issubset(t.evidence)
    )

    pass_expected = (
        len(rows) == 385
        and counts["TYPED_RESERVED"]["unsafe"] == 0
        and counts["TYPED_RESERVED"]["false_defer"] == 0
        and counts["SCALAR_RAW_HIGHEST"]["deadline_violation"] > 0
        and counts["SCALAR_RAW_HIGHEST"]["evidence_violation"] > 0
        and counts["SCALAR_RESERVED_HIGHEST"]["deadline_violation"] == 0
        and counts["SCALAR_RESERVED_HIGHEST"]["evidence_violation"] > 0
        and counts["SCALAR_RESERVED_POSTCHECK"]["unsafe"] == 0
        and counts["SCALAR_RESERVED_POSTCHECK"]["false_defer"] > 0
        and counts["CURRENT_ONLY"]["unsafe"] == 0
        and temporal_false_defer_witness is not None
        and verify_false_defer_witness is not None
        and incomparable
    )

    result = {
        "task": "ANYTIME-FIDELITY-TYPED-ADMISSION-R0-20260919-001",
        "state_count": len(rows),
        "catalog": catalog,
        "policy_counts": counts,
        "temporal_verify_equal_cost_incomparable": incomparable,
        "temporal_only_evidence_witness": sorted(t.evidence - v.evidence),
        "verify_only_evidence_witness": sorted(v.evidence - t.evidence),
        "current_only_temporal_false_defer_witness": temporal_false_defer_witness,
        "current_only_verify_false_defer_witness": verify_false_defer_witness,
        "rows_sha256": canonical_sha(rows),
        "decision": "PASS_ANYTIME_FIDELITY_TYPED_ADMISSION_SCOPED" if pass_expected else "HOLD_OR_FAIL",
    }
    result["summary_core_sha256"] = canonical_sha({k: val for k, val in result.items() if k != "summary_core_sha256"})

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ROWS.json").write_text(json.dumps(rows, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (out_dir / "RESULT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if pass_expected else 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    run(Path(args.out))


if __name__ == "__main__":
    main()
