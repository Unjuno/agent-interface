import hashlib
import json
import os
import platform
from pathlib import Path
import sqlite3
import subprocess
import sys
import time


BROKER = Path("/repo/runtime/host_model_ipc_broker_v1.py")
OUT = Path("/out")
REPO = Path("/repo")
CASE_IDS = ("exit_0", "exit_23", "timeout", "unavailable", "malformed", "idle", "queued")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def request(request_id, **extra):
    value = {
        "request_id": request_id,
        "schema": "/repo/schema.json",
        "working": "/repo",
        "prompt": "fixed fake-child boundary probe",
    }
    value.update(extra)
    return value


def write_requests(ipc, requests):
    for value in requests:
        path = ipc / (value["request_id"] + ".request.json")
        path.write_bytes(json_bytes(value))


def run_case(case_id, requests, *, child_exit="0", child_sleep="0", timeout="2", unavailable=False, idle=False):
    case_dir = OUT / "cases" / case_id
    ipc = case_dir / "ipc"
    ipc.mkdir(parents=True)
    write_requests(ipc, requests)
    fake = Path("/fakeexec/fake_codex.py")
    fake.write_text(
        "#!/usr/local/bin/python\n"
        "import os, sys, time\n"
        "with open(os.environ['FAKE_CALL_LOG'], 'a', encoding='utf-8') as f: f.write('invoked\\n')\n"
        "time.sleep(float(os.environ.get('FAKE_SLEEP', '0')))\n"
        "sys.stdout.write('fake-response\\n')\n"
        "sys.stderr.write('fake-stderr\\n')\n"
        "raise SystemExit(int(os.environ.get('FAKE_EXIT', '0')))\n",
        encoding="utf-8",
    )
    fake.chmod(0o700)
    call_log = case_dir / "fake_calls.txt"
    env = os.environ.copy()
    env.update({
        "CODEX_EXE": "/definitely-missing-codex" if unavailable else str(fake),
        "HOST_MODEL_BROKER_TIMEOUT_S": timeout,
        "FAKE_EXIT": str(child_exit),
        "FAKE_SLEEP": str(child_sleep),
        "FAKE_CALL_LOG": str(call_log),
    })
    argv = [sys.executable, "-B", str(BROKER), "--ipc", str(ipc), "--repo", str(REPO), "--once"]
    started = time.monotonic_ns()
    timed_out = False
    try:
        proc = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=0.45 if idle else 4)
        status = proc.returncode
        stdout, stderr = proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        status = None
        stdout = (exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    elapsed = time.monotonic_ns() - started
    ipc_files = sorted(p.name for p in ipc.iterdir())
    receipt_paths = sorted(ipc.glob("*.broker.json"))
    response_paths = sorted(ipc.glob("*.response.jsonl"))
    calls = call_log.read_text(encoding="utf-8").splitlines() if call_log.exists() else []
    receipts = {p.name.removesuffix(".broker.json"): json.loads(p.read_text()) for p in receipt_paths}
    responses = {p.name.removesuffix(".response.jsonl"): p.read_text(encoding="utf-8") for p in response_paths}
    request_hashes = {p.name: digest(p.read_bytes()) for p in sorted(ipc.glob("*.request.json"))}
    record = {
        "case_id": case_id,
        "request_sha256": request_hashes,
        "ipc_files": ipc_files,
        "broker_status": status,
        "externally_timed_out": timed_out,
        "elapsed_ns": elapsed,
        "stdout": stdout,
        "stderr": stderr,
        "receipts": receipts,
        "responses": responses,
        "fake_invocation_count": len(calls),
        "fake_invocation_log": calls,
        "argv": argv,
        "exit_setting": child_exit,
        "sleep_setting": child_sleep,
        "timeout_setting": timeout,
    }
    (case_dir / "RESULT.json").write_bytes(json_bytes(record))
    return record


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    rows = []
    rows.append(run_case("exit_0", [request("exit-0")], child_exit="0"))
    rows.append(run_case("exit_23", [request("exit-23")], child_exit="23"))
    rows.append(run_case("timeout", [request("timeout")], child_sleep="2", timeout="0.1"))
    rows.append(run_case("unavailable", [request("unavailable")], unavailable=True))
    rows.append(run_case("malformed", [request("malformed", instructions="/repo/forbidden.txt")]))
    rows.append(run_case("idle", [], idle=True))
    rows.append(run_case("queued", [request("z-last"), request("a-first")]))
    summary = {"schema": "broker-fake-child-result-v1", "case_ids": list(CASE_IDS), "rows": rows}
    (OUT / "RESULT.json").write_bytes(json_bytes(summary))
    (OUT / "ENVIRONMENT.json").write_bytes(json_bytes({
        "python": sys.version,
        "machine": platform.machine(),
        "platform": platform.platform(),
        "sqlite": sqlite3.sqlite_version,
        "broker_sha256": digest(BROKER.read_bytes()),
    }))
    manifest = {}
    for path in sorted(p for p in OUT.rglob("*") if p.is_file()):
        rel = str(path.relative_to(OUT))
        data = path.read_bytes()
        manifest[rel] = {"sha256": digest(data), "bytes": len(data)}
    (OUT / "FILE_MANIFEST.json").write_bytes(json_bytes({"files": manifest}))
    print(json.dumps({"cases": len(rows), "ids": [r["case_id"] for r in rows], "files": len(manifest)}))


if __name__ == "__main__":
    main()
