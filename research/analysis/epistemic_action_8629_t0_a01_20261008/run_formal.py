def verify_sources(root, expected):
    import hashlib

    errors = []
    for relative, digest in sorted(expected.items()):
        path = root / relative
        if not path.is_file():
            errors.append("missing frozen source: " + relative)
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            errors.append("frozen source hash mismatch: " + relative)
    return errors


def reserve_output(path):
    path.mkdir(parents=True, exist_ok=False)
    return path


def run_once(root, output_dir):
    import hashlib
    import json
    import platform
    import subprocess
    import sys
    import time
    from datetime import datetime, timezone

    root = root.resolve()
    freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
    errors = verify_sources(root, freeze["files"])
    if errors:
        raise RuntimeError("freeze verification failed: " + "; ".join(errors))
    output_dir = reserve_output(output_dir.resolve())

    started = datetime.now(timezone.utc).isoformat()
    candidate_command = [sys.executable, "candidate.py", "fixture.json"]
    t0 = time.perf_counter_ns()
    candidate = subprocess.run(candidate_command, cwd=root, capture_output=True, check=False)
    candidate_elapsed = time.perf_counter_ns() - t0
    (output_dir / "raw_candidate.json").write_bytes(candidate.stdout)
    (output_dir / "candidate.stderr").write_bytes(candidate.stderr)

    auditor_command = [sys.executable, "auditor.py", "--fixture", "fixture.json", "--oracle", "oracle.json"]
    t1 = time.perf_counter_ns()
    auditor = subprocess.run(auditor_command, cwd=root, input=candidate.stdout, capture_output=True, check=False)
    auditor_elapsed = time.perf_counter_ns() - t1
    (output_dir / "raw_audit.json").write_bytes(auditor.stdout)
    (output_dir / "auditor.stderr").write_bytes(auditor.stderr)

    try:
        audit = json.loads(auditor.stdout)
        audit_valid = True
    except (UnicodeDecodeError, json.JSONDecodeError):
        audit = None
        audit_valid = False

    def digest(data):
        return hashlib.sha256(data).hexdigest()

    receipt = {
        "allocation": "EPISTEMIC-ACTION-8629-T0-A01-20261008",
        "schema": "epistemic-action-run-v1",
        "started_utc": started,
        "platform": platform.platform(),
        "python": sys.version,
        "source_hashes_verified": True,
        "candidate_command": ["<sys.executable>", "candidate.py", "fixture.json"],
        "candidate_invocations": 1,
        "candidate_exit_code": candidate.returncode,
        "candidate_elapsed_ns": candidate_elapsed,
        "candidate_stdout_bytes": len(candidate.stdout),
        "candidate_stdout_sha256": digest(candidate.stdout),
        "candidate_stderr_bytes": len(candidate.stderr),
        "candidate_stderr_sha256": digest(candidate.stderr),
        "auditor_command": ["<sys.executable>", "auditor.py", "--fixture", "fixture.json", "--oracle", "oracle.json", "<raw_candidate.json on stdin>"],
        "auditor_invocations": 1,
        "auditor_exit_code": auditor.returncode,
        "auditor_elapsed_ns": auditor_elapsed,
        "auditor_stdout_bytes": len(auditor.stdout),
        "auditor_stdout_sha256": digest(auditor.stdout),
        "auditor_stderr_bytes": len(auditor.stderr),
        "auditor_stderr_sha256": digest(auditor.stderr),
        "auditor_output_valid": audit_valid,
        "retries": 0,
        "formal_disposition": audit.get("method_disposition", "HOLD") if audit else "HOLD",
        "hypothesis_disposition": audit.get("hypothesis_disposition", "HOLD") if audit else "HOLD",
    }
    (output_dir / "RUN.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return receipt


def main():
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    receipt = run_once(root, root / args.output_dir)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["formal_disposition"] == "PASS_METHOD_SCOPED" and receipt["hypothesis_disposition"] == "H_PASS_SCOPED" and receipt["candidate_exit_code"] == 0 and receipt["auditor_exit_code"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
