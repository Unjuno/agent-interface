from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from candidate import run_cached_action_guard, EFFECT
from runner import run_experiment
from oracle import guarded_cache_reference, regime_at
from scenario import ACTION_TIMES_MS, HARD, AMBIG, Scenario, generate_scenarios

REQUIRED_DECISION = "PASS_DECISION_POLICY_ACTION_GUARD_SCOPED"


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_source_hashes(root: Path, freeze: dict) -> list[str]:
    errors = []
    for rel, expected in freeze["source_sha256"].items():
        actual = sha256_path(root / rel)
        if actual != expected:
            errors.append(f"source hash mismatch {rel}: {actual} != {expected}")
    return errors


def audit_result(result: dict) -> list[str]:
    errors = []
    if result.get("formal_invocations") != 1 or result.get("reruns") != 0:
        errors.append("formal invocation/rerun invariant failed")
    if result.get("authority_grants") != 0:
        errors.append("authority grants must remain zero")
    mm = result.get("candidate_oracle_mismatch", {})
    if mm.get("redecide_vs_oracle") != 0 or mm.get("guard_vs_oracle") != 0:
        errors.append("candidate/oracle mismatch")
    g = result["metrics"]["cached_action_guard"]
    s = result["metrics"]["cached_supervisor_only"]
    if g["hard_invalid_effects"] != 0:
        errors.append("guard admitted hard-invalid effect")
    if g["ambiguous_effects"] != 0:
        errors.append("guard admitted ambiguous effect")
    if s["hard_invalid_effects"] <= 0:
        errors.append("frozen discriminator absent")
    if result.get("pre_hard_valid_guard_reference_mismatch") != 0:
        errors.append("guard lost valid continuation before first hard invalidation")
    if result.get("decision") != REQUIRED_DECISION:
        errors.append(f"unexpected decision {result.get('decision')}")
    return errors


def mutation_controls() -> dict:
    s = next(generate_scenarios(1, 424242))
    controls = {}

    oracle = guarded_cache_reference(s)
    for name in ("remove_guard", "stale_sample_as_current", "ambiguous_is_valid"):
        mutant = [d.disposition for d in run_cached_action_guard(s, mutation=name)["decisions"]]
        controls[name] = {
            "detected": mutant != oracle,
            "mismatch_count": sum(a != b for a, b in zip(mutant, oracle)),
        }

    mismatch_s = Scenario(
        scenario_id=999999,
        ambiguous_start_ms=s.ambiguous_start_ms,
        ambiguous_end_ms=s.ambiguous_end_ms,
        transient_hard_start_ms=s.transient_hard_start_ms,
        transient_hard_end_ms=s.transient_hard_end_ms,
        persistent_hard_start_ms=s.persistent_hard_start_ms,
        cache_generation=7,
        current_generation=8,
    )
    oracle_mismatch = guarded_cache_reference(mismatch_s)
    mutant_generation = [d.disposition for d in run_cached_action_guard(mismatch_s, mutation="ignore_generation")["decisions"]]
    controls["ignore_generation"] = {
        "detected": mutant_generation != oracle_mismatch,
        "mismatch_count": sum(a != b for a, b in zip(mutant_generation, oracle_mismatch)),
    }

    # Copied/corrupted result control: make candidate/oracle counters look superficially clean
    # while overwriting guarded metrics with the unsafe supervisor-only arm. The independent
    # invariant audit must still reject the corruption from effect-state counts.
    copied = run_experiment(64, 424243)
    copied["metrics"]["cached_action_guard"] = copy.deepcopy(copied["metrics"]["cached_supervisor_only"])
    copied["candidate_oracle_mismatch"] = {"redecide_vs_oracle": 0, "guard_vs_oracle": 0}
    copied["decision"] = REQUIRED_DECISION
    copied_errors = audit_result(copied)
    controls["copied_supervisor_result_as_guard"] = {
        "detected": bool(copied_errors),
        "mismatch_count": len(copied_errors),
        "errors": copied_errors,
    }
    return controls


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--result", type=Path, required=True)
    p.add_argument("--freeze", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    result = json.loads(args.result.read_text(encoding="utf-8"))
    errors = verify_source_hashes(args.root, freeze)
    errors.extend(audit_result(result))
    controls = mutation_controls()
    for name, c in controls.items():
        if not c["detected"]:
            errors.append(f"mutation control not detected: {name}")

    audit = {
        "task": result.get("task"),
        "result_sha256": sha256_path(args.result),
        "source_integrity": not any(e.startswith("source hash mismatch") for e in errors),
        "mutation_controls": controls,
        "errors": errors,
        "pass": not errors,
    }
    args.out.write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pass": audit["pass"], "errors": errors, "result_sha256": audit["result_sha256"]}, sort_keys=True))
    raise SystemExit(0 if audit["pass"] else 1)


if __name__ == "__main__":
    main()
