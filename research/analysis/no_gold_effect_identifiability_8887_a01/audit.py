"""Independent raw-only audit for #8887 A01; does not import candidate."""
import copy
import json
import sys
from pathlib import Path


ALLOCATION = "8887-common-mode-observational-equivalence-a01-20261012-01"
CHECKERS = ("file", "app_readback", "visual_receipt", "shared_parser")
OBSERVED = tuple(map(int, "00001111"))
TRUTH_WORLDS = {
    "A_PERFECT": tuple(map(int, "00001111")),
    "B_COMMON_MODE_CHANCE": tuple(map(int, "00110011")),
}


def validate(record):
    assert record["schema"] == "no_gold_common_mode_control_v1"
    assert record["allocation"] == ALLOCATION
    assert record["checker_ids"] == list(CHECKERS)
    assert len(record["rows"]) == 8
    expected_rows = [
        {"row_id": f"r{i:02d}", "outputs": {name: int(bit) for name in CHECKERS}}
        for i, bit in enumerate(OBSERVED)
    ]
    assert record["rows"] == expected_rows
    expected_prevalence = {name: 0.5 for name in CHECKERS}
    assert record["observed_prevalence"] == expected_prevalence
    expected_agreement = {
        f"{left}|{right}": 1.0
        for i, left in enumerate(CHECKERS)
        for right in CHECKERS[i + 1:]
    }
    assert record["pairwise_agreement"] == expected_agreement
    assert record["no_gold_disposition"] == "UNIDENTIFIABLE_WITHOUT_INDEPENDENCE_EVIDENCE"
    assert record["accuracy_estimate"] is None
    assert record["confidence_claim"] is None


def world_observables(truth):
    """Model a single shared source feeding every checker in both worlds."""
    rows = []
    for i, source_bit in enumerate(OBSERVED):
        rows.append({
            "row_id": f"r{i:02d}",
            "outputs": {checker: int(source_bit) for checker in CHECKERS},
        })
    assert len(truth) == len(rows)
    return rows


def audit(path):
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    validate(record)
    modeled = {name: world_observables(truth) for name, truth in TRUTH_WORLDS.items()}
    assert modeled["A_PERFECT"] == modeled["B_COMMON_MODE_CHANCE"] == record["rows"]
    outputs = tuple(record["rows"][i]["outputs"][CHECKERS[0]] for i in range(8))
    worlds = {}
    for name, truth in TRUTH_WORLDS.items():
        worlds[name] = {
            "truth": "".join(map(str, truth)),
            "truth_prevalence": sum(truth) / len(truth),
            "checker_accuracy": {
                checker: sum(a == b for a, b in zip(outputs, truth)) / len(truth)
                for checker in CHECKERS
            },
        }
    assert worlds["A_PERFECT"]["truth_prevalence"] == worlds["B_COMMON_MODE_CHANCE"]["truth_prevalence"]
    assert all(v == 1.0 for v in worlds["A_PERFECT"]["checker_accuracy"].values())
    assert all(v == 0.5 for v in worlds["B_COMMON_MODE_CHANCE"]["checker_accuracy"].values())
    assert record["no_gold_disposition"] == "UNIDENTIFIABLE_WITHOUT_INDEPENDENCE_EVIDENCE"

    mutations = {}
    mutated = copy.deepcopy(record)
    mutated["rows"][0]["outputs"][CHECKERS[0]] = 1
    try:
        validate(mutated)
    except (AssertionError, KeyError, TypeError):
        mutations["checker_bit_flip"] = "REJECTED"

    mutated = copy.deepcopy(record)
    mutated["rows"].pop()
    try:
        validate(mutated)
    except (AssertionError, KeyError, TypeError):
        mutations["row_drop"] = "REJECTED"

    mutated = copy.deepcopy(record)
    mutated["rows"][1]["row_id"] = mutated["rows"][0]["row_id"]
    try:
        validate(mutated)
    except (AssertionError, KeyError, TypeError):
        mutations["duplicate_row_id"] = "REJECTED"

    mutated = copy.deepcopy(record)
    mutated["accuracy_estimate"] = 1.0
    try:
        validate(mutated)
    except (AssertionError, KeyError, TypeError):
        mutations["unsupported_accuracy_claim"] = "REJECTED"

    assert len(mutations) == 4
    return {
        "schema": "no_gold_common_mode_audit_v1",
        "allocation": ALLOCATION,
        "status": "PASS_COUNTEREXAMPLE_ONLY",
        "same_observables_in_both_worlds": True,
        "worlds": worlds,
        "accuracy_gap": 0.5,
        "candidate_disposition": record["no_gold_disposition"],
        "mutations": mutations,
        "scope": "one finite constructed case; no GUI/checker accuracy claim",
    }


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py INPUT.json OUTPUT.json")
    result = audit(sys.argv[1])
    path = Path(sys.argv[2])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(result["status"])


if __name__ == "__main__":
    main()
