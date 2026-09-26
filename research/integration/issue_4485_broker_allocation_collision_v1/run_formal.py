"""Single-container frozen experiment driver for Issue #4485."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path("/evidence")
STUDY = Path("/study")
REPO = Path("/repo")
BROKER = REPO / "runtime/host_model_ipc_broker_v1.py"
FAKE = STUDY / "fake_codex.py"
EXPECTED = {
    "broker": "034b2e72a28fc3defb1b48195a2a8d3450e850895a4b3b7b7919dca44e198775",
    "tests": "a28b59232e55956a11bd87a35812b7d77df16febe5510c68fb80eda03a3ede1c",
}
EXPECTED_FAKE = "c9855dcc434b3bd52c9d1a5d35d0fadb72f338d2e7fefde11499f91ed849c64a"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_request(ipc, request_id):
    (ipc / f"{request_id}.request.json").write_text(json.dumps({
        "request_id": request_id, "schema": "/repo/schema.json",
        "working": "/repo", "prompt": request_id,
    }), encoding="utf-8")


def run_case(name, exit_code="0", mode="normal", unavailable=False, queued=()):
    case_dir = ROOT / "cases" / name
    case_dir.mkdir(parents=True)
    ipc = case_dir / "ipc"
    ipc.mkdir()
    ids = tuple(queued) if queued else (name,)
    for request_id in ids:
        write_request(ipc, request_id)
    invocation_log = case_dir / "invocations.jsonl"
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp",
           "CODEX_EXE": "/study/missing-executable" if unavailable else str(FAKE),
           "HOST_MODEL_BROKER_TIMEOUT_S": "0.2", "FAKE_EXIT": str(exit_code),
           "FAKE_MODE": mode, "FAKE_INVOCATIONS": str(invocation_log)}
    started = time.monotonic_ns()
    timed_out = False
    try:
        proc = subprocess.run([sys.executable, str(BROKER), "--ipc", str(ipc),
                               "--repo", str(REPO), "--once"], env=env,
                              capture_output=True, text=True, timeout=0.3)
        returncode, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode, stdout, stderr = None, exc.stdout or "", exc.stderr or ""
    receipts = {}
    responses = {}
    for path in sorted(ipc.glob("*.broker.json")):
        receipts[path.name] = json.loads(path.read_text(encoding="utf-8"))
    for path in sorted(ipc.glob("*.response.jsonl")):
        responses[path.name] = path.read_text(encoding="utf-8")
    invocations = invocation_log.read_text(encoding="utf-8").splitlines() if invocation_log.exists() else []
    row = {"case": name, "request_ids": list(ids), "process_returncode": returncode,
           "external_timeout": timed_out, "elapsed_ns": time.monotonic_ns() - started,
           "stdout": stdout, "stderr": stderr, "receipts": receipts,
           "responses": responses, "invocations": invocations}
    (case_dir / "row.json").write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")
    return row


def main():
    if not ROOT.is_dir() or any(ROOT.iterdir()):
        raise SystemExit("STOP_EVIDENCE_PATH_NOT_EMPTY")
    source_hashes = {"broker": digest(BROKER), "tests": digest(REPO / "runtime/test_host_model_ipc_broker_v1.py")}
    fake_hash = digest(FAKE)
    if source_hashes != EXPECTED:
        raise SystemExit(f"STOP_SOURCE_HASH_MISMATCH {source_hashes}")
    if not os.access(FAKE, os.X_OK) or fake_hash != EXPECTED_FAKE:
        raise SystemExit(f"STOP_FAKE_EXECUTABLE_GATE {fake_hash}")
    preflight = {"result": "PASS_PREFLIGHT", "source_sha256": source_hashes,
                 "fake_sha256": fake_hash, "fake_executable": str(FAKE)}
    (ROOT / "preflight.json").write_text(json.dumps(preflight, sort_keys=True) + "\n", encoding="utf-8")

    rows = []
    rows.append(run_case("exit_zero", "0"))
    rows.append(run_case("exit_23", "23"))
    rows.append(run_case("timeout", mode="sleep"))
    rows.append(run_case("unavailable", unavailable=True))
    malformed_dir = ROOT / "cases/malformed_request"
    malformed_dir.mkdir(parents=True)
    malformed_ipc = malformed_dir / "ipc"
    malformed_ipc.mkdir()
    (malformed_ipc / "malformed.request.json").write_text("{", encoding="utf-8")
    started = time.monotonic_ns()
    p = subprocess.run([sys.executable, str(BROKER), "--ipc", str(malformed_ipc),
                        "--repo", str(REPO), "--once"],
                       env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp"},
                       capture_output=True, text=True, timeout=0.3)
    rows.append({"case": "malformed_request", "request_ids": ["malformed"],
                 "process_returncode": p.returncode, "external_timeout": False,
                 "elapsed_ns": time.monotonic_ns() - started, "stdout": p.stdout,
                 "stderr": p.stderr, "receipts": {}, "responses": {}, "invocations": []})
    (malformed_dir / "row.json").write_text(json.dumps(rows[-1], sort_keys=True) + "\n", encoding="utf-8")

    idle_dir = ROOT / "cases/idle_once"
    idle_dir.mkdir(parents=True)
    idle_ipc = idle_dir / "ipc"
    idle_ipc.mkdir()
    started = time.monotonic_ns()
    try:
        p = subprocess.run([sys.executable, str(BROKER), "--ipc", str(idle_ipc),
                            "--repo", str(REPO), "--once"],
                           env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp"},
                           capture_output=True, text=True, timeout=0.3)
        idle = {"process_returncode": p.returncode, "external_timeout": False,
                "stdout": p.stdout, "stderr": p.stderr}
    except subprocess.TimeoutExpired as exc:
        idle = {"process_returncode": None, "external_timeout": True,
                "stdout": exc.stdout or "", "stderr": exc.stderr or ""}
    rows.append({"case": "idle_once", "request_ids": [], "elapsed_ns": time.monotonic_ns() - started,
                 "receipts": {}, "responses": {}, "invocations": [], **idle})
    (idle_dir / "row.json").write_text(json.dumps(rows[-1], sort_keys=True) + "\n", encoding="utf-8")
    rows.append(run_case("two_queued", queued=("a-first", "b-second")))
    with (ROOT / "raw.jsonl").open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
    (ROOT / "source_hashes.json").write_text(json.dumps(source_hashes, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "preflight": preflight, "raw_sha256": digest(ROOT / "raw.jsonl")}))


if __name__ == "__main__":
    main()
