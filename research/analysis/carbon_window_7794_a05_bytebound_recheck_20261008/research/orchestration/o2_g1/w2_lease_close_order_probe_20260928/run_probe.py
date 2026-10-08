"""Paired host-CPU probe for frozen W2 LEASE_CLOSE ordering.

This is an append-only diagnostic. It reads frozen sources/fixture, creates a
matched control and a one-event treatment in a fresh output directory, then
invokes the original verifier and raw auditor as separate CLIs.
"""
import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path


EXPECTED_BLOBS = {
    "verify_contract.py": "d8f4221811b160e5714d2d6e4154c82af94d633e",
    "audit_contract.py": "1942546e60ad7e6cb56b9a383830033db14d0397",
    "event-schema.json": "ebc424d2df631aa74c6d9aee4699c595a27ed589",
    "trace-cases.json": "0a49a00567c25766495cd332be50f6c2946781f7",
}
EXPECTED_FIXTURE_SHA256 = "6a693f06b1b4be15a8da35ec3aaf806d7fb3601091c8ef638c516069d1b4e95f"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def invoke(argv):
    p = subprocess.run(argv, text=True, capture_output=True, check=False)
    return {"argv": [str(x) for x in argv], "exit_code": p.returncode,
            "stdout": p.stdout, "stderr": p.stderr}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_dir.resolve(strict=True)
    out = args.output_dir.resolve()
    if out.exists():
        raise SystemExit("STOP_OUTPUT_DIRECTORY_EXISTS")
    out.mkdir(parents=True)

    pinned = {}
    for name, expected in EXPECTED_BLOBS.items():
        data = (source / name).read_bytes()
        actual = git_blob_sha(data)
        if actual != expected:
            raise SystemExit(f"STOP_SOURCE_BLOB_MISMATCH:{name}:{actual}")
        pinned[name] = {"git_blob": actual, "sha256": sha256(data)}

    fixture_bytes = (source / "trace-cases.json").read_bytes()
    if sha256(fixture_bytes) != EXPECTED_FIXTURE_SHA256:
        raise SystemExit("STOP_FIXTURE_SHA256_MISMATCH")
    original = json.loads(fixture_bytes)
    control = copy.deepcopy(original)
    target = next(c for c in control["cases"] if c["case_id"] == "release-before-terminal")
    lease_open = next(e for e in target["events"] if e["event_type"] == "LEASE_OPEN")
    lease_open["lineage"]["actuation_id"] = "A4"
    treatment = copy.deepcopy(control)
    target = next(c for c in treatment["cases"] if c["case_id"] == "release-before-terminal")
    open_event = next(e for e in target["events"] if e["event_type"] == "LEASE_OPEN")
    close_event = {
        "event_id": "r_close_lease_order_probe",
        "event_type": "LEASE_CLOSE",
        "source_role": "executor",
        "clock": copy.deepcopy(open_event["clock"]),
        "time": {"lower_ns": 50, "upper_ns": 50, "censoring": "exact"},
        "input_authority": "false",
        "semantic_authority": "false",
        "lineage": {"lease_id": "L4", "actuation_id": "A4", "parent_event_ids": []},
        "payload": {},
    }
    insert_at = next(i for i, e in enumerate(target["events"])
                     if e["event_type"] == "INPUT_EDGE_BRACKET")
    target["events"].insert(insert_at, close_event)

    runs = {}
    for label, document in (("control", control), ("closed", treatment)):
        trace = out / f"{label}.trace-cases.json"
        trace.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        verification = out / f"{label}.verification.json"
        audit = out / f"{label}.audit.json"
        runs[label] = {
            "trace_sha256": sha256(trace.read_bytes()),
            "verify": invoke([sys.executable, str(source / "verify_contract.py"),
                              "--schema", str(source / "event-schema.json"),
                              "--traces", str(trace), "--out", str(verification)]),
        }
        runs[label]["verification_sha256"] = sha256(verification.read_bytes()) if verification.exists() else None
        runs[label]["audit"] = invoke([sys.executable, str(source / "audit_contract.py"),
                                       "--traces", str(trace), "--verification", str(verification),
                                       "--out", str(audit)])
        runs[label]["audit_sha256"] = sha256(audit.read_bytes()) if audit.exists() else None
        if verification.exists():
            runs[label]["verification_summary"] = json.loads(verification.read_text(encoding="utf-8"))
        if audit.exists():
            runs[label]["audit_summary"] = json.loads(audit.read_text(encoding="utf-8"))

    control_ok = runs["control"]["verify"]["exit_code"] == 0 and runs["control"]["audit"]["exit_code"] == 0
    closed_verify_ok = runs["closed"]["verify"]["exit_code"] == 0
    closed_audit_failed = runs["closed"]["audit"]["exit_code"] != 0
    if control_ok and closed_verify_ok and closed_audit_failed:
        disposition = "FAIL_W2_CLOSE_ORDER_CHECKER_DISAGREEMENT"
    elif control_ok and runs["closed"]["verify"]["exit_code"] != 0 and closed_audit_failed:
        disposition = "PASS_CLOSE_ORDER_GATE_SCOPED"
    else:
        disposition = "HOLD_CLOSE_ORDER_RESULT_INCOMPLETE_OR_DIFFERENT"

    result = {
        "schema": "w2-lease-close-order-host-probe-v1",
        "main_snapshot": "2ac5a00b9879c48f0ecf304c1d3ff01fe4c18ad8",
        "runtime": sys.version,
        "platform": sys.platform,
        "disposition": disposition,
        "source_blobs": pinned,
        "source_fixture_sha256": EXPECTED_FIXTURE_SHA256,
        "control_treatment_delta": "one same-lease/same-actuation LEASE_CLOSE event at 50 ns in the treatment only; open-binding A4 is identical in both versioned traces",
        "runs": runs,
        "limits": [
            "Synthetic host-CPU trace only; no Docker/formal execution.",
            "The original fixture and frozen verifier/auditor/schema are unchanged.",
            "No live input, runtime authority, GUI behavior, or product-safety claim.",
        ],
    }
    result_path = out / "PROBE_RESULT.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": disposition,
                      "control_verify": runs["control"]["verify"]["exit_code"],
                      "control_audit": runs["control"]["audit"]["exit_code"],
                      "closed_verify": runs["closed"]["verify"]["exit_code"],
                      "closed_audit": runs["closed"]["audit"]["exit_code"],
                      "result_sha256": sha256(result_path.read_bytes())}, indent=2))
    if not control_ok:
        raise SystemExit("STOP_CONTROL_DID_NOT_PASS")


if __name__ == "__main__":
    main()
