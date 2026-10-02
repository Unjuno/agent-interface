"""Independent audit-only successor for the missing stale-generation mutation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


EXPECTED = {
    "MODEL.json": "274c4f7de76f0c68738cdb73d3683e3dc57f570ccecc6f4b67b4adc01060958d",
    "candidate_raw.json": "266f6df83f0a824bf437ce1bb16fda0cc28abf046b4c57dd6428f727170078d4",
    "audit_raw.json": "cb30cc5c2a580410c8b3eaac09fe1f8731a5c7ab87d8322e75988fb1cb11fe8f",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def total_correct(outcome: dict, model: dict) -> bool:
    return bool(
        outcome.get("terminated") is True
        and isinstance(outcome.get("steps"), int)
        and outcome["steps"] <= model["horizon_steps"]
        and outcome.get("effect") == model["required_effect"]
        and not any(tag in model["forbidden_prefix_tags"] for tag in outcome.get("forbidden_prefix", []))
        and outcome.get("release") == model["required_release"]
    )


def universal_preimage(model: dict) -> set[str]:
    result = set()
    for state in model["states"]:
        outcomes = state.get("outcomes", [])
        if outcomes and all(total_correct(outcome, model) for outcome in outcomes):
            result.add(state["id"])
    return result


def matches_exact_guard(state: dict, safe_reference: dict, omit_generation: bool = False) -> bool:
    for cue, expected in safe_reference["cues"].items():
        if omit_generation and cue == "generation_fresh":
            continue
        if state["cues"].get(cue) != expected:
            return False
    return True


def audit(model: dict, candidate: dict, prior_audit: dict, input_hashes: dict[str, str]) -> dict:
    errors: list[str] = []
    for name, expected in EXPECTED.items():
        if input_hashes.get(name) != expected:
            errors.append(f"INPUT_SHA256_MISMATCH:{name}")

    states = model.get("states", [])
    preimage = universal_preimage(model)
    if len(states) != 10 or sum(len(s.get("outcomes", [])) for s in states) != 13:
        errors.append("FROZEN_ROW_COUNTS_MISMATCH")
    if sorted(preimage) != candidate.get("preimage_state_ids"):
        errors.append("INDEPENDENT_PREIMAGE_MISMATCH")
    if candidate.get("state_count") != len(states) or candidate.get("outcome_count") != 13:
        errors.append("CANDIDATE_COUNTS_MISMATCH")
    candidate_rows = candidate.get("outcome_rows", [])
    expected_rows = [
        (state["id"], outcome, total_correct(outcome, model))
        for state in states for outcome in state.get("outcomes", [])
    ]
    if len(candidate_rows) != len(expected_rows):
        errors.append("CANDIDATE_OUTCOME_ROW_COUNT_MISMATCH")
    else:
        for actual, (state_id, outcome, accepted) in zip(candidate_rows, expected_rows):
            if (
                actual.get("state_id") != state_id
                or actual.get("outcome") != outcome
                or actual.get("passes_total_correctness") is not accepted
            ):
                errors.append(f"CANDIDATE_OUTCOME_ROW_MISMATCH:{state_id}:{outcome.get('id')}")
    if prior_audit.get("decision") != "PASS_METHOD_SCOPED" or prior_audit.get("errors") != []:
        errors.append("PARENT_AUDIT_RECEIPT_MISMATCH")

    prior_mutations = prior_audit.get("mutation_controls", {})
    prior_mutation_names = {
        "existential_success_accepts_unreliable_state",
        "drop_release_gate_accepts_release_blocked",
        "drop_termination_gate_accepts_late_completion",
        "pixels_only_merges_ready_and_duplicate",
        "drop_forbidden_prefix_accepts_duplicate",
    }
    if set(prior_mutations) != prior_mutation_names or not all(prior_mutations.values()):
        errors.append("PARENT_MUTATION_RECEIPTS_MISMATCH")

    by_id = {s["id"]: s for s in states}
    unreliable = by_id["unreliable_effect_contract"]["outcomes"]
    duplicate = by_id["already_committed"]["outcomes"]
    release_blocked = by_id["release_blocked"]["outcomes"]
    late = by_id["late_completion"]["outcomes"]
    visible = [s for s in states if s["cues"]["pixels"] == "save_visible"]

    mutants = {
        "existential_success": {
            "counterexample_found": any(total_correct(o, model) for o in unreliable)
            and not all(total_correct(o, model) for o in unreliable),
            "unsafe_state_ids": ["unreliable_effect_contract"],
        },
        "drop_forbidden_prefix": {
            "counterexample_found": all(
                o.get("effect") == model["required_effect"]
                and o.get("steps", model["horizon_steps"] + 1) <= model["horizon_steps"]
                and o.get("terminated") is True
                and o.get("release") == model["required_release"]
                for o in duplicate
            ) and "already_committed" not in preimage,
            "unsafe_state_ids": ["already_committed"],
        },
        "pixels_only_equivalence": {
            "counterexample_found": len({s["id"] in preimage for s in visible}) > 1,
            "unsafe_state_ids": ["already_committed"],
        },
        "drop_release": {
            "counterexample_found": all(
                o.get("effect") == model["required_effect"]
                and o.get("steps", model["horizon_steps"] + 1) <= model["horizon_steps"]
                and o.get("terminated") is True
                and not set(o.get("forbidden_prefix", [])).intersection(model["forbidden_prefix_tags"])
                for o in release_blocked
            ) and "release_blocked" not in preimage,
            "unsafe_state_ids": ["release_blocked"],
        },
        "drop_termination": {
            "counterexample_found": all(
                o.get("effect") == model["required_effect"]
                and o.get("release") == model["required_release"]
                and not set(o.get("forbidden_prefix", [])).intersection(model["forbidden_prefix_tags"])
                for o in late
            ) and "late_completion" not in preimage,
            "unsafe_state_ids": ["late_completion"],
        },
    }

    safe_reference = by_id["ready_simple"]
    stale = by_id["stale_generation"]
    exact_accepts_stale = matches_exact_guard(stale, safe_reference)
    generation_mutant_accepts_stale = matches_exact_guard(stale, safe_reference, omit_generation=True)
    stale_outcome_fails = all(not total_correct(o, model) for o in stale["outcomes"])
    stale_forbidden = any(
        bool(set(o.get("forbidden_prefix", [])).intersection(model["forbidden_prefix_tags"]))
        for o in stale["outcomes"]
    )
    mutants["drop_generation_freshness"] = {
        "counterexample_found": (
            generation_mutant_accepts_stale
            and not exact_accepts_stale
            and stale_outcome_fails
            and stale_forbidden
            and "stale_generation" not in preimage
        ),
        "unsafe_state_ids": ["stale_generation"],
        "exact_guard_decision": "REFUSE" if not exact_accepts_stale else "ADMIT",
        "mutated_guard_decision": "ADMIT" if generation_mutant_accepts_stale else "REFUSE",
        "outcome_effects": [o.get("effect") for o in stale["outcomes"]],
        "forbidden_prefix_tags": sorted({tag for o in stale["outcomes"] for tag in o.get("forbidden_prefix", [])}),
    }
    if not all(item["counterexample_found"] for item in mutants.values()):
        errors.append("MUTATION_COUNTEREXAMPLE_MISSING")

    return {
        "decision": "PASS_REQUIRED_MUTATION_COVERAGE_SCOPED" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "input_sha256": input_hashes,
        "independent_preimage_state_ids": sorted(preimage),
        "state_count": len(states),
        "outcome_count": sum(len(s.get("outcomes", [])) for s in states),
        "mutation_checks": mutants,
        "candidate_invocations": 0,
        "independent_audit_invocations": 1,
        "retries": 0,
        "scope": "audit-only supplement to a finite synthetic model; no real GUI or authority claim",
    }


def main() -> None:
    root = Path(__file__).resolve().parent
    input_paths = {
        "MODEL.json": root / "inputs" / "MODEL.json",
        "candidate_raw.json": root / "inputs" / "results" / "t0-01" / "candidate_raw.json",
        "audit_raw.json": root / "inputs" / "results" / "t0-01" / "audit_raw.json",
    }
    raw = {name: path.read_bytes() for name, path in input_paths.items()}
    hashes = {name: sha256(data) for name, data in raw.items()}
    values = {name: json.loads(data) for name, data in raw.items()}
    result = audit(values["MODEL.json"], values["candidate_raw.json"], values["audit_raw.json"], hashes)
    out = root / "results" / "t1-01" / "audit_raw.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "errors": result["errors"], "preimage": result["independent_preimage_state_ids"], "generation_mutation": result["mutation_checks"]["drop_generation_freshness"]}, sort_keys=True))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
