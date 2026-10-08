"""Run preregistered completion-sentinel mutations against the frozen T3 CLI."""
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from test_audit_formal_x11 import fixture_rows  # noqa: E402


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mutate(rows, kind):
    complete = [row for row in rows if row.get("event") == "runner_complete"]
    if len(complete) != 1:
        raise ValueError(f"fixture requires exactly one runner_complete row, got {len(complete)}")
    row = complete[0]
    if kind == "unchanged":
        return rows
    if kind == "exit_code_false":
        row["exit_code"] = False
    elif kind == "exit_code_float_zero":
        row["exit_code"] = 0.0
    elif kind == "exit_code_string_zero":
        row["exit_code"] = "0"
    elif kind == "exit_code_null":
        row["exit_code"] = None
    elif kind == "remove_exit_code":
        row.pop("exit_code")
    elif kind == "exit_code_one":
        row["exit_code"] = 1
    elif kind == "append_integer_zero_completion":
        rows.append(copy.deepcopy(row))
    elif kind == "append_nonzero_completion":
        extra = copy.deepcopy(row)
        extra["exit_code"] = 2
        rows.append(extra)
    else:
        raise ValueError(f"unknown mutation: {kind}")
    return rows


def write_json(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def run(results_dir):
    out = Path(results_dir).resolve()
    if not out.is_dir() or any(out.iterdir()):
        raise SystemExit("results directory must exist and be empty")
    spec = json.loads((HERE / "EXPERIMENT_SPEC.json").read_text(encoding="utf-8"))
    expected = json.loads((HERE / "EXPECTED.json").read_text(encoding="utf-8"))
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    if freeze.get("status") != "START_GATE_PASSED" or not freeze.get("slot_start_main"):
        raise SystemExit("frozen start gate is not passed")
    (out / "raw").mkdir()
    (out / "audits").mkdir()
    (out / "stdout").mkdir()
    (out / "stderr").mkdir()
    cases = [spec["control"], *spec["mutations"]]
    results = []
    for case in cases:
        rows = mutate(copy.deepcopy(fixture_rows()), case["kind"])
        raw_path = out / "raw" / f"{case['id']}.jsonl"
        raw_path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
                                       for row in rows), encoding="utf-8", newline="\n")
        audit_path = out / "audits" / f"{case['id']}.json"
        proc = subprocess.run(
            [sys.executable, "-B", str(HERE / "audit_formal_x11.py"), str(raw_path),
             str(HERE / "EXPECTED.json"), str(audit_path), "synthetic-cli"],
            cwd=HERE, capture_output=True, text=True, timeout=10, check=False)
        (out / "stdout" / f"{case['id']}.txt").write_text(proc.stdout, encoding="utf-8")
        (out / "stderr" / f"{case['id']}.txt").write_text(proc.stderr, encoding="utf-8")
        audit = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.is_file() else {}
        results.append({
            "id": case["id"], "kind": case["kind"],
            "expected_audit_exit": case["expected_audit_exit"],
            "observed_audit_exit": proc.returncode,
            "audit_status": audit.get("status"),
            "raw_sha256": sha256(raw_path), "audit_sha256": sha256(audit_path) if audit_path.is_file() else None,
            "stdout_sha256": sha256(out / "stdout" / f"{case['id']}.txt"),
            "stderr_sha256": sha256(out / "stderr" / f"{case['id']}.txt"),
        })
    expectation_match = all(row["expected_audit_exit"] == row["observed_audit_exit"] for row in results)
    report = {
        "schema": "runner-completion-sentinel-experiment-v1",
        "allocation": spec["allocation"],
        "target_pr_head": spec["target_pr_head"],
        "main_at_run": freeze["slot_start_main"],
        "target_auditor_sha256": sha256(HERE / "audit_formal_x11.py"),
        "expected_sha256": sha256(HERE / "EXPECTED.json"),
        "spec_sha256": sha256(HERE / "EXPERIMENT_SPEC.json"),
        "freeze_sha256": sha256(HERE / "FREEZE.json"),
        "fixture_source_sha256": sha256(HERE / "test_audit_formal_x11.py"),
        "candidate_sha256": sha256(HERE / "run_mutation_experiment.py"),
        "container_platform": "linux/arm64",
        "synthetic_only": True,
        "target_mutation_cases": len(spec["mutations"]),
        "control_cases": 1,
        "expectation_match": expectation_match,
        "scientific_disposition": ("PASS_COMPLETION_SENTINEL_HYPOTHESIS_SCOPED"
                                   if expectation_match else "FAIL_EXPERIMENTAL_EXPECTATION"),
        "cases": results,
        "scope": "synthetic JSONL CLI-boundary experiment only; no X11, physical input, MAP01, or task effect",
    }
    write_json(out / "RUN.json", report)
    print(json.dumps({"allocation": spec["allocation"], "candidate_status": report["scientific_disposition"],
                      "cases": [{"id": x["id"], "exit": x["observed_audit_exit"]} for x in results]},
                     sort_keys=True))
    return 0 if expectation_match else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: run_mutation_experiment.py EMPTY_RESULTS_DIR")
    raise SystemExit(run(sys.argv[1]))
