#!/usr/bin/env python3
"""Independent raw-only auditor. Does not import candidate.py."""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import math
from pathlib import Path

HORIZON_MS = 350.0
GROWTH_RATIO = 2.0


def load_jsonl(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def pixels(encoded: str, width: int, height: int) -> bytes:
    binary = base64.b64decode(encoded, validate=True)
    first, second, third, payload = binary.split(b"\n", 3)
    if (first, second, third) != (b"P5", f"{width} {height}".encode(), b"255"):
        raise AssertionError("frame header differs")
    if len(payload) != width * height:
        raise AssertionError("frame length differs")
    return payload


def observer_digest(row: dict) -> str:
    canonical = json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def independently_expected(row: dict) -> dict:
    image_rows = [pixels(encoded, row["width"], row["height"]) for encoded in row["frames_b64"]]
    area = [sum(byte > 0 for byte in img) for img in image_rows]
    # Pixel-area equivalent radius; independent implementation of the frozen rule.
    radii = [math.sqrt(float(count) / math.pi) for count in area]
    changed_intervals = sum(image_rows[i] != image_rows[i + 1] for i in range(len(image_rows) - 1))
    growth_ratio = radii[-1] / radii[0] if radii[0] != 0 else math.inf
    interval_ms = row["timestamps_ms"][-1] - row["timestamps_ms"][-2]
    if interval_ms <= 0:
        raise AssertionError("last timestamps are not increasing")
    radial_rate = (radii[-1] - radii[-2]) / interval_ms
    tau_ms = radii[-1] / radial_rate if radial_rate > 0 else None
    cues = {
        "any_pixel_change": "YIELD" if changed_intervals > 0 else "CONTINUE",
        "endpoint_radius_growth": "YIELD" if growth_ratio >= GROWTH_RATIO else "CONTINUE",
        "radius_tau": "UNKNOWN" if tau_ms is None else ("YIELD" if tau_ms <= HORIZON_MS else "CONTINUE"),
    }
    return {
        "case_id": row["case_id"],
        "pair_key": row["pair_key"],
        "observer_input_sha256": observer_digest(row),
        "frame_count": len(image_rows),
        "pixel_change_intervals": changed_intervals,
        "radius_start_px": radii[0],
        "radius_end_px": radii[-1],
        "estimated_tau_ms": tau_ms,
        "cues": cues,
    }


def audit(inputs: list[dict], truth: dict, outputs: list[dict]) -> dict:
    if len(inputs) != 12 or len(outputs) != 12 or len(truth.get("pairs", [])) != 6:
        raise AssertionError("expected exactly 12 observer rows, outputs and six truth pairs")
    if set(truth) != {"pairs"}:
        raise AssertionError("truth sidecar schema differs")
    if len({row["case_id"] for row in inputs}) != 12 or len({row["case_id"] for row in outputs}) != 12:
        raise AssertionError("duplicate case ids")
    by_input = {row["case_id"]: row for row in inputs}
    by_output = {row["case_id"]: row for row in outputs}
    if set(by_input) != set(by_output):
        raise AssertionError("missing or extra candidate output")
    allowed_input = {"case_id", "pair_key", "timestamps_ms", "frames_b64", "width", "height"}
    if any(set(row) != allowed_input for row in inputs):
        raise AssertionError("observer input schema contains an unexpected field")
    if any("truth" in row or "contact_ms" in row or "world" in row for row in inputs):
        raise AssertionError("truth leaked into candidate-visible input")
    if any(set(row) != set(independently_expected(by_input[row["case_id"]])) for row in outputs):
        raise AssertionError("candidate output schema differs")

    last_observed_ms = max(max(row["timestamps_ms"]) for row in inputs)
    truth_cases: list[str] = []
    truth_pair_keys: list[str] = []
    for spec in truth["pairs"]:
        if set(spec) != {
            "pair_key", "approach_case", "approach_contact_ms",
            "animation_case", "animation_contact_ms",
        }:
            raise AssertionError("truth pair schema differs")
        contact_ms = spec["approach_contact_ms"]
        if isinstance(contact_ms, bool) or not isinstance(contact_ms, int) or contact_ms <= last_observed_ms:
            raise AssertionError("approach truth must specify contact after the observed horizon")
        if spec["animation_contact_ms"] is not None:
            raise AssertionError("animation truth must specify no contact")
        truth_cases.extend((spec["approach_case"], spec["animation_case"]))
        truth_pair_keys.append(spec["pair_key"])
    if len(set(truth_pair_keys)) != 6 or len(set(truth_cases)) != 12 or set(truth_cases) != set(by_input):
        raise AssertionError("truth labels do not form six distinct, complete pairs")

    pair_counts = {"exact_input_pairs": 0, "cue_output_pairs_equal": 0}
    cue_yields = {key: 0 for key in ("any_pixel_change", "endpoint_radius_growth", "radius_tau")}
    for spec in truth["pairs"]:
        left = by_input[spec["approach_case"]]
        right = by_input[spec["animation_case"]]
        if left["pair_key"] != spec["pair_key"] or right["pair_key"] != spec["pair_key"]:
            raise AssertionError("pair identity mismatch")
        if left["timestamps_ms"] != right["timestamps_ms"] or left["frames_b64"] != right["frames_b64"]:
            raise AssertionError("counterfactual observer inputs are not byte-identical")
        pair_counts["exact_input_pairs"] += 1
        for row in (left, right):
            expected = independently_expected(row)
            if by_output[row["case_id"]] != expected:
                raise AssertionError(f"raw output does not match independent replay: {row['case_id']}")
        lc = by_output[left["case_id"]]["cues"]
        rc = by_output[right["case_id"]]["cues"]
        if lc != rc:
            raise AssertionError("deterministic cues differ on identical observer inputs")
        pair_counts["cue_output_pairs_equal"] += 1
        for cue, decision in lc.items():
            if decision == "YIELD":
                cue_yields[cue] += 1

    if pair_counts != {"exact_input_pairs": 6, "cue_output_pairs_equal": 6}:
        raise AssertionError("not all six exact pairs were reconstructed")
    status = "PASS_VISUAL_EQUIVALENCE_BOUNDARY_SCOPED" if any(cue_yields.values()) else "HOLD_CUE_NOT_TRIGGERED"
    return {
        "status": status,
        "pairs": pair_counts,
        "cue_yields_on_approach": cue_yields,
        "paired_false_yields_on_animation": dict(cue_yields),
        "limitations": [
            "synthetic 2-D raster equivalence only",
            "no live visual recognition, GUI, DOOM, safety, or product claim",
        ],
        "errors": [],
    }


def corruption_controls(inputs: list[dict], outputs: list[dict], truth: dict) -> dict:
    checks = 0
    try:
        audit(inputs, truth, outputs[:-1])
    except AssertionError:
        checks += 1
    if checks != 1:
        raise AssertionError("missing-output corruption was not rejected")
    mutated = json.loads(json.dumps(inputs))
    mutated[1]["frames_b64"][0] = mutated[1]["frames_b64"][0][:-4] + "AAAA"
    try:
        audit(mutated, truth, outputs)
    except (AssertionError, ValueError):
        checks += 1
    if checks != 2:
        raise AssertionError("frame corruption was not rejected")
    mutated = json.loads(json.dumps(inputs))
    mutated[1]["timestamps_ms"][1] += 1
    try:
        audit(mutated, truth, outputs)
    except AssertionError:
        checks += 1
    if checks != 3:
        raise AssertionError("timestamp corruption was not rejected")
    mutated_truth = json.loads(json.dumps(truth))
    mutated_truth["pairs"][0]["animation_contact_ms"] = 900
    try:
        audit(inputs, mutated_truth, outputs)
    except AssertionError:
        checks += 1
    if checks != 4:
        raise AssertionError("truth-label corruption was not rejected")
    return {"effective_controls_passed": checks, "expected": 4}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--truth", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    inputs = load_jsonl(args.input)
    outputs = load_jsonl(args.output)
    truth = json.loads(args.truth.read_text(encoding="utf-8"))
    result = audit(inputs, truth, outputs)
    result["corruption_controls"] = corruption_controls(inputs, outputs, truth)
    result["expected_output_rows"] = len(inputs)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"auditor {result['status']}: pairs={result['pairs']} controls={result['corruption_controls']}")


if __name__ == "__main__":
    main()
