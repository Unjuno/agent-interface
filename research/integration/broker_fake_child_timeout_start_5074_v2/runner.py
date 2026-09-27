"""Run the frozen seven-case fake-child broker matrix once in Docker."""
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from protocol import CASES, sha256, wait_until_started, write_json

SRC = Path("/src")
OUT = Path("/out")
BROKER = SRC / "host_model_ipc_broker_v1.py"


def fake_source() -> str:
    return (
        "#!" + sys.executable + "\n"
        "import json,os,pathlib,sys,time\n"
        "payload=sys.stdin.read()\n"
        "log=pathlib.Path(os.environ['FAKE_CALL_LOG'])\n"
        "with log.open('a',encoding='utf-8') as f:\n"
        " f.write(json.dumps({'event':'child_started','started_ns':time.perf_counter_ns(),"
        "'argv':sys.argv[1:],'stdin':payload})+'\\n')\n"
        " f.flush(); os.fsync(f.fileno())\n"
        "pathlib.Path(os.environ['FAKE_START_MARKER']).write_text('started\\n',encoding='utf-8')\n"
        "time.sleep(float(os.environ.get('FAKE_SLEEP','0')))\n"
        "print(os.environ.get('FAKE_RESPONSE','fake-response'))\n"
        "raise SystemExit(int(os.environ.get('FAKE_EXIT','0')))\n"
    )


def timeout_evidence_fields(marker_ns, start_record, marker_error,
                            broker_timeout_s: float) -> dict:
    """Return serialized timeout fields without relying on ambient variables."""
    return {
        "child_start_marker_ns": marker_ns,
        "child_start_record": start_record,
        "marker_error": marker_error,
        "broker_timeout_s": broker_timeout_s,
    }


def one_case(spec: dict) -> dict:
    name = spec["name"]
    case_root = OUT / "cases" / name
    ipc = case_root / "ipc"
    ipc.mkdir(parents=True)
    call_log = case_root / "child-calls.jsonl"
    marker = case_root / "child.started"
    fake = case_root / "fake_codex.py"
    fake.write_text(fake_source(), encoding="utf-8", newline="\n")
    fake.chmod(0o755)
    if spec.get("malformed"):
        (ipc / "00.request.json").write_text('{"request_id":', encoding="utf-8")
    elif not spec.get("idle"):
        ids = ("a", "z") if spec.get("queued") else (name,)
        for request_id in ids:
            write_json(ipc / f"{request_id}.request.json", {
                "request_id": request_id, "schema": "/repo/schema.json",
                "working": "/repo", "prompt": "prompt:" + request_id,
            })
    env = os.environ.copy()
    broker_timeout = float(spec.get("broker_timeout", 5))
    env.update({
        "CODEX_EXE": "/tmp/issue5074-missing" if spec.get("missing") else str(fake),
        "HOST_MODEL_BROKER_TIMEOUT_S": str(broker_timeout),
        "FAKE_CALL_LOG": str(call_log), "FAKE_START_MARKER": str(marker),
        "FAKE_EXIT": str(spec.get("child_exit", 0)),
        "FAKE_SLEEP": str(spec.get("child_sleep", 0)),
        "FAKE_RESPONSE": "response:" + name,
    })
    cmd = [sys.executable, str(BROKER), "--ipc", str(ipc),
           "--repo", "/out/cases/" + name, "--once"]
    started = time.monotonic_ns()
    proc = subprocess.Popen(cmd, cwd="/", env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    marker_ns = None
    start_record = None
    marker_error = None
    if name == "timeout-after-start":
        try:
            marker_ns, start_record = wait_until_started(marker, call_log, proc)
        except Exception as exc:
            marker_error = f"{type(exc).__name__}: {exc}"
            if proc.poll() is None:
                proc.kill()
    external_timeout = False
    try:
        stdout, stderr = proc.communicate(timeout=0.35 if spec.get("idle") else 7)
    except subprocess.TimeoutExpired:
        external_timeout = True
        proc.kill()
        stdout, stderr = proc.communicate()
    raw_files = {}
    for path in sorted(case_root.rglob("*")):
        if path.is_file():
            raw_files[str(path.relative_to(OUT))] = {
                "sha256": sha256(path), "bytes": path.stat().st_size,
            }
    receipts = {}
    for path in sorted(ipc.glob("*.broker.json")):
        receipts[path.name] = json.loads(path.read_text(encoding="utf-8"))
    responses = {}
    for path in sorted(ipc.glob("*.response.jsonl")):
        responses[path.name] = path.read_text(encoding="utf-8")
    calls = []
    if call_log.exists():
        calls = [json.loads(line) for line in call_log.read_text(encoding="utf-8").splitlines()]
    return {
        "name": name, "argv": cmd, "process_exit": proc.returncode,
        "external_timeout": external_timeout, "stdout": stdout, "stderr": stderr,
        "child_start_marker": marker.exists(),
        **timeout_evidence_fields(marker_ns, start_record, marker_error,
                                  broker_timeout),
        "child_calls": calls, "receipts": receipts, "responses": responses,
        "files": raw_files, "started_ns": started, "finished_ns": time.monotonic_ns(),
    }


def main() -> int:
    if not OUT.is_dir() or any(OUT.iterdir()):
        raise FileExistsError(f"formal output must be a fresh empty directory: {OUT}")
    receipt = Path("/invocation-receipt.json")
    if not receipt.is_file():
        raise FileNotFoundError("host-side invocation receipt was not mounted")
    shutil.copyfile(receipt, OUT / "invocation-receipt.json")
    if sha256(BROKER) != os.environ["EXPECTED_BROKER_SHA256"]:
        raise ValueError("mounted broker source SHA-256 mismatch")
    cases = []
    for spec in CASES:
        row = one_case(spec)
        cases.append(row)
        if row.get("marker_error"):
            break
    write_json(OUT / "raw.json", {
        "schema": "broker-timeout-start-raw-v1",
        "allocation": "broker-fake-child-timeout-start-20260928-01",
        "broker_sha256": sha256(BROKER), "cases": cases,
    })
    manifest = {}
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            manifest[str(path.relative_to(OUT))] = {
                "sha256": sha256(path), "bytes": path.stat().st_size,
            }
    write_json(OUT / "manifest.json", manifest)
    print("FORMAL_CASES_COMPLETE", len(cases))
    return 2 if len(cases) != len(CASES) else 0


if __name__ == "__main__":
    raise SystemExit(main())
