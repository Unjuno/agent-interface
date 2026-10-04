#!/usr/bin/env python3
"""Reproduce the PR #7602 reversed edge-bracket classification."""

import ast
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
    receipt = namespace["input_edge_receipts"](fixture["events"])[0]
    down = receipt.get("down_edge_interval_ns")
    up = receipt.get("up_edge_interval_ns")
    reversed_intervals = (
        type(down) is list and type(up) is list and up[1] < down[0]
    )
    reproduced = reversed_intervals and receipt.get("status") == "adapter_edge_brackets_paired"

    result = {
        "source_commit": "76886c5cc41ef801bf1d0cb153b1dabf444d9127",
        "source_blob": "776b3f32ada0b24d171908e595227e00e2ad9508",
        "source_sha256": source_sha256,
        "function": "input_edge_receipts",
        "fixture_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        "actual_classification": receipt.get("status"),
        "down_interval_ns": down,
        "up_interval_ns": up,
        "reversed_interval_pair_reproduced": reproduced,
        "scope": "Synthetic static counterexample only; does not establish any retained run was mismeasured.",
        "receipt": receipt,
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "actual_classification", "down_interval_ns", "up_interval_ns",
        "reversed_interval_pair_reproduced")}, indent=2))
    if not reproduced:
        raise SystemExit("expected reversed-interval misclassification was not reproduced")


if __name__ == "__main__":
    main()
