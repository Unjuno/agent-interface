#!/usr/bin/env python3
"""Independent replay and integrity audit for bracket timestamp type alias A01."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8-sig"))
SOURCE = ROOT.parent / "map01_overlap_controller_v39.py"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def source_at(commit, path):
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        check=True, stdout=subprocess.PIPE).stdout.decode("utf-8")


def extract(source, label):
    tree = ast.parse(source)
    node = next(row for row in tree.body
                if isinstance(row, ast.FunctionDef) and row.name == "input_edge_receipts")
    namespace = {"hashlib": hashlib}
    exec(compile(ast.fix_missing_locations(ast.Module(
        body=[node], type_ignores=[])), label, "exec"), namespace)
    return namespace["input_edge_receipts"], node


def interval(row, edge_name, start, end):
    data = row["physical_key_measurement"]
    data["adapter_edge"]["interval"] = [start, end]
    bracket_name = "physical_down_interval" if edge_name == "down" else "physical_up_interval"
    data["bracket"][bracket_name] = [start, end]
    pre, post = data["pre_sample"], data["post_sample"]
    pre["started_ns"] = pre["finished_ns"] = start
    post["started_ns"], post["finished_ns"] = start, end
    if edge_name == "down":
        data["press_request_ns"] = data["sync_return_ns"] = start
        row["admitted_ns"] = row["input_ack_ns"] = start
    else:
        data["release_request_ns"] = data["sync_return_ns"] = start


def result(projector, rows):
    matches = [row for row in projector(rows)
               if row.get("status", "").startswith("adapter_edge_")]
    if len(matches) != 1:
        return {"status": "unexpected_receipt_count", "count": len(matches)}
    row = matches[0]
    return {key: row.get(key) for key in (
        "status", "down_edge_interval_ns", "up_edge_interval_ns",
        "grants_input_authority", "application_consumption_observed")}


def has_exact_bracket_interval_check(node):
    nested = next((row for row in node.body
                   if isinstance(row, ast.FunctionDef) and row.name == "bracket_matches"), None)
    if nested is None:
        return False
    for row in ast.walk(nested):
        if not isinstance(row, ast.Call) or not isinstance(row.func, ast.Name):
            continue
        if row.func.id != "valid_interval" or len(row.args) != 1:
            continue
        arg = row.args[0]
        if (isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute) and
                arg.func.attr == "get" and isinstance(arg.func.value, ast.Name) and
                arg.func.value.id == "bracket" and len(arg.args) == 1 and
                isinstance(arg.args[0], ast.Name) and arg.args[0].id == "interval_name"):
            return True
    return False


def main():
    path = FREEZE["source_path"]
    frozen = source_at(FREEZE["source_commit"], path)
    current = SOURCE.read_text(encoding="utf-8")
    baseline, _ = extract(frozen, "frozen-baseline")
    candidate, candidate_node = extract(current, "candidate")
    rows = [json.loads(line) for line in
            (ROOT / "INPUT.jsonl").read_text(encoding="utf-8-sig").splitlines() if line]
    down = next(row for row in rows if row.get("event") == "input_admission")
    up = next(row for row in rows if row.get("event") == "input_release_measurement")
    interval(down, "down", 0, 1)
    interval(up, "up", 2, 3)
    positive = json.loads(json.dumps(rows))
    positive_result = result(candidate, positive)
    mutations = []
    for case, endpoint, value in (
            ("down_lower_false_alias", 0, False),
            ("down_upper_true_alias", 1, True)):
        mutated = json.loads(json.dumps(positive))
        bracket = mutated[0]["physical_key_measurement"]["bracket"]["physical_down_interval"]
        bracket[endpoint] = value
        mutations.append({
            "case": case,
            "baseline": result(baseline, mutated),
            "candidate": result(candidate, mutated),
        })
    raw_red = json.loads((ROOT / "raw/A01-red.json").read_text())
    raw_green = json.loads((ROOT / "raw/A01-green.json").read_text())
    checks = {
        "frozen_source_sha_matches": sha256(frozen.encode()) == FREEZE["source_sha256"],
        "local_fixture_sha_matches": sha256((ROOT / "INPUT.jsonl").read_bytes()) ==
                                     FREEZE["local_fixture_sha256"],
        "runner_sha_matches": sha256((ROOT / "run_a01.py").read_bytes()) ==
                              FREEZE["runner_sha256"],
        "candidate_source_sha_matches_green_raw": sha256(current.encode()) ==
                                                  raw_green["source_sha256_candidate"],
        "positive_control_stays_paired": positive_result["status"] == "adapter_edge_brackets_paired",
        "baseline_accepts_each_bool_alias": all(
            row["baseline"]["status"] == "adapter_edge_brackets_paired" and
            row["baseline"]["down_edge_interval_ns"] is not None and
            row["baseline"]["up_edge_interval_ns"] is not None for row in mutations),
        "candidate_rejects_each_bool_alias": all(
            row["candidate"]["status"] == "adapter_edge_receipt_incomplete" and
            row["candidate"]["down_edge_interval_ns"] is None and
            row["candidate"]["up_edge_interval_ns"] is None for row in mutations),
        "source_validates_exact_bracket_interval": has_exact_bracket_interval_check(candidate_node),
        "retained_red_records_false_accept": raw_red["decision"] == "FAIL_TYPE_ALIAS_ACCEPTED" and
            all(row["candidate"]["status"] == "adapter_edge_brackets_paired"
                for row in raw_red["mutations"]),
        "retained_green_records_rejection": raw_green["decision"] == "PASS_TYPE_ALIAS_REJECTED" and
            all(row["candidate"]["status"] == "adapter_edge_receipt_incomplete"
                for row in raw_green["mutations"]),
        "retained_green_matches_independent_replay": all(
            raw_green["mutations"][i]["candidate"] == mutations[i]["candidate"]
            for i in range(2)),
    }
    out = {
        "schema": "v39-bracket-time-type-alias-audit-v1",
        "checks": checks,
        "positive": positive_result,
        "mutations": mutations,
        "decision": "PASS_INDEPENDENT_REPLAY" if all(checks.values()) else "FAIL",
        "scope": "source/fixture/raw replay only; no live input, application, game, model, or task effect",
    }
    (ROOT / "raw/AUDIT.json").write_text(
        json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out["decision"] == "PASS_INDEPENDENT_REPLAY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
