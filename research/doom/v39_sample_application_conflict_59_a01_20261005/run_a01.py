"""Compare exact #7662 parent and candidate across application-flag layers."""
import ast
import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_projector(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    node = next(row for row in tree.body
                if isinstance(row, ast.FunctionDef) and
                row.name == "input_edge_receipts")
    namespace = {"hashlib": hashlib}
    exec(compile(ast.fix_missing_locations(ast.Module(
        body=[node], type_ignores=[])), str(path), "exec"), namespace)
    return namespace["input_edge_receipts"]


def receipt(projector, rows):
    row = projector(rows)[0]
    return {key: row.get(key) for key in (
        "status", "down_edge_interval_ns", "up_edge_interval_ns")}


def set_flag(rows, row_index, layer, value):
    row = rows[row_index]
    if layer == "event":
        target = row
    else:
        measurement = row["physical_key_measurement"]
        target = {
            "measurement": measurement,
            "adapter_edge": measurement["adapter_edge"],
            "bracket": measurement["bracket"],
            "pre_sample": measurement["pre_sample"],
            "post_sample": measurement["post_sample"],
        }[layer]
    target["application_consumption_observed"] = value


def main():
    baseline_path = ROOT / "BASELINE_SOURCE.py.txt"
    candidate_path = ROOT / "CANDIDATE_SOURCE.py.txt"
    input_path = ROOT / "INPUT.jsonl"
    baseline = load_projector(baseline_path)
    candidate = load_projector(candidate_path)
    template = [json.loads(line) for line in
                input_path.read_text(encoding="utf-8").splitlines() if line]
    expected_layers = ("event", "measurement", "adapter_edge", "bracket",
                       "pre_sample", "post_sample")
    expected_values = (("true", True), ("int_one", 1), ("int_zero", 0),
                       ("null", None), ("string_false", "false"))
    mutations = []
    for row_index in range(2):
        for layer in expected_layers:
            for value_name, value in expected_values:
                changed = copy.deepcopy(template)
                set_flag(changed, row_index, layer, value)
                mutations.append({
                    "row_index": row_index,
                    "layer": layer,
                    "value": value_name,
                    "baseline": receipt(baseline, changed),
                    "candidate": receipt(candidate, changed),
                })

    valid_baseline = receipt(baseline, template)
    valid_candidate = receipt(candidate, template)
    baseline_false_accepts = [row for row in mutations
                              if row["baseline"]["status"] ==
                              "adapter_edge_brackets_paired"]
    candidate_false_accepts = [row for row in mutations
                               if row["candidate"]["status"] ==
                               "adapter_edge_brackets_paired"]
    result = {
        "protocol": "v39-sample-application-conflict-a01-v1",
        "sources": {
            "baseline_sha256": sha256(baseline_path),
            "candidate_sha256": sha256(candidate_path),
            "input_sha256": sha256(input_path),
        },
        "valid_control": {"baseline": valid_baseline,
                          "candidate": valid_candidate},
        "mutation_count": len(mutations),
        "baseline_false_accept_count": len(baseline_false_accepts),
        "baseline_false_accepts": baseline_false_accepts,
        "candidate_false_accept_count": len(candidate_false_accepts),
        "candidate_false_accepts": candidate_false_accepts,
        "mutations": mutations,
        "scope": "Deterministic AST-extracted projection comparison only; no X server, live input, game, model, task feedback, or allocation.",
    }
    result["candidate_pass"] = (
        len(mutations) == 60 and
        valid_baseline["status"] == "adapter_edge_brackets_paired" and
        valid_candidate["status"] == "adapter_edge_brackets_paired" and
        len(baseline_false_accepts) == 20 and
        all(row["layer"] in ("pre_sample", "post_sample")
            for row in baseline_false_accepts) and
        not candidate_false_accepts and
        all(row["candidate"]["status"] == "adapter_edge_receipt_incomplete" and
            row["candidate"]["down_edge_interval_ns"] is None and
            row["candidate"]["up_edge_interval_ns"] is None
            for row in mutations))
    target = ROOT / "raw" / "A01.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({
        "status": "PASS" if result["candidate_pass"] else "FAIL",
        "baseline_false_accepts": len(baseline_false_accepts),
        "candidate_false_accepts": len(candidate_false_accepts),
        "mutations": len(mutations),
        "valid_control": valid_candidate["status"],
        "raw": str(target.relative_to(ROOT)),
    }, indent=2, sort_keys=True))
    return 0 if result["candidate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
