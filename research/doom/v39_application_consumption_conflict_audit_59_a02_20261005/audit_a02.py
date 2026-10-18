#!/usr/bin/env python3
"""Independently recompute A01 chronology classifications and mutation controls."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_INPUT_SHA256 = "3f664d52a492ad9d0cbbbdb70880ffe16a4909d4bf2c2880d51891d523652363"
IMPLEMENTATIONS = ("baseline", "candidate")
PAIRED = "adapter_edge_brackets_paired"
INCOMPLETE = "adapter_edge_receipt_incomplete"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valid_interval(value: Any) -> bool:
    return (type(value) is list and len(value) == 2 and
            all(type(part) is int for part in value) and value[0] <= value[1])


def audit_cases(cases: Any) -> dict[str, Any]:
    errors: list[str] = []
    counts = {"ordered": 0, "incomplete": 0}
    if type(cases) is not list or len(cases) != 100:
        return {"status": "REJECTED", "errors": ["case count is not 100"],
                "counts": counts, "chronology_mismatches": 0}

    chronology_mismatches = 0
    for index, row in enumerate(cases):
        if type(row) is not dict:
            errors.append(f"case {index}: row is not an object")
            continue
        down, up = row.get("down"), row.get("up")
        if not valid_interval(down) or not valid_interval(up):
            errors.append(f"case {index}: invalid input interval")
            chronology_mismatches += 1
            continue

        ordered = down[1] < up[0]
        if row.get("expected_ordered") is not ordered:
            errors.append(f"case {index}: recorded chronology disagrees with intervals")
            chronology_mismatches += 1
        expected_status = PAIRED if ordered else INCOMPLETE
        if row.get("status") != expected_status:
            errors.append(f"case {index}: status disagrees with intervals")
        if ordered:
            counts["ordered"] += 1
            if (row.get("down_edge_interval_ns") != down or
                    row.get("up_edge_interval_ns") != up):
                errors.append(f"case {index}: paired outputs disagree with intervals")
        else:
            counts["incomplete"] += 1
            if (row.get("down_edge_interval_ns") is not None or
                    row.get("up_edge_interval_ns") is not None):
                errors.append(f"case {index}: unordered interval was exposed")

    if counts != {"ordered": 15, "incomplete": 85}:
        errors.append(f"expected 15/85 chronology cases, got {counts}")
    return {"status": "PASS" if not errors else "REJECTED", "errors": errors,
            "counts": counts, "chronology_mismatches": chronology_mismatches}


def audit_raw(raw: Any) -> dict[str, Any]:
    if type(raw) is not dict or type(raw.get("interval_sweep")) is not dict:
        return {"status": "REJECTED", "errors": ["interval sweep missing"]}
    implementations: dict[str, Any] = {}
    errors: list[str] = []
    total_mismatches = 0
    for name in IMPLEMENTATIONS:
        sweep = raw["interval_sweep"].get(name)
        cases = sweep.get("cases") if type(sweep) is dict else None
        result = audit_cases(cases)
        implementations[name] = result
        errors.extend(f"{name}: {message}" for message in result["errors"])
        total_mismatches += result["chronology_mismatches"]
    return {"status": "PASS" if not errors else "REJECTED", "errors": errors,
            "implementations": implementations,
            "chronology_mismatches": total_mismatches}


def make_balanced_corruption(raw: dict[str, Any]) -> dict[str, Any]:
    mutated = copy.deepcopy(raw)
    for name in IMPLEMENTATIONS:
        rows = mutated["interval_sweep"][name]["cases"]
        valid = next(row for row in rows
                     if row["down"][1] < row["up"][0])
        invalid = next(row for row in rows
                       if row["down"][1] >= row["up"][0])
        valid["expected_ordered"] = False
        valid["status"] = INCOMPLETE
        valid["down_edge_interval_ns"] = None
        valid["up_edge_interval_ns"] = None
        invalid["expected_ordered"] = True
        invalid["status"] = PAIRED
        invalid["down_edge_interval_ns"] = invalid["down"][:]
        invalid["up_edge_interval_ns"] = invalid["up"][:]
    return mutated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    observed_hash = sha256(args.input)
    raw = json.loads(args.input.read_text(encoding="utf-8"))
    original = audit_raw(raw)
    mutated = make_balanced_corruption(raw)
    mutation_result = audit_raw(mutated)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "source-A01.json").write_bytes(args.input.read_bytes())
    (args.output_dir / "mutated-A01.json").write_text(
        json.dumps(mutated, indent=2) + "\n", encoding="utf-8")
    counts_preserved = all(
        original.get("implementations", {}).get(name, {}).get("counts") ==
        mutation_result.get("implementations", {}).get(name, {}).get("counts")
        for name in IMPLEMENTATIONS)
    passed = (observed_hash == EXPECTED_INPUT_SHA256 and
              original["status"] == "PASS" and
              mutation_result["status"] == "REJECTED" and
              mutation_result["chronology_mismatches"] == 4 and counts_preserved)
    report = {
        "schema": "v39-application-consumption-audit-a02-v1",
        "status": "PASS_RAW_CHRONOLOGY_MUTATION_REJECTED" if passed else "FAIL_AUDIT_A02",
        "source": {"input_sha256": observed_hash,
                   "expected_input_sha256": EXPECTED_INPUT_SHA256},
        "original": original,
        "mutated": {"status": mutation_result["status"],
                    "errors": mutation_result["errors"],
                    "chronology_mismatches": mutation_result["chronology_mismatches"],
                    "counts": {name: mutation_result["implementations"][name]["counts"]
                               for name in IMPLEMENTATIONS}},
        "scope": "Audit-only deterministic verification of retained A01 interval classifications; no projector, X server, GUI, input, game, model, or task effect was executed.",
    }
    (args.output_dir / "AUDIT_A02.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
