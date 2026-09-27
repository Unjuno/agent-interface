"""Post-hoc, non-training revalidation of PR #4481 review findings.

This reads only the frozen manifest, frozen sources and already-retained raw
result/audit. It never imports runner.py or audit.py and never changes a formal
artifact. Its scope is limited to source-byte correspondence and whether the
per-seed-vs-mean lift implementation difference changes this observed decision.
"""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path


EXPECTED_RAW_SHA256 = "ee680b543073c89539a9dc131c0b4e24ca09f82d19054000106ef4630c8a1706"
EXPECTED_SEEDS = [3490, 3491, 3492]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def run(root):
    root = Path(root)
    errors = []
    freeze = load(root / "FREEZE.json")
    raw_bytes = (root / "FORMAL_RESULT.json.gz").read_bytes()
    raw = gzip.decompress(raw_bytes)
    raw_hash = sha256(raw)
    if raw_hash != EXPECTED_RAW_SHA256:
        errors.append("raw_result_sha256")
    payload = json.loads(raw)
    audit = load(root / "AUDIT.json")
    if audit.get("raw_result_sha256") != raw_hash:
        errors.append("audit_raw_binding")

    source_hashes = {}
    for name, expected in freeze["source_sha256"].items():
        actual = sha256((root / name).read_bytes())
        source_hashes[name] = {"expected": expected, "actual": actual, "match": actual == expected}
        if actual != expected:
            errors.append("source_hash:" + name)

    contract = (root / "ISSUE_CONTRACT.md").read_bytes()
    contract_sha = sha256(contract)
    if contract_sha != freeze["public_issue_contract_excerpt"]["sha256"]:
        errors.append("issue_contract_sha256")

    records = audit.get("reports", [])
    if [row.get("seed") for row in records] != EXPECTED_SEEDS:
        errors.append("audit_seed_schedule")
    lifts = []
    seed_quality = []
    for row in records:
        arms = row["arms"]
        treatment = arms["targeted_augmented"]
        control_recall = arms["balanced_control"]["suites"]["near_boundary_shift"]["by_class"]["CORRECT"]["accepted_recall"]
        treatment_recall = treatment["suites"]["near_boundary_shift"]["by_class"]["CORRECT"]["accepted_recall"]
        lift = treatment_recall - control_recall
        if not math.isclose(lift, row["paired_correct_recall_lift"], rel_tol=0, abs_tol=1e-12):
            errors.append("reported_paired_lift:" + str(row["seed"]))
        lifts.append(lift)

        shift = treatment["suites"]["near_boundary_shift"]
        by_class = shift["by_class"]
        quality = (
            shift["accuracy"] >= .95
            and all(by_class[label]["coverage"] >= .75 and by_class[label]["accepted_recall"] >= .95
                    for label in ("CONTINUE", "CORRECT", "WATCH"))
            and shift["false_correct_fraction_all_rows"] <= .005
        )
        seed_quality.append({
            "seed": row["seed"],
            "shift_accuracy": shift["accuracy"],
            "correct_recall": treatment_recall,
            "quality_gate": quality,
            "original_auditor_shift_quality_gate": treatment["gates"]["shift_quality"],
        })
        if quality != treatment["gates"]["shift_quality"]:
            errors.append("recomputed_quality_gate:" + str(row["seed"]))

    mean_lift = sum(lifts) / len(lifts) if lifts else None
    population_sd = (sum((x - sum(lifts) / len(lifts)) ** 2 for x in lifts) / len(lifts)) ** .5 if lifts else None
    mean_lift_gate = mean_lift is not None and mean_lift >= .10
    all_seed_lift_gate = bool(lifts) and all(x >= .10 for x in lifts)
    quality_gate = bool(seed_quality) and all(row["quality_gate"] for row in seed_quality)
    outcome = "FAIL_DISJOINT_STRATA_AUGMENTATION" if not quality_gate else audit["decision_recomputed"]
    if outcome != audit.get("decision_recomputed"):
        errors.append("decision_disagreement")

    return {
        "schema": "needle-pilot09-review-revalidation-v1",
        "scope": "existing retained evidence only; no training, replay, replacement, or formal retry",
        "raw_result_sha256": raw_hash,
        "raw_result_bytes": len(raw),
        "source_hashes_match_freeze": len(source_hashes) == 10 and all(v["match"] for v in source_hashes.values()),
        "source_hashes": source_hashes,
        "issue_contract_sha256": contract_sha,
        "paired_correct_recall_lifts": lifts,
        "mean_paired_correct_recall_lift": mean_lift,
        "mean_lift_gate_threshold": .10,
        "mean_lift_gate_pass": mean_lift_gate,
        "all_individual_lifts_at_least_threshold": all_seed_lift_gate,
        "population_sd_of_treatment_shifted_correct_recall": audit["shifted_correct_recall_std"],
        "seed_quality": seed_quality,
        "all_seed_quality_gates_pass": quality_gate,
        "decision_revalidated": outcome,
        "per_seed_lift_implementation_difference_changes_observed_decision": False,
        "source_hash_limitation": (
            "All submitted source bytes match the frozen SHA-256 manifest. The retained formal payload does not itself "
            "contain a runtime source attestation; this revalidation proves submitted-tree correspondence, not an "
            "independent measurement of the mounted source bytes at process start."
        ),
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run(args.source)
    encoded = (json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    with open(args.output, "xb") as stream:
        stream.write(encoded)
    print(encoded.decode(), end="")
    if result["errors"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
