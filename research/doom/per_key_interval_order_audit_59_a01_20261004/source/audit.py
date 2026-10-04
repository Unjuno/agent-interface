#!/usr/bin/env python3
"""Reproduce PR #7602 edge-bracket chronology classifications."""

import ast
import copy
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source" / "map01_overlap_controller_v39.py.txt"
FIXTURE = ROOT / "source" / "fixture.json"
OUTPUT = ROOT / "out" / "reproduction.json"
EXPECTED_SOURCE_SHA256 = "48aa1c791ddaa7965a6c1374fc95a7a695d192b62e5fb3b859c0a56e11b7293a"


def main():
    source_bytes = SOURCE.read_bytes()
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise SystemExit(f"source hash mismatch: {source_sha256}")

    tree = ast.parse(source_bytes.decode("utf-8"))
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "input_edge_receipts"
    )
    isolated = ast.Module(body=[function], type_ignores=[])
    namespace = {"hashlib": hashlib}
    exec(compile(isolated, str(SOURCE), "exec"), namespace)

    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cases = {}
    for name, down_interval, up_interval in (
        ("ordered", [100, 110], [200, 210]),
        ("touching", [100, 200], [200, 250]),
        ("overlapping", [100, 200], [150, 250]),
        ("reversed", [200, 210], [100, 110]),
    ):
        events = copy.deepcopy(fixture["events"])
        events[0]["physical_key_measurement"]["adapter_edge"]["interval"] = down_interval
        events[1]["physical_key_measurement"]["adapter_edge"]["interval"] = up_interval
        cases[name] = namespace["input_edge_receipts"](events)[0]

    reversed_receipt = cases["reversed"]
    invalid_chronology = ("touching", "overlapping", "reversed")
    reproduced = (
        cases["ordered"].get("status") == "adapter_edge_brackets_paired" and
        all(cases[name].get("status") == "adapter_edge_brackets_paired"
            for name in invalid_chronology))

    result = {
        "source_commit": "76886c5cc41ef801bf1d0cb153b1dabf444d9127",
        "source_blob": "776b3f32ada0b24d171908e595227e00e2ad9508",
        "source_sha256": source_sha256,
        "function": "input_edge_receipts",
        "fixture_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        "classifications": {
            name: {
                "status": receipt.get("status"),
                "down_interval_ns": receipt.get("down_edge_interval_ns"),
                "up_interval_ns": receipt.get("up_edge_interval_ns"),
            }
            for name, receipt in cases.items()
        },
        "chronology_matrix_fail_open_reproduced": reproduced,
        "overlapping_interval_pair_classified_complete": (
            cases["overlapping"].get("status") == "adapter_edge_brackets_paired"),
        "touching_interval_pair_classified_complete": (
            cases["touching"].get("status") == "adapter_edge_brackets_paired"),
        "ordered_pair_classified_complete": (
            cases["ordered"].get("status") == "adapter_edge_brackets_paired"),
        "strict_chronology_fail_open_reproduced": reproduced,
        "scope": "Synthetic static counterexample only; does not establish any retained run was mismeasured.",
        "reversed_receipt": reversed_receipt,
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "classifications", "chronology_matrix_fail_open_reproduced",
        "overlapping_interval_pair_classified_complete",
        "touching_interval_pair_classified_complete",
        "strict_chronology_fail_open_reproduced")}, indent=2))
    if not reproduced:
        raise SystemExit("expected strict-chronology classification matrix changed")


if __name__ == "__main__":
    main()
