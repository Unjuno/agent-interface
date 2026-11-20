#!/usr/bin/env python3
"""Exact-source test of bool/int aliasing in duplicated X11 sample brackets."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SOURCE_COMMIT = "719ef679c977a925db3a6d1fe15f9cd93cf2b42c"
SOURCE_PATH = "research/doom/map01_overlap_controller_v39.py"
FIXTURE_PATH = ROOT / "INPUT.jsonl"


def load_projector(source_text, label):
    tree = ast.parse(source_text)
    node = next(item for item in tree.body
                if isinstance(item, ast.FunctionDef) and item.name == "input_edge_receipts")
    namespace = {"hashlib": hashlib}
    module = ast.Module(body=[node], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), label, "exec"), namespace)
    return namespace["input_edge_receipts"]


def frozen_source():
    return subprocess.run(
        ["git", "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}"],
        check=True, stdout=subprocess.PIPE).stdout.decode("utf-8")


def set_edge_interval(row, edge_name, start, end):
    data = row["physical_key_measurement"]
    data["adapter_edge"]["interval"] = [start, end]
    interval_name = "physical_down_interval" if edge_name == "down" else "physical_up_interval"
    data["bracket"][interval_name] = [start, end]
    pre, post = data["pre_sample"], data["post_sample"]
    pre["started_ns"] = pre["finished_ns"] = start
    post["started_ns"] = start
    post["finished_ns"] = end
    if edge_name == "down":
        data["press_request_ns"] = start
        data["sync_return_ns"] = start
        row["admitted_ns"] = start
        row["input_ack_ns"] = start
    else:
        data["release_request_ns"] = start
        data["sync_return_ns"] = start


def project(projector, events):
    receipts = projector(events)
    row = next(row for row in receipts if row.get("status", "").startswith("adapter_edge_"))
    return {
        "status": row["status"],
        "down_edge_interval_ns": row.get("down_edge_interval_ns"),
        "up_edge_interval_ns": row.get("up_edge_interval_ns"),
        "grants_input_authority": row.get("grants_input_authority"),
        "application_consumption_observed": row.get("application_consumption_observed"),
    }


def main():
    frozen = frozen_source()
    current_path = ROOT.parent / "map01_overlap_controller_v39.py"
    current = current_path.read_text(encoding="utf-8")
    baseline_projector = load_projector(frozen, f"{SOURCE_COMMIT}:{SOURCE_PATH}")
    candidate_projector = load_projector(current, str(current_path))
    template = [json.loads(line) for line in FIXTURE_PATH.read_text().splitlines() if line]
    down = next(row for row in template if row.get("event") == "input_admission")
    up = next(row for row in template if row.get("event") == "input_release_measurement")
    set_edge_interval(down, "down", 0, 1)
    set_edge_interval(up, "up", 2, 3)
    positive = json.loads(json.dumps(template))
    baseline_positive = project(baseline_projector, positive)
    candidate_positive = project(candidate_projector, positive)

    mutations = []
    for label, replacement, endpoint in (
            ("down_lower_false_alias", False, 0),
            ("down_upper_true_alias", True, 1)):
        mutated = json.loads(json.dumps(positive))
        bracket = mutated[0]["physical_key_measurement"]["bracket"]["physical_down_interval"]
        original = bracket[endpoint]
        bracket[endpoint] = replacement
        mutations.append({
            "case": label, "row_index": 0, "endpoint": endpoint,
            "before": original, "mutated": replacement,
            "baseline": project(baseline_projector, mutated),
            "candidate": project(candidate_projector, mutated),
        })

    source_blob = subprocess.run(
        ["git", "rev-parse", f"{SOURCE_COMMIT}:{SOURCE_PATH}"],
        check=True, capture_output=True, text=True).stdout.strip()
    output = {
        "schema": "v39-bracket-time-type-alias-a01-v1",
        "source_commit": SOURCE_COMMIT,
        "source_git_blob": source_blob,
        "source_sha256_before": hashlib.sha256(frozen.encode()).hexdigest(),
        "source_sha256_candidate": hashlib.sha256(current.encode()).hexdigest(),
        "input_sha256": hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest(),
        "positive": {"baseline": baseline_positive, "candidate": candidate_positive},
        "mutations": mutations,
        "decision": "PASS_TYPE_ALIAS_REJECTED" if (
            baseline_positive["status"] == "adapter_edge_brackets_paired" and
            candidate_positive["status"] == "adapter_edge_brackets_paired" and
            all(row["candidate"]["status"] == "adapter_edge_receipt_incomplete" and
                row["candidate"]["down_edge_interval_ns"] is None and
                row["candidate"]["up_edge_interval_ns"] is None for row in mutations))
            else "FAIL_TYPE_ALIAS_ACCEPTED",
        "scope": "deterministic source projection over retained X-server sampling rows; no live input or application claim",
    }
    out = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "raw/A01.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["decision"] == "PASS_TYPE_ALIAS_REJECTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
