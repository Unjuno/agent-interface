"""Independent audit of T2 result; this module never imports/runs T2 code."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
T2 = REPO / "research/analysis/backward_observable_guards_6256_comparator_t2_20261002"
T1 = REPO / "research/analysis/backward_observable_guards_6256_stale_generation_t1_20261002"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_safe(outcome, bound):
    return (outcome["effect"] == "exact_target_saved" and not outcome["forbidden_prefix"]
            and outcome["release"] == "empty_verified" and outcome["terminated"]
            and outcome["steps"] <= bound)


def audit(expected):
    paths = {
        "t2_code": T2 / "comparator.py",
        "t2_tests": T2 / "test_comparator.py",
        "t2_raw": T2 / "results/t2-01/audit_raw.json",
        "model": T1 / "inputs/MODEL.json",
        "candidate": T1 / "inputs/results/t0-01/candidate_raw.json",
        "parent_audit": T1 / "inputs/results/t0-01/audit_raw.json",
    }
    hashes = {k: digest(v) for k, v in paths.items()}
    errors = ["hash:" + k for k in expected if hashes[k] != expected[k]]
    state_by_id = {s["id"]: s for s in json.loads(paths["model"].read_text(encoding="utf-8"))["states"]}
    model = json.loads(paths["model"].read_text(encoding="utf-8"))
    candidate = json.loads(paths["candidate"].read_text(encoding="utf-8"))
    raw = json.loads(paths["t2_raw"].read_text(encoding="utf-8"))
    pairs = {(s["id"], o["id"]): o for s in model["states"] for o in s["outcomes"]}
    row_pairs = {(r["state_id"], r["outcome"]["id"]): r for r in candidate["outcome_rows"]}
    exact = {sid for sid, s in state_by_id.items() if s["outcomes"] and all(exact_safe(o, model["horizon_steps"]) for o in s["outcomes"])}
    forward = {sid for sid in state_by_id if all(row_pairs[(sid, oid)]["passes_total_correctness"] for (row_sid, oid) in pairs if row_sid == sid)}
    simple, committed = state_by_id["ready_simple"], state_by_id["already_committed"]
    checks = {
        "state_count_10": len(state_by_id) == 10,
        "outcome_count_13": len(pairs) == 13,
        "candidate_rows_cover_every_pair": set(row_pairs) == set(pairs),
        "independent_preimage_equals_candidate": exact == set(candidate["preimage_state_ids"]),
        "complete_forward_rows_equal_preimage": forward == exact,
        "pixel_pair_same_value_mixed_labels": simple["cues"]["pixels"] == committed["cues"]["pixels"] and ((simple["id"] in exact) != (committed["id"] in exact)),
        "t2_retains_both_assertion_failures": set(raw["errors"]) == {"proposal_local_failed_to_illustrate_incompleteness", "pixel_alias_not_unknown"},
        "cost_one_illustrative_unmeasured_row": raw["observation"]["cost_rows_count"] == 1 and "not measured" in raw["observation"]["costs"],
    }
    errors.extend(k for k, v in checks.items() if not v)
    return {"decision": "PASS_T2_FALSE_STOP_RECONCILED_SCOPED" if not errors else "HOLD_OR_FAIL", "errors": errors, "hashes": hashes, "states": len(state_by_id), "outcomes": len(pairs), "preimage": sorted(exact), "forward_admitted": sorted(forward), "pixel_pair": {"ids": [simple["id"], committed["id"]], "pixels": simple["cues"]["pixels"], "labels": {simple["id"]: simple["id"] in exact, committed["id"]: committed["id"] in exact}}, "checks": checks, "t2_decision_unchanged": raw["decision"], "scope": "finite synthetic authored model only; cost unmeasured; no T2 rerun"}


if __name__ == "__main__":
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    print(json.dumps(audit(freeze["input_sha256"]), indent=2, sort_keys=True))
