#!/usr/bin/env python3
"""Independently check strict interval chronology at PR #7602's repaired head."""

import ast
import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source" / "map01_overlap_controller_v39.py.txt"
FIXTURE = ROOT / "source" / "fixture.json"
OUTPUT = ROOT / "out" / "verification.json"
EXPECTED_SOURCE_SHA256 = "a6ec913551d5d9f40ab06bd2dd76b8e1730ff0f1b66a911fecd5927118aee813"


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
    intervals = {
        "ordered": ([100, 110], [200, 210]),
        "touching": ([100, 200], [200, 250]),
        "overlapping": ([100, 200], [150, 250]),
        "reversed": ([200, 210], [100, 110]),
    }
    cases = {}
    for name, (down_interval, up_interval) in intervals.items():
        events = copy.deepcopy(fixture["events"])
        events[0]["physical_key_measurement"]["adapter_edge"]["interval"] = down_interval
        events[1]["physical_key_measurement"]["adapter_edge"]["interval"] = up_interval
        cases[name] = namespace["input_edge_receipts"](events)[0]

    endpoints = range(4)
    valid_intervals = [(start, end) for start in endpoints for end in endpoints
                       if start <= end]
    exhaustive = {"pairs": 0, "strictly_ordered": 0,
                  "not_strictly_ordered": 0, "ordered_paired": 0,
                  "invalid_incomplete": 0, "first_invalid_status": None}
    for down_start, down_end in valid_intervals:
        for up_start, up_end in valid_intervals:
            events = copy.deepcopy(fixture["events"])
            events[0]["physical_key_measurement"]["adapter_edge"]["interval"] = [
                down_start, down_end]
            events[1]["physical_key_measurement"]["adapter_edge"]["interval"] = [
                up_start, up_end]
            receipt = namespace["input_edge_receipts"](events)[0]
            paired = receipt.get("status") == "adapter_edge_brackets_paired"
            strictly_ordered = down_end < up_start
            exhaustive["pairs"] += 1
            if strictly_ordered:
                exhaustive["strictly_ordered"] += 1
                exhaustive["ordered_paired"] += paired
            else:
                exhaustive["not_strictly_ordered"] += 1
                exhaustive["invalid_incomplete"] += not paired
                if paired and exhaustive["first_invalid_status"] is None:
                    exhaustive["first_invalid_status"] = {
                        "down_interval": [down_start, down_end],
                        "up_interval": [up_start, up_end],
                    }

    passed = (
        cases["ordered"].get("status") == "adapter_edge_brackets_paired" and
        all(cases[name].get("status") == "adapter_edge_receipt_incomplete"
            for name in ("touching", "overlapping", "reversed")) and
        exhaustive["pairs"] == 100 and
        exhaustive["strictly_ordered"] == 15 and
        exhaustive["not_strictly_ordered"] == 85 and
        exhaustive["ordered_paired"] == 15 and
        exhaustive["invalid_incomplete"] == 85 and
        exhaustive["first_invalid_status"] is None)

    result = {
        "source_commit": "40c6a278d06ec4411b72dd5d7d8899d85bebfcf4",
        "source_blob": "84cf5c5a812ae02f2bd454f35aab30becfd704e1",
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
        "exhaustive_closed_interval_pairs_endpoints_0_to_3": exhaustive,
        "strict_chronology_fix_verified": passed,
        "scope": "Independent AST-extracted synthetic projection audit only; no retained run or runtime behavior claim.",
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "classifications": result["classifications"],
        "exhaustive_closed_interval_pairs_endpoints_0_to_3": exhaustive,
        "strict_chronology_fix_verified": passed,
    }, indent=2))
    if not passed:
        raise SystemExit("strict chronology repair matrix failed")


if __name__ == "__main__":
    main()
