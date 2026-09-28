"""Run and retain the host-only W2 close-order candidate/oracle matrix."""
import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path


FIXTURE_SHA256 = "6a693f06b1b4be15a8da35ec3aaf806d7fb3601091c8ef638c516069d1b4e95f"
CASES = {
    "no_close": {"expected": ["AUTHORIZED_MATCH", "AUTHORIZED_MATCH"]},
    "pre_close": {"close_time": 450, "expected": ["AUTHORIZED_MATCH", "AUTHORIZED_MATCH"]},
    "post_close": {"close_time": 50, "expected": ["REJECT_EDGE_AFTER_LEASE_CLOSE"] * 2},
    "overlap": {"close_time": 50, "overlap_down": True,
                "expected": ["HOLD_EDGE_CLOSE_ORDER_UNCERTAIN", "REJECT_EDGE_AFTER_LEASE_CLOSE"]},
    "foreign_close": {"close_time": 50, "close_actuation": "FOREIGN-ACTUATION",
                       "expected": ["HOLD_CLOSE_LINEAGE_UNRESOLVED"] * 2},
    "missing_close": {"close_time": 50, "close_actuation": None,
                       "expected": ["HOLD_CLOSE_LINEAGE_UNRESOLVED"] * 2},
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def make_trace(fixture, spec):
    document = copy.deepcopy(fixture)
    target = next(c for c in document["cases"] if c["case_id"] == "release-before-terminal")
    opened = next(e for e in target["events"] if e["event_type"] == "LEASE_OPEN")
    opened["lineage"]["actuation_id"] = "A4"
    if spec.get("overlap_down"):
        down = next(e for e in target["events"] if e.get("event_type") == "INPUT_EDGE_BRACKET" and e["payload"]["edge"] == "down")
        down["time"] = {"lower_ns": 45, "upper_ns": 55, "censoring": "bounded"}
        down["payload"]["transition_interval_ns"] = [45, 55]
    close_time = spec.get("close_time")
    if close_time is not None:
        actuation = spec.get("close_actuation", "A4")
        lineage = {"lease_id": "L4", "parent_event_ids": []}
        if actuation is not None:
            lineage["actuation_id"] = actuation
        close = {
            "event_id": "close-order-matrix-close",
            "event_type": "LEASE_CLOSE",
            "source_role": "executor",
            "clock": copy.deepcopy(opened["clock"]),
            "time": {"lower_ns": close_time, "upper_ns": close_time, "censoring": "exact"},
            "input_authority": "false",
            "semantic_authority": "false",
            "lineage": lineage,
            "payload": {},
        }
        target["events"].append(close)
        target["events"].sort(key=lambda event: event["time"]["lower_ns"])
    return document


def run(argv):
    p = subprocess.run(argv, capture_output=True, text=True, check=False)
    return {"exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def statuses(report_path):
    report = json.loads(report_path.read_text(encoding="utf-8"))
    target = next(c for c in report["cases"] if c["case_id"] == "release-before-terminal")
    return [d["status"] for d in target["decisions"]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.exists():
        raise SystemExit("STOP_OUTPUT_DIRECTORY_EXISTS")
    output.mkdir(parents=True)
    fixture_bytes = args.fixture.read_bytes()
    if sha256(fixture_bytes) != FIXTURE_SHA256:
        raise SystemExit("STOP_FROZEN_FIXTURE_SHA256_MISMATCH")
    fixture = json.loads(fixture_bytes)
    retained = {}
    for name, spec in CASES.items():
        case_dir = output / name
        case_dir.mkdir()
        trace = case_dir / "trace-cases.json"
        candidate = case_dir / "candidate.json"
        audit = case_dir / "audit.json"
        trace.write_text(json.dumps(make_trace(fixture, spec), indent=2) + "\n", encoding="utf-8")
        candidate_run = run([sys.executable, str(Path(__file__).with_name("close_order_cli.py")),
                             "--traces", str(trace), "--out", str(candidate)])
        if candidate_run["exit_code"] != 0:
            raise SystemExit("STOP_CANDIDATE_RUN:" + name)
        audit_run = run([sys.executable, str(Path(__file__).with_name("audit_close_order_cli.py")),
                         "--traces", str(trace), "--candidate", str(candidate), "--out", str(audit)])
        if audit_run["exit_code"] != 0:
            raise SystemExit("STOP_RAW_AUDIT:" + name)
        actual = statuses(candidate)
        audit_doc = json.loads(audit.read_text(encoding="utf-8"))
        if actual != spec["expected"] or audit_doc["errors"]:
            raise SystemExit("FAIL_MATRIX_DECISION:" + name)
        retained[name] = {
            "expected_target_decisions": spec["expected"],
            "candidate_cli": candidate_run,
            "auditor_cli": audit_run,
            "audit_disposition": audit_doc["disposition"],
            "audit_errors": audit_doc["errors"],
            "decision_rows": audit_doc["decision_rows"],
            "outputs_sha256": {
                "trace-cases.json": sha256(trace.read_bytes()),
                "candidate.json": sha256(candidate.read_bytes()),
                "audit.json": sha256(audit.read_bytes()),
            },
        }

    tamper_dir = output / "tampered_candidate_control"
    tamper_dir.mkdir()
    source_report = output / "post_close" / "candidate.json"
    tampered = json.loads(source_report.read_text(encoding="utf-8"))
    target = next(c for c in tampered["cases"] if c["case_id"] == "release-before-terminal")
    target["decisions"][0]["status"] = "AUTHORIZED_MATCH"
    tampered_path = tamper_dir / "candidate.json"
    tampered_path.write_text(json.dumps(tampered, indent=2) + "\n", encoding="utf-8")
    audit_path = tamper_dir / "audit.json"
    raw_trace = output / "post_close" / "trace-cases.json"
    tamper_run = run([sys.executable, str(Path(__file__).with_name("audit_close_order_cli.py")),
                      "--traces", str(raw_trace), "--candidate", str(tampered_path), "--out", str(audit_path)])
    if tamper_run["exit_code"] != 1 or "candidate_raw_disagreement:release-before-terminal" not in tamper_run["stdout"]:
        raise SystemExit("FAIL_TAMPER_CONTROL_ESCAPED")

    result = {
        "schema": "w2-lease-close-candidate-matrix-result-v1",
        "disposition": "PASS_HOST_CLOSE_ORDER_CANDIDATE_MATRIX_ONLY",
        "source_main_snapshot": "611962d32477f8a86096431227a819418ceef994",
        "fixture_sha256": FIXTURE_SHA256,
        "runtime": sys.version,
        "container": False,
        "matrix": retained,
        "tamper_control": {
            "auditor_exit_code": tamper_run["exit_code"],
            "auditor_stdout": tamper_run["stdout"],
            "auditor_stderr": tamper_run["stderr"],
            "tampered_candidate_sha256": sha256(tampered_path.read_bytes()),
            "audit_sha256": sha256(audit_path.read_bytes()),
            "audit_errors": json.loads(audit_path.read_text(encoding="utf-8"))["errors"],
        },
        "limits": [
            "Synthetic host-CPU candidate construction only; not Docker/formal evidence.",
            "Foreign or missing close actuation lineage conservatively HOLD; no broader close policy is claimed.",
            "No live authority, GUI, model, task effect, or runtime integration is tested.",
        ],
    }
    result_path = output / "RESULT.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": result["disposition"], "matrix_cases": len(retained),
                      "tamper_exit": tamper_run["exit_code"], "result_sha256": sha256(result_path.read_bytes())}, indent=2))


if __name__ == "__main__":
    main()
