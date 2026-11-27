#!/usr/bin/env python3
"""Custody wrapper: candidate once, then raw-only auditor once on exit 0."""
import hashlib
import json
import pathlib
import subprocess
import sys

PKG = pathlib.Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    freeze = json.loads((PKG / "FREEZE.json").read_text())
    for rel, expected in freeze["code_sources"].items():
        if sha((PKG / rel).read_bytes()) != expected:
            raise SystemExit("frozen code digest mismatch: " + rel)
    if sha((PKG / "FREEZE.json").read_bytes()) != (PKG / "FREEZE.sha256").read_text().split()[0]:
        raise SystemExit("freeze sidecar mismatch")
    out = PKG / "results"
    out.mkdir(exist_ok=False)
    candidate = subprocess.run([sys.executable, str(PKG / "candidate.py")],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out / "candidate.stdout").write_bytes(candidate.stdout)
    (out / "candidate.stderr").write_bytes(candidate.stderr)
    (out / "candidate.exit").write_text(str(candidate.returncode) + "\n")
    if candidate.returncode != 0:
        (out / "audit.not_run").write_text("candidate exit was not zero; no retry\n")
        return candidate.returncode
    audit = subprocess.run([sys.executable, str(PKG / "auditor.py")], input=candidate.stdout,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out / "auditor.stdout").write_bytes(audit.stdout)
    (out / "auditor.stderr").write_bytes(audit.stderr)
    (out / "auditor.exit").write_text(str(audit.returncode) + "\n")
    run = {"candidate_invocations": 1, "candidate_exit": candidate.returncode,
           "candidate_stdout_sha256": hashlib.sha256(candidate.stdout).hexdigest(),
           "candidate_stderr_sha256": hashlib.sha256(candidate.stderr).hexdigest(),
           "auditor_invocations": 1, "auditor_exit": audit.returncode,
           "auditor_stdout_sha256": hashlib.sha256(audit.stdout).hexdigest(),
           "auditor_stderr_sha256": hashlib.sha256(audit.stderr).hexdigest(), "retries": 0}
    (out / "RUN.json").write_text(json.dumps(run, sort_keys=True, indent=2) + "\n")
    return audit.returncode


if __name__ == "__main__":
    raise SystemExit(main())
