"""Independent raw-only audit of candidate receipts and all mutation inputs."""
import hashlib
import json
import sys
from pathlib import Path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(source_dir, results_dir):
    source, out = Path(source_dir), Path(results_dir)
    errors = []
    spec = json.loads((source / "EXPERIMENT_SPEC.json").read_text(encoding="utf-8"))
    run = json.loads((out / "RUN.json").read_text(encoding="utf-8"))
    if run.get("allocation") != spec.get("allocation"):
        errors.append("allocation mismatch")
    freeze = json.loads((source / "FREEZE.json").read_text(encoding="utf-8"))
    if run.get("main_at_run") != freeze.get("slot_start_main") or not run.get("main_at_run"):
        errors.append("current-main freeze mismatch")
    pins = {
        "target_auditor_sha256": "audit_formal_x11.py",
        "expected_sha256": "EXPECTED.json",
        "spec_sha256": "EXPERIMENT_SPEC.json",
        "freeze_sha256": "FREEZE.json",
        "fixture_source_sha256": "test_audit_formal_x11.py",
        "candidate_sha256": "run_mutation_experiment.py",
    }
    for field, filename in pins.items():
        if run.get(field) != sha256(source / filename):
            errors.append(f"source hash mismatch: {field}")
    host_path = out / "candidate-host-receipt.json"
    if not host_path.is_file():
        errors.append("candidate host receipt missing")
    else:
        host = json.loads(host_path.read_text(encoding="utf-8"))
        if (host.get("candidate_exit_code") != 0 or type(host.get("candidate_exit_code")) is not int
                or host.get("engine_context") != "orbstack"
                or host.get("image_digest") != "sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a"
                or host.get("image_id") != host.get("image_digest")
                or host.get("platform") != "linux/amd64"):
            errors.append("candidate host receipt runtime identity/exit invalid")
        if (not isinstance(host.get("container_id"), str) or len(host["container_id"]) != 64
                or any(c not in "0123456789abcdef" for c in host["container_id"])):
            errors.append("candidate host receipt container ID invalid")
        if host.get("stdout_sha256") != sha256(out / "container.stdout.txt"):
            errors.append("candidate host stdout hash mismatch")
        if host.get("stderr_sha256") != sha256(out / "container.stderr.txt"):
            errors.append("candidate host stderr hash mismatch")
        if host.get("run_receipt_sha256") != sha256(out / "RUN.json"):
            errors.append("candidate RUN receipt binding mismatch")
        argv = host.get("argv")
        if (not isinstance(argv, list) or "--pull=never" not in argv or "--network" not in argv
                or argv[argv.index("--network") + 1:argv.index("--network") + 2] != ["none"]
                or "--read-only" not in argv or "--entrypoint" not in argv
                or "--cpus=1" not in argv or "--memory=256m" not in argv or "--pids-limit=32" not in argv
                or not any(isinstance(arg, str) and arg.startswith("type=bind,source=") and arg.endswith(",readonly")
                           for arg in argv)):
            errors.append("candidate host argv is not bounded and offline")
    expected_cases = {item["id"]: item for item in [spec["control"], *spec["mutations"]]}
    rows = run.get("cases")
    if not isinstance(rows, list) or {row.get("id") for row in rows} != set(expected_cases) or len(rows) != len(expected_cases):
        errors.append("case inventory mismatch")
        rows = rows if isinstance(rows, list) else []
    for item in rows:
        case_id = item.get("id")
        if case_id not in expected_cases:
            continue
        frozen = expected_cases[case_id]
        raw_path = out / "raw" / f"{case_id}.jsonl"
        audit_path = out / "audits" / f"{case_id}.json"
        stdout_path = out / "stdout" / f"{case_id}.txt"
        stderr_path = out / "stderr" / f"{case_id}.txt"
        for field, path in (("raw_sha256", raw_path), ("audit_sha256", audit_path),
                            ("stdout_sha256", stdout_path), ("stderr_sha256", stderr_path)):
            if not path.is_file() or item.get(field) != sha256(path):
                errors.append(f"artifact hash mismatch: {case_id}/{field}")
        if item.get("kind") != frozen["kind"] or item.get("expected_audit_exit") != frozen["expected_audit_exit"]:
            errors.append(f"preregistered expectation mismatch: {case_id}")
        if item.get("observed_audit_exit") != frozen["expected_audit_exit"]:
            errors.append(f"auditor exit mismatch: {case_id}")
        if not raw_path.is_file() or not audit_path.is_file():
            continue
        raw_rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line]
        completions = [r for r in raw_rows if r.get("event") == "runner_complete"]
        kind = frozen["kind"]
        if kind == "unchanged":
            valid = len(completions) == 1 and type(completions[0].get("exit_code")) is int and completions[0]["exit_code"] == 0
        elif kind == "exit_code_false":
            valid = len(completions) == 1 and type(completions[0].get("exit_code")) is bool and completions[0]["exit_code"] is False
        elif kind == "exit_code_float_zero":
            valid = len(completions) == 1 and type(completions[0].get("exit_code")) is float and completions[0]["exit_code"] == 0.0
        elif kind == "exit_code_string_zero":
            valid = len(completions) == 1 and completions[0].get("exit_code") == "0"
        elif kind == "exit_code_null":
            valid = len(completions) == 1 and "exit_code" in completions[0] and completions[0]["exit_code"] is None
        elif kind == "remove_exit_code":
            valid = len(completions) == 1 and "exit_code" not in completions[0]
        elif kind == "exit_code_one":
            valid = len(completions) == 1 and type(completions[0].get("exit_code")) is int and completions[0]["exit_code"] == 1
        elif kind == "append_integer_zero_completion":
            valid = len(completions) == 2 and all(type(r.get("exit_code")) is int and r["exit_code"] == 0 for r in completions)
        elif kind == "append_nonzero_completion":
            valid = len(completions) == 2 and [r.get("exit_code") for r in completions] == [0, 2]
        else:
            valid = False
        if not valid:
            errors.append(f"raw mutation malformed: {case_id}")
        audited = json.loads(audit_path.read_text(encoding="utf-8"))
        expected_status = "PASS_SYNTHETIC_RAW_ONLY_CLI_BOUNDARY" if frozen["expected_audit_exit"] == 0 else "FAIL_AUDIT"
        if audited.get("status") != expected_status:
            errors.append(f"audit status mismatch: {case_id}")
        if audited.get("allocation") != json.loads((source / "EXPECTED.json").read_text(encoding="utf-8")).get("allocation"):
            errors.append(f"audit allocation mismatch: {case_id}")
    if run.get("expectation_match") is not True or run.get("scientific_disposition") != "PASS_COMPLETION_SENTINEL_HYPOTHESIS_SCOPED":
        errors.append("candidate did not satisfy preregistered experiment disposition")
    return errors


def main(source_dir, results_dir):
    errors = audit(source_dir, results_dir)
    print(json.dumps({"status": "PASS_INDEPENDENT_COMPLETION_SENTINEL_AUDIT" if not errors else "FAIL_INDEPENDENT_AUDIT",
                      "errors": errors, "results_sha256": sha256(Path(results_dir) / "RUN.json")}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit_mutation_experiment.py SOURCE_DIR RESULTS_DIR")
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
