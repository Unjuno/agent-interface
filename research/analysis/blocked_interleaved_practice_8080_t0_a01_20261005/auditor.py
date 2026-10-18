"""Independent raw-only schedule, reversible-effect, and scorer audit."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def expected_order(variants: list[str], attempts: int, arm: str) -> list[str]:
    if arm == "blocked":
        return [variant for variant in variants for _ in range(attempts)]
    return [variants[index] for _ in range(attempts) for index in range(len(variants))]


def score(trace: dict[str, object], truth: dict[str, object]) -> str:
    expected = truth["expected_effects"]
    intent = trace["intent"]
    if intent not in expected:
        return "UNKNOWN_OUTSIDE_FAMILY"
    if trace["observed_target"] != intent:
        return "REJECT_WRONG_TARGET"
    if trace["observed_effect"] != expected[intent]:
        return "REJECT_FALSE_SUCCESS"
    return "VALID_EXACT_EFFECT" if trace["success_claim"] is True else "NO_SUCCESS_CLAIM"


def audit(design: dict[str, object], truth: dict[str, object], raw: dict[str, object]) -> dict[str, object]:
    errors = []
    variants = list(design["training_variants"])
    heldout = set(truth["heldout_variants"])
    attempts = int(design["attempts_per_variant"])
    expected_count = len(variants) * attempts
    if len(variants) != 3 or len(heldout) != 2 or heldout.intersection(variants):
        errors.append("fixture_partition")
    if raw.get("schema") != "blocked-interleaved-8080-candidate-v1":
        errors.append("raw_schema")
    if raw.get("scope") != "synthetic_in_memory_only":
        errors.append("execution_scope")
    arms = raw.get("arms", {})
    counts_by_arm = {}
    effects_checked = inverse_checked = restored = 0
    for arm in ("blocked", "interleaved"):
        content = arms.get(arm, {})
        schedule = content.get("schedule", [])
        effects = content.get("effects", [])
        expected = expected_order(variants, attempts, arm)
        if schedule != expected:
            errors.append(f"schedule:{arm}")
        if len(schedule) != expected_count or len(effects) != expected_count:
            errors.append(f"dose:{arm}")
        counts = Counter(schedule)
        counts_by_arm[arm] = dict(counts)
        if any(counts[variant] != attempts for variant in variants):
            errors.append(f"exposure:{arm}")
        if set(schedule) & heldout or set(schedule) - set(variants):
            errors.append(f"heldout_or_unknown_leak:{arm}")
        if len(schedule) == expected_count:
            if arm == "blocked" and any(schedule[i] != schedule[i - 1] for i in range(1, len(schedule)) if i not in (attempts, 2 * attempts)):
                errors.append("blocked_contiguity")
            if arm == "interleaved" and any(schedule[i] == schedule[i - 1] for i in range(1, len(schedule))):
                errors.append("interleaved_repeat")
        per_variant_attempts = Counter()
        for index, row in enumerate(effects):
            if index >= len(schedule):
                errors.append(f"extra_effect:{arm}")
                continue
            variant = schedule[index]
            per_variant_attempts[variant] += 1
            if row.get("slot") != index or row.get("variant") != variant:
                errors.append(f"row_identity:{arm}:{index}")
            if row.get("within_variant_attempt") != per_variant_attempts[variant]:
                errors.append(f"attempt_ordinal:{arm}:{index}")
            if row.get("materials_id") != design["materials_id"] or row.get("feedback_event") != "fixed_feedback_v1":
                errors.append(f"dose_material_or_feedback:{arm}:{index}")
            if row.get("observed_forward_effect") != truth["expected_effects"].get(variant):
                errors.append(f"forward_effect:{arm}:{index}")
            else:
                effects_checked += 1
            if row.get("observed_inverse_effect") != truth["expected_inverse_effects"].get(variant):
                errors.append(f"inverse_effect:{arm}:{index}")
            else:
                inverse_checked += 1
            if row.get("restored_initial_state") is not True:
                errors.append(f"not_restored:{arm}:{index}")
            else:
                restored += 1
    controls = [
        {"id": trace["id"], "score": score(trace, truth)}
        for trace in truth["scoring_controls"]
    ]
    decision = "METHOD_PASS_SCOPED" if not errors else "FAIL"
    return {
        "schema": "blocked-interleaved-8080-audit-v1",
        "decision": decision,
        "errors": errors,
        "training_variants": len(variants),
        "heldout_variants": len(heldout),
        "attempts_per_variant_per_arm": attempts,
        "attempts_per_arm": expected_count,
        "counts_by_arm": counts_by_arm,
        "forward_effects_checked": effects_checked,
        "inverse_effects_checked": inverse_checked,
        "restorations_checked": restored,
        "scoring_controls": controls,
        "human_effect": "NOT_TESTED",
        "scope": "synthetic schedule and reversible effect-oracle method readiness only",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", type=Path, default=Path("design.json"))
    parser.add_argument("--truth", type=Path, default=Path("scorer_fixture.json"))
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    design, truth, raw = (json.loads(p.read_text()) for p in (args.design, args.truth, args.raw))
    result = audit(design, truth, raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"{result['decision']} errors={len(result['errors'])} output={args.output}")
    return 0 if result["decision"] == "METHOD_PASS_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
