"""Run the preregistered CPU-only synthetic matrix exactly once."""

import hashlib
import json
import os
import platform
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from gate import run_gated


ROOT = Path(__file__).resolve().parent
BASE = "5ff239141f49c1603c0f6b078268f4a2f6e082df"
SOURCES = ["PREREG.md", "gate.py", "test_gate.py", "run_construction.py", "audit.py", "test_audit.py"]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    source_hashes = {name: digest((ROOT / name).read_bytes()) for name in SOURCES}
    freeze = {"base_main": BASE, "runtime": platform.python_version(), "sources": source_hashes,
              "scope": "host-only synthetic; no GPU, Docker, model, game, GUI or input"}
    (ROOT / "FREEZE.json").write_text(json.dumps(freeze, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    manifest = {"commit": BASE, "files": source_hashes}
    manifest_sha = digest(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode())
    good_inventory = {"returncode": 0, "stdout": b'{"compute_processes":[]}', "stderr": b""}
    good_json = b'{"schema":"synthetic-v1","result":"ok"}'
    cases = []

    def run_case(name, inventory=good_inventory, source=manifest, source_sha=manifest_sha,
                 candidate_value=None, corrupt_after_replace=False):
        calls = []
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "raw.json"

            def candidate():
                calls.append(1)
                return candidate_value if candidate_value is not None else {"returncode": 0, "stdout": good_json}

            if corrupt_after_replace:
                original_replace = os.replace

                def replace_then_corrupt(src, dst):
                    original_replace(src, dst)
                    Path(dst).write_bytes(b"tampered-after-replace")

                with patch("gate.os.replace", side_effect=replace_then_corrupt):
                    outcome = run_gated(inventory, source, source_sha, candidate, target)
            else:
                outcome = run_gated(inventory, source, source_sha, candidate, target)
            artifact_sha = digest(target.read_bytes()) if target.exists() else None
        cases.append({"case": name, "outcome": outcome, "candidate_calls": len(calls),
                      "published_artifact_sha256": artifact_sha})

    run_case("empty_inventory", inventory={"returncode": 0, "stdout": b"", "stderr": b""})
    run_case("inventory_command_failure", inventory={"returncode": 2, "stdout": b"{}", "stderr": b"probe failed"})
    run_case("malformed_inventory", inventory={"returncode": 0, "stdout": b"{", "stderr": b""})
    run_case("inventory_schema_invalid", inventory={"returncode": 0, "stdout": b'{"processes":[]}', "stderr": b""})
    run_case("incomplete_source_identity", source={"commit": "", "files": {}})
    run_case("changed_source_digest", source_sha="0" * 64)
    run_case("candidate_nonzero", candidate_value={"returncode": 9, "stdout": good_json, "stderr": b"candidate failed"})
    run_case("candidate_output_absent", candidate_value={"returncode": 0, "stdout": b"", "stderr": b""})
    run_case("candidate_json_truncated", candidate_value={"returncode": 0, "stdout": b'{"result":', "stderr": b""})
    run_case("postwrite_digest_mismatch", corrupt_after_replace=True)
    run_case("valid_success")

    run = {"schema": "issue5730-construction-run-v1", "base_main": BASE,
           "python": sys.version, "source_sha256": source_hashes, "cases": cases,
           "candidate_invocations": sum(case["candidate_calls"] for case in cases),
           "scope": "synthetic host-only; no GPU, CUDA, Docker, model, game, GUI or input"}
    raw = (json.dumps(run, sort_keys=True, indent=2) + "\n").encode("utf-8")
    (ROOT / "RUN.json").write_bytes(raw)
    (ROOT / "STDOUT.bin").write_bytes(raw)
    (ROOT / "STDERR.bin").write_bytes(b"")
    execution = {"command": "python -B run_construction.py", "exit_code": 0,
                 "stdout_sha256": digest(raw), "stderr_sha256": digest(b""),
                 "run_sha256": digest(raw), "candidate_invocations": run["candidate_invocations"]}
    (ROOT / "EXECUTION.json").write_text(json.dumps(execution, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
