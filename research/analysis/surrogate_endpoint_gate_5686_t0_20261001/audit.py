#!/usr/bin/env python3
"""Independent raw-only auditor; intentionally does not import candidate.py."""
import argparse
import json
from collections import defaultdict
from pathlib import Path


EXPECTED = {
    "concordant": "DIRECTION_CONCORDANT_IN_OBSERVED_STRATA_PREDICTIVE_VALIDITY_UNESTABLISHED",
    "unrelated": "REJECT_INTERMEDIATE_ONLY_EFFECT",
    "common_cause": "REJECT_INTERMEDIATE_ONLY_EFFECT",
    "paradox": "REJECT_NONCOMPENSABLE_SAFETY_REGRESSION",
    "incomplete": "UNCERTAIN_INCOMPLETE_ENDPOINTS",
}
EXPECTED_ATTEMPTS = {
    "concordant": {"a1", "a2", "b1", "b2"},
    "unrelated": {"a1", "a2", "b1", "b2"},
    "common_cause": {"a_easy_c", "a_hard_c", "a_easy_t", "a_hard_t",
                     "b_easy_c", "b_hard_c", "b_easy_t", "b_hard_t"},
    "paradox": {"a1", "a2", "b1", "b2"},
    "incomplete": {"a1", "a2", "b1", "b2"},
}
EXPECTED_STRATA = {"route_a", "route_b"}


def independent_result(rows):
    by_stratum = defaultdict(lambda: {0: [], 1: []})
    for row in rows:
        if row["treatment"] not in (0, 1):
            raise ValueError("invalid treatment")
        by_stratum[row["stratum"]][row["treatment"]].append(row)
    effects = []
    for label, arms in sorted(by_stratum.items()):
        if not arms[0] or not arms[1]:
            raise ValueError("unpaired stratum: " + label)
        n0, n1 = len(arms[0]), len(arms[1])
        effects.append({
            "stratum": label,
            "delta_speed_benefit_ms": sum(x["latency_ms"] for x in arms[0])/n0 - sum(x["latency_ms"] for x in arms[1])/n1,
            "delta_utility": sum(x["utility"] for x in arms[1])/n1 - sum(x["utility"] for x in arms[0])/n0,
            "delta_harm": sum(bool(x["safety_failure"]) for x in arms[1])/n1 - sum(bool(x["safety_failure"]) for x in arms[0])/n0,
            "attempts": n0+n1,
            "incomplete": any(x["endpoint"] != "verified" for arm in arms.values() for x in arm),
        })
    if any(x["incomplete"] for x in effects):
        decision = "UNCERTAIN_INCOMPLETE_ENDPOINTS"
    elif any(x["delta_harm"] > 0 for x in effects):
        decision = "REJECT_NONCOMPENSABLE_SAFETY_REGRESSION"
    elif any(x["delta_speed_benefit_ms"] > 0 and x["delta_utility"] < 0 for x in effects):
        decision = "REJECT_EFFECT_DIRECTION_INVERSION"
    elif any(x["delta_speed_benefit_ms"] > 0 and x["delta_utility"] == 0 for x in effects):
        decision = "REJECT_INTERMEDIATE_ONLY_EFFECT"
    elif all(x["delta_speed_benefit_ms"] > 0 and x["delta_utility"] > 0 for x in effects):
        decision = "DIRECTION_CONCORDANT_IN_OBSERVED_STRATA_PREDICTIVE_VALIDITY_UNESTABLISHED"
    else:
        decision = "NOT_PROMOTABLE"
    return {"world": rows[0]["world"], "attempt_count": len(rows),
            "naive_intermediate_only_rule_promotes": any(x["delta_speed_benefit_ms"] > 0 for x in effects),
            "strata": effects, "disposition": decision}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--fixtures", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    frozen = json.loads(Path(args.fixtures).read_text())
    frozen_by_world = defaultdict(list)
    for row in frozen:
        frozen_by_world[row["world"]].append(row)
    attempts, claimed = defaultdict(list), {}
    for line in Path(args.input).read_text().splitlines():
        item = json.loads(line)
        if item["record_type"] == "attempt":
            row = item["record"]
            attempts[row["world"]].append(row)
        elif item["record_type"] == "summary":
            summary = item["summary"]
            if summary["world"] in claimed:
                raise ValueError("duplicate summary")
            claimed[summary["world"]] = summary
        else:
            raise ValueError("unknown record type")
    errors = []
    results = {}
    for world, rows in sorted(attempts.items()):
        computed = independent_result(rows)
        results[world] = computed
        if sorted(rows, key=lambda r: (r["stratum"], r["attempt"])) != sorted(
                frozen_by_world.get(world, []), key=lambda r: (r["stratum"], r["attempt"])):
            errors.append("raw attempt rows differ from frozen fixture: " + world)
        if {r["attempt"] for r in rows} != EXPECTED_ATTEMPTS.get(world):
            errors.append("attempt inventory mismatch: " + world)
        if {r["stratum"] for r in rows} != EXPECTED_STRATA:
            errors.append("stratum inventory mismatch: " + world)
        if claimed.get(world) != computed:
            errors.append("candidate summary mismatch: " + world)
        if computed["disposition"] != EXPECTED.get(world):
            errors.append("unexpected disposition: " + world)
        if computed["naive_intermediate_only_rule_promotes"] is not True:
            errors.append("naive intermediate rule did not promote control: " + world)
        if world != "concordant" and computed["disposition"].startswith("DIRECTION_CONCORDANT"):
            errors.append("false-positive world was retained as concordant: " + world)
        if world == "concordant" and "PREDICTIVE_VALIDITY_UNESTABLISHED" not in computed["disposition"]:
            errors.append("positive synthetic control overclaimed validity")
        if world == "common_cause":
            # Verify positive within-arm association without treating it as an effect.
            for treatment in (0, 1):
                arm = [r for r in rows if r["treatment"] == treatment]
                if not (min(r["latency_ms"] for r in arm if r["utility"] == 2) < max(r["latency_ms"] for r in arm if r["utility"] == 0)):
                    errors.append("common-cause fixture lacks within-arm association")
    if set(attempts) != set(EXPECTED) or set(claimed) != set(EXPECTED) or set(attempts) != set(frozen_by_world):
        errors.append("world set mismatch")
    # For this fixed T0, every frozen attempt id must be unique and all authored rows retained.
    ids = [(r["world"], r["attempt"]) for rows in attempts.values() for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate attempt id")
    result = {"status": "PASS_SURROGATE_GATE_SCOPED" if not errors else "FAIL_AUDIT",
              "attempt_count": sum(map(len, attempts.values())), "world_count": len(attempts),
              "results": results, "errors": errors,
              "scope": "synthetic authored finite cases only; no empirical surrogate validated"}
    Path(args.output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(result["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
