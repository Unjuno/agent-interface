#!/usr/bin/env python3
"""Run the frozen baseline/candidate projection comparison without imports."""
import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_projector(path):
    tree = ast.parse(path.read_text())
    node = next(row for row in tree.body
                if isinstance(row, ast.FunctionDef) and
                row.name == "input_edge_receipts")
    namespace = {"hashlib": hashlib}
    exec(compile(ast.fix_missing_locations(ast.Module(
        body=[node], type_ignores=[])), str(path), "exec"), namespace)
    return namespace["input_edge_receipts"]


def rows_from_input():
    return [json.loads(line) for line in
            (ROOT / "INPUT.jsonl").read_text().splitlines()]


def result_for(projector, events):
    receipt = projector(events)[0]
    return {key: receipt.get(key) for key in
            ("status", "application_consumption_observed",
             "down_edge_interval_ns", "up_edge_interval_ns")}


def mutated(events, row_index, layer):
    clone = json.loads(json.dumps(events))
    row = clone[row_index]
    if layer == "event":
        row["application_consumption_observed"] = True
    elif layer == "measurement":
        row["physical_key_measurement"]["application_consumption_observed"] = True
    elif layer == "adapter_edge":
        row["physical_key_measurement"]["adapter_edge"][
            "application_consumption_observed"] = True
    elif layer == "bracket":
        row["physical_key_measurement"]["bracket"][
            "application_consumption_observed"] = True
    else:
        raise ValueError(layer)
    return clone


def set_edge_interval(row, edge_name, start, end):
    measurement = row["physical_key_measurement"]
    measurement["adapter_edge"]["interval"] = [start, end]
    measurement["bracket"][
        "physical_down_interval" if edge_name == "down"
        else "physical_up_interval"] = [start, end]
    pre = measurement["pre_sample"]
    post = measurement["post_sample"]
    pre["started_ns"] = pre["finished_ns"] = start
    post["started_ns"] = start if edge_name == "up" else end
    post["finished_ns"] = end
    if edge_name == "down":
        measurement["press_request_ns"] = start
        measurement["sync_return_ns"] = start
        row["admitted_ns"] = start
        row["input_ack_ns"] = start
    else:
        measurement["release_request_ns"] = start
        measurement["sync_return_ns"] = start


def sweep(projector, template):
    endpoints = range(4)
    intervals = [(start, end) for start in endpoints for end in endpoints
                 if start <= end]
    cases = []
    for down_start, down_end in intervals:
        for up_start, up_end in intervals:
            events = json.loads(json.dumps(template))
            down = next(row for row in events
                        if row.get("event") == "input_admission")
            up = next(row for row in events
                      if row.get("event") == "input_release_measurement")
            set_edge_interval(down, "down", down_start, down_end)
            set_edge_interval(up, "up", up_start, up_end)
            receipt = projector(events)[0]
            cases.append({
                "down": [down_start, down_end],
                "up": [up_start, up_end],
                "expected_ordered": down_end < up_start,
                "status": receipt["status"],
                "down_edge_interval_ns": receipt.get("down_edge_interval_ns"),
                "up_edge_interval_ns": receipt.get("up_edge_interval_ns"),
            })
    paired = sum(row["status"] == "adapter_edge_brackets_paired" for row in cases)
    incomplete = sum(row["status"] == "adapter_edge_receipt_incomplete" for row in cases)
    return {"cases": cases, "paired": paired, "incomplete": incomplete}


def main():
    base_path = ROOT / "BASELINE_SOURCE.py.txt"
    candidate_path = ROOT / "CANDIDATE_SOURCE.py.txt"
    input_path = ROOT / "INPUT.jsonl"
    base = load_projector(base_path)
    candidate = load_projector(candidate_path)
    source_rows = rows_from_input()
    layers = ("event", "measurement", "adapter_edge", "bracket")

    mutations = []
    for row_index in range(2):
        for layer in layers:
            events = mutated(source_rows, row_index, layer)
            mutations.append({
                "row_index": row_index,
                "layer": layer,
                "baseline": result_for(base, events),
                "candidate": result_for(candidate, events),
            })

    output = {
        "protocol": "v39-application-consumption-conflict-a01-v1",
        "sources": {
            "baseline_commit": "8b5fa6429a1529bd98d61e8331a53c6fb76939e6",
            "baseline_sha256": sha256(base_path),
            "candidate_sha256": sha256(candidate_path),
            "input_sha256": sha256(input_path),
        },
        "valid_control": result_for(candidate, source_rows),
        "application_flag_mutations": mutations,
        "interval_sweep": {
            "baseline": sweep(base, source_rows),
            "candidate": sweep(candidate, source_rows),
        },
        "scope": "Deterministic software projection only; no X server, live input, application consumption, game, model, or user-task effect.",
    }
    false_accepts = [row for row in mutations
                     if row["candidate"]["status"] == "adapter_edge_brackets_paired"]
    output["candidate_false_accept_count"] = len(false_accepts)
    output["baseline_false_accept_count"] = sum(
        row["baseline"]["status"] == "adapter_edge_brackets_paired"
        for row in mutations)
    output["candidate_pass"] = (
        output["valid_control"]["status"] == "adapter_edge_brackets_paired" and
        output["baseline_false_accept_count"] > 0 and
        output["candidate_false_accept_count"] == 0 and
        output["interval_sweep"]["baseline"]["paired"] == 15 and
        output["interval_sweep"]["baseline"]["incomplete"] == 85 and
        output["interval_sweep"]["candidate"]["paired"] == 15 and
        output["interval_sweep"]["candidate"]["incomplete"] == 85)
    encoded = json.dumps(output, indent=2, sort_keys=True) + "\n"
    target = ROOT / "raw" / "A01.json"
    target.write_text(encoded)
    print(encoded, end="")
    return 0 if output["candidate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
