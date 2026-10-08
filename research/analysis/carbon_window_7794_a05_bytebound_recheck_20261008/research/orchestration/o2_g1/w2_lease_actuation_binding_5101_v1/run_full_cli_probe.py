"""Run frozen W2 CLIs on baseline and a single lease-actuation mutant.

This is host-CPU reproduction only; it is not the pinned-container formal run.
All generated evidence is written to a caller-supplied fresh output directory.
"""
import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def invoke(argv):
    completed = subprocess.run(argv, text=True, capture_output=True, check=False)
    return {
        "argv": [str(x) for x in argv],
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--frozen-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    source = args.frozen_dir.resolve(strict=True)
    out = args.output_dir.resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_FRESH")
    out.mkdir(parents=True, exist_ok=True)

    fixture = json.loads((source / "trace-cases.json").read_text(encoding="utf-8"))
    mutant = copy.deepcopy(fixture)
    case = next(c for c in mutant["cases"] if c["case_id"] == "release-before-terminal")
    lease_open = next(e for e in case["events"] if e["event_type"] == "LEASE_OPEN")
    lease_open["lineage"]["actuation_id"] = "FOREIGN-ACTUATION"
    mutant_path = out / "foreign-actuation.trace-cases.json"
    mutant_path.write_text(json.dumps(mutant, indent=2) + "\n", encoding="utf-8")

    verifier = source / "verify_contract.py"
    auditor = source / "audit_contract.py"
    schema = source / "event-schema.json"
    baseline_trace = source / "trace-cases.json"
    runs = {}
    for label, traces in (("baseline", baseline_trace), ("foreign_actuation", mutant_path)):
        verification = out / f"{label}.verification.json"
        audit = out / f"{label}.audit.json"
        runs[f"{label}_verify"] = invoke([
            sys.executable, str(verifier), "--schema", str(schema),
            "--traces", str(traces), "--out", str(verification),
        ])
        runs[f"{label}_audit"] = invoke([
            sys.executable, str(auditor), "--traces", str(traces),
            "--verification", str(verification), "--out", str(audit),
        ])
        runs[f"{label}_verification_sha256"] = sha256(verification) if verification.exists() else None
        runs[f"{label}_audit_sha256"] = sha256(audit) if audit.exists() else None

    summary = {
        "schema": "w2-lease-actuation-host-cli-probe-v1",
        "disposition": "HOST_CLI_PROBE_COMPLETE_NOT_FORMAL",
        "frozen_source_sha256": {
            name: sha256(source / name)
            for name in ("verify_contract.py", "audit_contract.py", "event-schema.json", "trace-cases.json")
        },
        "mutant": {
            "case_id": "release-before-terminal",
            "mutation": "LEASE_OPEN.lineage.actuation_id absent -> FOREIGN-ACTUATION",
            "mutated_trace_sha256": sha256(mutant_path),
        },
        "runs": runs,
        "limits": [
            "Host Python CLI only; not Docker/formal evidence.",
            "Synthetic fixture only; no live input, GUI, model, or task effect.",
            "Verifier/auditor sources were read-only; all generated files are under the fresh output directory.",
        ],
    }
    result_path = out / "HOST_CLI_RESULT.json"
    result_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "result_path": str(result_path),
        "runs": {k: v for k, v in runs.items() if isinstance(v, dict)},
        "result_sha256": sha256(result_path),
    }, indent=2))
    if any(isinstance(v, dict) and v["exit_code"] != 0 for v in runs.values()):
        raise SystemExit("HOST_CLI_RUN_FAILURE")


if __name__ == "__main__":
    main()
