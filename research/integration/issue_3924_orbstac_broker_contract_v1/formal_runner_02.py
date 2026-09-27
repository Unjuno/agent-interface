"""Allocation 02: frozen fake-only broker matrix after run-01 preflight STOP."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

STUDY = Path(__file__).parent
ROOT = Path("/evidence/formal")
ROOT.mkdir(parents=True, exist_ok=False)
BROKER = Path("/repo/runtime/host_model_ipc_broker_v1.py")
TEST = Path("/repo/runtime/test_host_model_ipc_broker_v1.py")
freeze = json.loads((STUDY / "FREEZE_02.json").read_text())
if hashlib.sha256(BROKER.read_bytes()).hexdigest() != freeze["source"]["broker_sha256"]:
    raise SystemExit("STOP_SOURCE_HASH_MISMATCH")
if hashlib.sha256(TEST.read_bytes()).hexdigest() != freeze["source"]["existing_test_sha256"]:
    raise SystemExit("STOP_EXISTING_TEST_HASH_MISMATCH")

cases = ["exit0", "exit23", "timeout", "unavailable", "malformed", "one-shot-idle", "two-queued"]
for name in cases:
    out = ROOT / name
    out.mkdir()
    ipc = out / "ipc"
    ipc.mkdir()
    fake_records = out / "fake-records"
    fake_records.mkdir()
    if name != "one-shot-idle":
        if name == "two-queued":
            requests = [
                {"request_id": "queued-a", "schema": "/repo/schema.json", "working": "/repo", "prompt": "fake"},
                {"request_id": "queued-b", "schema": "/repo/schema.json", "working": "/repo", "prompt": "fake"},
            ]
        else:
            requests = [json.loads((STUDY / "fixtures" / name / "request.json").read_text())]
        for req in requests:
            (ipc / f"{req['request_id']}.request.json").write_text(json.dumps(req) + "\n")
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "PYTHONIOENCODING": "utf-8"}
    if name == "exit0": env.update({"FAKE_EXIT": "0", "CODEX_EXE": "/study/fake_codex.py"})
    if name == "exit23": env.update({"FAKE_EXIT": "23", "CODEX_EXE": "/study/fake_codex.py"})
    if name == "two-queued": env.update({"FAKE_EXIT": "0", "CODEX_EXE": "/study/fake_codex.py"})
    if name == "timeout": env.update({"FAKE_EXIT": "0", "FAKE_SLEEP_S": "0.3", "HOST_MODEL_BROKER_TIMEOUT_S": "0.05", "CODEX_EXE": "/study/fake_codex.py"})
    if name == "unavailable": env["CODEX_EXE"] = "/missing/fake-codex"
    env["FAKE_RECORD_ROOT"] = str(fake_records)
    start = time.monotonic_ns()
    proc = subprocess.Popen(
        [sys.executable, str(BROKER), "--ipc", str(ipc), "--repo", "/repo", "--once"],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=0.3 if name == "one-shot-idle" else 2.0)
        killed = False
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        killed = True
    end = time.monotonic_ns()
    (out / "process.json").write_text(json.dumps({"returncode": proc.returncode, "killed_by_harness": killed,
        "elapsed_ns": end-start, "stdout": stdout, "stderr": stderr, "case": name}, sort_keys=True)+"\n")
    if name == "one-shot-idle":
        continue
    for path in sorted(ipc.iterdir()): shutil.copy2(path, out / path.name)
    for path in sorted(fake_records.iterdir()): shutil.copy2(path, out / path.name)
    print(f"FORMAL_CASE_RETAINED case={name} broker_rc={proc.returncode} timeout_kill={killed}")
print("FORMAL_MATRIX_COMPLETE allocation=02 cases=7 fake_only=1")
