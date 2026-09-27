#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path


EXPECTED_BROKER_BLOB = "5734f54f318db9ac5e96b2bed6f6bed105ac39ff"
ALLOCATION = "broker-fake-child-boundary-4485-arm64-construction-20260928-01"


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(input_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise SystemExit("STOP_FRESH_OUTPUT_NOT_EMPTY")
    broker_path = input_dir / "host_model_ipc_broker_v1.py"
    broker_bytes = broker_path.read_bytes()
    broker_blob = git_blob(broker_bytes)
    if broker_blob != EXPECTED_BROKER_BLOB:
        raise SystemExit(f"STOP_BROKER_BLOB_MISMATCH:{broker_blob}")
    broker_sha_before = hashlib.sha256(broker_bytes).hexdigest()
    root = output_dir / "case-exit-23"
    ipc = root / "ipc"
    repo = root / "repo"
    ipc.mkdir(parents=True)
    repo.mkdir(parents=True)
    fake = output_dir / "fake_codex.py"
    fake_log = output_dir / "fake_child_call.json"
    fake_source = """#!/usr/bin/env python3
import json, os, sys
record = {"argv": sys.argv[1:], "stdin": sys.stdin.read(), "intended_exit": 23}
with open(os.environ["FAKE_CHILD_LOG"], "w", encoding="utf-8") as f:
    json.dump(record, f, sort_keys=True)
    f.write("\\n")
sys.stdout.write("partial fake-child response\\n")
sys.stderr.write("fake child diagnostic\\n")
raise SystemExit(23)
"""
    fake.write_text(fake_source, encoding="utf-8")
    fake.chmod(0o755)
    request = {
        "request_id": "case-exit-23",
        "schema": "/repo/schema.json",
        "working": "/repo",
        "prompt": "frozen construction probe",
    }
    request_path = ipc / "case-exit-23.request.json"
    request_path.write_text(json.dumps(request, sort_keys=True) + "\n", encoding="utf-8")
    env = os.environ.copy()
    env["CODEX_EXE"] = str(fake)
    env["FAKE_CHILD_LOG"] = str(fake_log)
    started = time.monotonic_ns()
    command = [sys.executable, str(broker_path), "--ipc", str(ipc), "--repo", str(repo), "--once"]
    broker_proc = subprocess.run(command, capture_output=True, text=True, env=env, timeout=15, check=False)
    elapsed_ns = time.monotonic_ns() - started
    broker_path.read_bytes() == broker_bytes or (_ for _ in ()).throw(RuntimeError("broker input changed"))
    receipt_path = ipc / "case-exit-23.broker.json"
    response_path = ipc / "case-exit-23.response.jsonl"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else None
    response = response_path.read_text(encoding="utf-8") if response_path.exists() else None
    child_call = json.loads(fake_log.read_text(encoding="utf-8")) if fake_log.exists() else None
    raw = {
        "schema": "broker-fake-child-boundary-construction-raw-v1",
        "issue": 5013,
        "allocation": ALLOCATION,
        "source_git_blob": broker_blob,
        "source_sha256_before": broker_sha_before,
        "source_sha256_after": sha256(broker_path),
        "container": {"python": sys.version.split()[0], "platform": platform.platform(), "machine": platform.machine()},
        "case": "ACTUAL_FAKE_CHILD_EXIT_23",
        "broker_command": command,
        "broker_process_exit": broker_proc.returncode,
        "broker_stdout": broker_proc.stdout,
        "broker_stderr": broker_proc.stderr,
        "broker_elapsed_ns": elapsed_ns,
        "request": request,
        "request_file_sha256": sha256(request_path),
        "broker_receipt": receipt,
        "response": response,
        "fake_child_call": child_call,
        "fake_child_log_sha256": sha256(fake_log) if fake_log.exists() else None,
        "authority_requested": False,
        "scope": "one real local fake-child subprocess construction case; not the seven-case formal Issue #5013 allocation",
    }
    (output_dir / "RAW_RESULT.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(raw, sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
