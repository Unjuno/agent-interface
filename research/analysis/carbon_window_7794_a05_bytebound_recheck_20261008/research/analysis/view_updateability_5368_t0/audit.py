"""Independent raw-only reconstruction and audit; does not import gate.py."""
from __future__ import annotations

import json
from pathlib import Path


def matches_projection(world: dict, observed: dict) -> bool:
    state = world["fields"]
    for key, value in observed.items():
        if key not in state or state[key] != value:
            return False
    return True


def effect_is_allowed(case: dict, world: dict) -> bool:
    outcomes = world["effects"].get(case["action"])
    if not outcomes or outcomes.get("realizable") is not True:
        return False
    if outcomes.get("effect") != case["requested_effect"]:
        return False
    if outcomes.get("target") != case["requested_target"]:
        return False
    return all(item not in case["forbidden_collateral"] for item in outcomes.get("collateral", []))


def smallest_separator(case: dict, fiber: list[dict], truth: dict[str, bool]) -> str | None:
    for field in case["hint_candidates"]:
        buckets: dict[str, list[bool]] = {}
        for world in fiber:
            key = json.dumps(world["fields"].get(field, "<MISSING>"), sort_keys=True)
            buckets.setdefault(key, []).append(truth[world["id"]])
        if len(buckets) > 1 and all(len(set(values)) == 1 for values in buckets.values()):
            if len({values[0] for values in buckets.values()}) > 1:
                return field
    return None


def independently_expected(case: dict) -> tuple[str, str | None, list[str]]:
    if case["unknown_model"]:
        return "UNKNOWN_MODEL", None, []
    fiber = [world for world in case["worlds"] if matches_projection(world, case["observed"])]
    if not fiber:
        return "UNKNOWN_MODEL", None, []
    truth = {world["id"]: effect_is_allowed(case, world) for world in fiber}
    members = sorted(truth)
    if all(truth.values()):
        return "ADMIT", None, members
    if not any(truth.values()):
        return "UNTRANSLATABLE", None, members
    separator = smallest_separator(case, fiber, truth)
    if separator is None:
        return "UNTRANSLATABLE", None, members
    return "NEEDS_DISAMBIGUATING_OBSERVATION", separator, members


def main() -> None:
    root = Path(__file__).resolve().parent
    fixture = json.loads((root / "fixture.json").read_text(encoding="utf-8"))
    raw = [json.loads(line) for line in (root / "candidate.jsonl").read_text(encoding="utf-8").splitlines()]
    baseline_raw = [json.loads(line) for line in (root / "baseline.jsonl").read_text(encoding="utf-8").splitlines()]
    errors: list[str] = []
    if len(raw) != len(fixture["cases"]):
        errors.append(f"row_count:{len(raw)}!={len(fixture['cases'])}")
    by_id = {row.get("id"): row for row in raw}
    baseline_by_id = {row.get("id"): row for row in baseline_raw}
    if len(by_id) != len(raw):
        errors.append("duplicate_or_missing_candidate_id")

    baseline_false_admissions = 0
    baseline_admissions = 0
    for case in fixture["cases"]:
        row = by_id.get(case["id"])
        if row is None:
            errors.append(f"missing:{case['id']}")
            continue
        expected_decision, expected_hint, fiber_ids = independently_expected(case)
        if row.get("decision") != expected_decision:
            errors.append(f"decision:{case['id']}:{row.get('decision')}!={expected_decision}")
        if row.get("hint") != expected_hint:
            errors.append(f"hint:{case['id']}:{row.get('hint')}!={expected_hint}")
        if row.get("fiber") != fiber_ids:
            errors.append(f"fiber:{case['id']}:{row.get('fiber')}!={fiber_ids}")
        declared = case["expected"]
        if (expected_decision, expected_hint) != (declared["decision"], declared["hint"]):
            errors.append(f"fixture_expectation_inconsistent:{case['id']}")
        if set(row) != {"id", "decision", "hint", "fiber"}:
            errors.append(f"unexpected_output_fields:{case['id']}")
        baseline = baseline_by_id.get(case["id"])
        baseline_label = case["observed"].get("label") == case["requested_label"]
        baseline_would_admit = case["freshness_valid"] is True and baseline_label
        if baseline is None:
            errors.append(f"baseline_missing:{case['id']}")
        else:
            baseline_admissions += int(baseline_would_admit)
            if baseline.get("decision") != ("ADMIT" if baseline_would_admit else "YIELD"):
                errors.append(f"baseline_decision:{case['id']}")
            if baseline.get("freshness_pass") is not (case["freshness_valid"] is True) or baseline.get("label_match") is not baseline_label:
                errors.append(f"baseline_receipt:{case['id']}")
            if baseline_would_admit and (case["unknown_model"] or expected_decision != "ADMIT"):
                baseline_false_admissions += 1
    result = {
        "status": "PASS_READONLY" if not errors else "FAIL_AUDIT",
        "rows_expected": len(fixture["cases"]),
        "rows_received": len(raw),
        "baseline_rows_received": len(baseline_raw),
        "baseline_admissions": baseline_admissions,
        "baseline_false_admissions": baseline_false_admissions,
        "matched": len(fixture["cases"]) - sum(1 for error in errors if error.startswith(("decision:", "hint:", "fiber:", "missing:"))),
        "errors": errors,
        "authority_or_effect_emitted": False,
    }
    with (root / "audit.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()

