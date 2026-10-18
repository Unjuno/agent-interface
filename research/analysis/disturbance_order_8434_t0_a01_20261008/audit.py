#!/usr/bin/env python3
"""Independent raw-only reconstruction; intentionally imports no candidate code."""

import hashlib
import json
import random
import statistics
import sys
from pathlib import Path


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _reference_schedule(kind, seed, count):
    if kind == "iid":
        values = ["A"] * count
        values.extend(["B"] * count)
        rng = random.Random(seed)
        rng.shuffle(values)
        return values
    left, right = ("A", "B") if seed % 2 == 0 else ("B", "A")
    if kind == "clustered":
        values = []
        for label in (left, right, left, right):
            values.extend([label] * (count // 2))
        return values
    if kind == "alternating":
        values = []
        for _ in range(count):
            values.extend((left, right))
        return values
    if kind == "heldout_block":
        return [left] * count + [right] * count
    raise ValueError("unrecognized structure")


def _reference_metrics(sequence):
    segments = []
    for symbol in sequence:
        if len(segments) == 0 or segments[-1]["label"] != symbol:
            segments.append({"label": symbol, "length": 1})
        else:
            segments[-1]["length"] += 1
    transitions = 0
    serial_product = 0
    for position in range(len(sequence) - 1):
        if sequence[position] != sequence[position + 1]:
            transitions += 1
            serial_product -= 1
        else:
            serial_product += 1
    event_rows = []
    position = 0
    for segment in segments:
        for age in range(segment["length"]):
            absolute = position + age
            event_rows.append({
                "index": absolute,
                "label": sequence[absolute],
                "intensity": 1,
                "duration": 1,
                "routes": {
                    "switch_reconfigure": age >= 1,
                    "two_step_cache": absolute > 0 and age <= 1,
                    "null_a": True,
                    "null_b": True,
                },
                "forbidden_effects": 0,
                "release_empty": True,
            })
        position += segment["length"]
    route_totals = {}
    route_names = ("switch_reconfigure", "two_step_cache", "null_a", "null_b")
    for route in route_names:
        achieved = sum(row["routes"][route] is True for row in event_rows)
        route_totals[route] = {
            "safe_effects": achieved,
            "missed_opportunities": len(sequence) - achieved,
            "forbidden_effects": 0,
            "release_empty_failures": 0,
        }
    return {
        "opportunity_count": len(sequence),
        "label_counts": {"A": sequence.count("A"), "B": sequence.count("B")},
        "transitions": transitions,
        "runs": segments,
        "run_count": len(segments),
        "lag1_product_sum": serial_product,
        "routes": route_totals,
        "events": event_rows,
    }


def audit_document(source_bytes, raw):
    errors = []
    source = json.loads(source_bytes)
    expected_source_hash = hashlib.sha256(source_bytes).hexdigest()
    if set(raw) != {"format", "source_sha256", "cases"}:
        errors.append("raw_top_level_schema")
    if raw.get("format") != "disturbance-order-8434-t0-a01-raw-v1":
        errors.append("raw_format")
    if raw.get("source_sha256") != expected_source_hash:
        errors.append("source_hash_binding")

    expected_cases = {}
    for split, key in (("calibration", "calibration_seeds"), ("heldout", "heldout_seeds")):
        for structure in source["structures"]:
            for seed in source[key]:
                case_id = f"{split}:{structure}:{seed}"
                schedule = _reference_schedule(structure, seed, source["count_per_label"])
                expected_cases[case_id] = {
                    "case_id": case_id,
                    "split": split,
                    "structure": structure,
                    "seed": seed,
                    "schedule": schedule,
                    "schedule_sha256": hashlib.sha256(_canonical(schedule)).hexdigest(),
                    **_reference_metrics(schedule),
                }

    observed = {}
    for case in raw.get("cases", []):
        if not isinstance(case, dict) or not isinstance(case.get("case_id"), str):
            errors.append("malformed_case")
            continue
        case_id = case["case_id"]
        if case_id in observed:
            errors.append(f"duplicate_case:{case_id}")
        observed[case_id] = case
    if set(observed) != set(expected_cases):
        errors.append("case_set_mismatch")
    for case_id, expected in expected_cases.items():
        if case_id in observed and observed[case_id] != expected:
            errors.append(f"raw_reconstruction_mismatch:{case_id}")

    heldout_deltas = {}
    calibration_deltas = {}
    for split, destination in (("heldout", heldout_deltas), ("calibration", calibration_deltas)):
        for structure in source["structures"]:
            vals = []
            for seed in source["heldout_seeds" if split == "heldout" else "calibration_seeds"]:
                case_id = f"{split}:{structure}:{seed}"
                row = expected_cases[case_id]
                routes = row["routes"]
                vals.append(routes["switch_reconfigure"]["safe_effects"] - routes["two_step_cache"]["safe_effects"])
            destination[structure] = {
                "median_paired_delta": statistics.median(vals),
                "minimum": min(vals),
                "maximum": max(vals),
                "n": len(vals),
            }
    margin = source["material_margin_safe_effects"]
    positives = [name for name in source["structures"] if name != "iid" and heldout_deltas[name]["median_paired_delta"] >= margin]
    negatives = [name for name in source["structures"] if name != "iid" and heldout_deltas[name]["median_paired_delta"] <= -margin]
    crossover = bool(positives and negatives)
    if not crossover:
        errors.append("heldout_crossover_gate")
    # Reconstructed route rows also independently verify all safety/release gates.
    if any(route["forbidden_effects"] or route["release_empty_failures"]
           for case in expected_cases.values() for route in case["routes"].values()):
        errors.append("hard_gate_violation")
    # Null controls must match in every source-bound case, not only in an aggregate.
    if any(case["routes"]["null_a"] != case["routes"]["null_b"] for case in expected_cases.values()):
        errors.append("null_control_mismatch")
    return {
        "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
        "errors": errors,
        "case_count": len(observed),
        "expected_case_count": len(expected_cases),
        "heldout_crossover": crossover,
        "heldout_positive_structures": positives,
        "heldout_negative_structures": negatives,
        "heldout_deltas": heldout_deltas,
        "calibration_deltas": calibration_deltas,
        "claim_scope": "finite authored deterministic method fixture only; no empirical interface inference",
    }


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: audit.py SOURCE.json RAW.json AUDIT.json")
    source_path, raw_path, audit_path = map(Path, argv[1:])
    result = audit_document(source_path.read_bytes(), json.loads(raw_path.read_bytes()))
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_bytes(json.dumps(result, indent=2, sort_keys=True).encode() + b"\n")
    print(json.dumps({"status": result["status"], "errors": result["errors"], "cases": result["case_count"]}))
    return 0 if result["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
