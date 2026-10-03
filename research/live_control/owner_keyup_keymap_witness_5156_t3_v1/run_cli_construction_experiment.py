"""One-shot host-only synthetic candidate followed by separate raw-only audit."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest() if Path(path).is_file() else None


def invoke_once(argv, timeout_seconds):
    child = subprocess.Popen(argv, cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    try:
        stdout, stderr = child.communicate(timeout=timeout_seconds)
        return {"pid": child.pid, "returncode": child.returncode, "stdout": stdout,
                "stderr": stderr, "timed_out": False}
    except subprocess.TimeoutExpired:
        child.kill()
        stdout, stderr = child.communicate()
        return {"pid": child.pid, "returncode": None, "stdout": stdout,
                "stderr": stderr, "timed_out": True}


def run(results_dir):
    results = Path(results_dir).resolve()
    results.mkdir(parents=True, exist_ok=False)
    expected_path = HERE / "EXPECTED.json"
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    raw_path = results / "raw.jsonl"
    started = datetime.now(timezone.utc).isoformat()

    candidate = invoke_once([sys.executable, "-B", str(HERE / "emit_synthetic_candidate.py"), str(raw_path)], 10)
    (results / "candidate.stdout.txt").write_text(candidate["stdout"], encoding="utf-8")
    (results / "candidate.stderr.txt").write_text(candidate["stderr"], encoding="utf-8")

    auditor = None
    if candidate["returncode"] == 0:
        auditor = invoke_once([sys.executable, "-B", str(HERE / "audit_formal_x11.py"),
                               str(raw_path), str(expected_path), str(results / "audit.json"),
                               "synthetic-cli"], 10)
        (results / "auditor.stdout.txt").write_text(auditor["stdout"], encoding="utf-8")
        (results / "auditor.stderr.txt").write_text(auditor["stderr"], encoding="utf-8")

    audit_data = {}
    audit_path = results / "audit.json"
    if audit_path.is_file():
        audit_data = json.loads(audit_path.read_text(encoding="utf-8"))
    disposition = ("PASS_SYNTHETIC_RAW_ONLY_CLI_BOUNDARY"
                   if candidate["returncode"] == 0 and auditor is not None
                   and auditor["returncode"] == 0
                   and audit_data.get("status") == "PASS_SYNTHETIC_RAW_ONLY_CLI_BOUNDARY"
                   else "SYNTHETIC_CLI_BOUNDARY_NOT_PASS")
    report = {
        "schema": "synthetic-raw-only-cli-boundary-v1",
        "synthetic_only": True,
        "container_or_x11_used": False,
        "started_at_utc": started,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "allocation_label": expected["allocation"],
        "frozen_main": expected["frozen_main"],
        "candidate_invocations": 1,
        "candidate_pid": candidate["pid"],
        "candidate_returncode": candidate["returncode"],
        "candidate_timed_out": candidate["timed_out"],
        "auditor_invocations": int(auditor is not None),
        "auditor_pid": auditor["pid"] if auditor else None,
        "audit_returncode": auditor["returncode"] if auditor else None,
        "audit_timed_out": auditor["timed_out"] if auditor else False,
        "audit_status": audit_data.get("status"),
        "raw_sha256": sha256(raw_path),
        "candidate_sha256": sha256(HERE / "emit_synthetic_candidate.py"),
        "auditor_sha256": sha256(HERE / "audit_formal_x11.py"),
        "candidate_fixture_source_sha256": sha256(HERE / "test_audit_formal_x11.py"),
        "experiment_driver_sha256": sha256(HERE / "run_cli_construction_experiment.py"),
        "expected_sha256": sha256(expected_path),
        "disposition": disposition,
        "scope": "synthetic JSONL serialization/process boundary only; no X server or physical input evidence",
    }
    (results / "RUN.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if disposition == "PASS_SYNTHETIC_RAW_ONLY_CLI_BOUNDARY" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.results))
