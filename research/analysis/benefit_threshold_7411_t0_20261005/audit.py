"""Independent raw-only oracle and eight tamper controls; does not import candidate."""
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUT = HERE / "INPUT.json"
CANDIDATE = HERE / "CANDIDATE.json"
AUDIT = HERE / "AUDIT.json"
EXPECTED = {
    "planner_boundary": ("THRESHOLD_BRACKETED", 100),
    "local_processing": ("THRESHOLD_BRACKETED", 150),
    "correctness_regression": ("INELIGIBLE_CORRECTNESS_GATE", None),
    "sparse_support": ("UNKNOWN_INSUFFICIENT_SUPPORT", None),
}


def fail_if_not(condition, message):
    if not condition:
        raise ValueError(message)


def independent_expected(data, input_hash):
    records = data["records"]
    ids = [r.get("trial_id") for r in records]
    fail_if_not(len(ids) == len(set(ids)), "duplicate raw trial id")
    conditions = {r["condition"] for r in records}
    fail_if_not(conditions == set(EXPECTED), "case-label set mismatch")
    out = {}
    for condition in sorted(conditions):
        subset = [r for r in records if r["condition"] == condition]
        correct = {r["correctness_gate"] for r in subset}
        fail_if_not(len(correct) == 1 and type(next(iter(correct))) is bool,
                    "mixed or invalid correctness gate")
        dose_cells = []
        for level in data["dose_levels_ms"]:
            observed = [r for r in subset if r["dose_ms_saved"] == level]
            fail_if_not(all(r["choice"] in {"worthwhile", "not_worthwhile",
                                                "indifferent", "missing"}
                            for r in observed), "invalid choice enum")
            scored = [r["choice"] for r in observed
                      if r["choice"] in ("worthwhile", "not_worthwhile")]
            positives = scored.count("worthwhile")
            dose_cells.append({
                "dose_ms_saved": level,
                "n_valid": len(scored),
                "n_worthwhile": positives,
                "proportion": round(positives / len(scored), 6) if scored else None,
            })
        if correct == {False}:
            state, bracket = "INELIGIBLE_CORRECTNESS_GATE", None
        elif any(cell["n_valid"] < data["minimum_valid_per_dose"] for cell in dose_cells):
            state, bracket = "UNKNOWN_INSUFFICIENT_SUPPORT", None
        else:
            crossing = next((i for i, cell in enumerate(dose_cells)
                             if cell["proportion"] >= 0.5), None)
            if crossing is None:
                state, bracket = "UNKNOWN_NO_CROSSING", None
            elif crossing == 0:
                state, bracket = "CROSSED_AT_MIN_TESTED_DOSE", [None, dose_cells[0]["dose_ms_saved"]]
            else:
                state = "THRESHOLD_BRACKETED"
                bracket = [dose_cells[crossing - 1]["dose_ms_saved"],
                           dose_cells[crossing]["dose_ms_saved"]]
        out[condition] = {"status": state, "cells": dose_cells,
                          "threshold_bracket_ms": bracket}
    return {"input_sha256": input_hash,
            "estimator": "first-tested-dose-with-at-least-50%-worthwhile-choices",
            "results": out}


def validate(data_bytes, candidate_obj):
    data = json.loads(data_bytes)
    fail_if_not(data.get("schema") == "synthetic-paired-choice-v1", "schema mismatch")
    digest = hashlib.sha256(data_bytes).hexdigest()
    expected = independent_expected(data, digest)
    fail_if_not(candidate_obj == expected, "candidate differs from independent raw oracle")
    results = expected["results"]
    for name, (state, median) in EXPECTED.items():
        row = results[name]
        fail_if_not(row["status"] == state, f"wrong state for {name}")
        bracket = row["threshold_bracket_ms"]
        if median is not None:
            fail_if_not(bracket is not None and bracket[0] <= median <= bracket[1],
                        f"planted median not bracketed for {name}")
        else:
            fail_if_not(bracket is None, f"ineligible/unknown case gained threshold: {name}")
    fail_if_not(results["planner_boundary"] != results["local_processing"],
                "timing-location strata collapsed")


def mutated_pairs(data_bytes, candidate_obj):
    pairs = []
    pairs.append((data_bytes, {k: v for k, v in candidate_obj.items()
                               if k != "input_sha256"}))
    changed = copy.deepcopy(candidate_obj); changed["input_sha256"] = "0" * 64
    pairs.append((data_bytes, changed))
    changed = copy.deepcopy(candidate_obj); del changed["results"]["planner_boundary"]
    pairs.append((data_bytes, changed))
    changed = copy.deepcopy(candidate_obj); changed["results"]["planner_boundary"]["cells"][0]["n_valid"] += 1
    pairs.append((data_bytes, changed))
    changed = copy.deepcopy(candidate_obj); changed["results"]["correctness_regression"]["status"] = "THRESHOLD_BRACKETED"
    changed["results"]["correctness_regression"]["threshold_bracket_ms"] = [0, 50]
    pairs.append((data_bytes, changed))
    changed = copy.deepcopy(candidate_obj); changed["results"]["sparse_support"]["threshold_bracket_ms"] = [100, 150]
    pairs.append((data_bytes, changed))
    altered = json.loads(data_bytes); altered["records"].pop()
    pairs.append(((json.dumps(altered, sort_keys=True, separators=(",", ":")) + "\n").encode(), candidate_obj))
    altered = json.loads(data_bytes); altered["records"][0]["condition"] = "local_processing"
    pairs.append(((json.dumps(altered, sort_keys=True, separators=(",", ":")) + "\n").encode(), candidate_obj))
    return pairs


def main():
    data_bytes = INPUT.read_bytes()
    candidate_obj = json.loads(CANDIDATE.read_bytes())
    validate(data_bytes, candidate_obj)
    rejected = 0
    for bad_input, bad_candidate in mutated_pairs(data_bytes, candidate_obj):
        try:
            validate(bad_input, bad_candidate)
        except (ValueError, KeyError, TypeError):
            rejected += 1
    result = {"status": "PASS_METHOD_SCOPED" if rejected == 8 else "FAIL_METHOD",
              "input_sha256": hashlib.sha256(data_bytes).hexdigest(),
              "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
              "conditions": 4, "mutation_controls": 8,
              "mutations_rejected": rejected,
              "scope": "synthetic method only; no user-value inference"}
    encoded = (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode()
    AUDIT.write_bytes(encoded)
    print(encoded.decode(), end="")
    if rejected != 8:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
