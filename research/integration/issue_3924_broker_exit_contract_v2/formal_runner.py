"""One frozen seven-case fake-only broker allocation."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

STUDY = Path("/study")
FREEZE = json.loads((STUDY / "FREEZE.json").read_text())
BROKER = Path("/repo/runtime/host_model_ipc_broker_v1.py")
TEST = Path("/repo/runtime/test_host_model_ipc_broker_v1.py")
FAKE = STUDY / "fake_codex.py"
assert hashlib.sha256(BROKER.read_bytes()).hexdigest() == FREEZE["source"]["broker_sha256"]
assert hashlib.sha256(TEST.read_bytes()).hexdigest() == FREEZE["source"]["existing_test_sha256"]
assert FAKE.is_file() and os.access(FAKE, os.X_OK)
assert hashlib.sha256(FAKE.read_bytes()).hexdigest() == FREEZE["fake_sha256"]
assert shutil.which("codex") is None
assert sys.version_info[:2] == (3, 12)

ROOT = Path("/evidence/formal")
ROOT.mkdir(parents=True, exist_ok=False)
(ROOT / "container.json").write_text(json.dumps({
    "allocation": FREEZE["allocation"], "image_id": FREEZE["environment"]["image_id"],
    "python": sys.version, "platform": sys.platform, "uname": list(os.uname()),
    "study_mount": str(STUDY.resolve()), "fake_sha256": hashlib.sha256(FAKE.read_bytes()).hexdigest(),
    "broker_sha256": hashlib.sha256(BROKER.read_bytes()).hexdigest(),
    "test_sha256": hashlib.sha256(TEST.read_bytes()).hexdigest(), "real_codex_found": False,
}, sort_keys=True, indent=2) + "\n")

cases = FREEZE["formal_matrix"]
for name in cases:
    out = ROOT / name
    out.mkdir()
    ipc = out / "ipc"
    ipc.mkdir()
    fake_records = out / "fake-records"
    fake_records.mkdir()
    requests = []
    if name == "two-queued":
        requests = [
            {"request_id": "queued-a", "schema": "/repo/schema.json", "working": "/repo", "prompt": "fake"},
            {"request_id": "queued-b", "schema": "/repo/schema.json", "working": "/repo", "prompt": "fake"},
        ]
    elif name != "one-shot-idle":
        requests = [json.loads((STUDY / "fixtures" / f"{name}.json").read_text())]
    for request in requests:
        (ipc / f"{request['request_id']}.request.json").write_text(json.dumps(request) + "\n", encoding="utf-8")

    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "PYTHONIOENCODING": "utf-8", "FAKE_RECORD_ROOT": str(fake_records)}
    if name in ("exit0", "two-queued"):
        env.update({"CODEX_EXE": str(FAKE), "FAKE_EXIT": "0"})
    elif name == "exit23":
        env.update({"CODEX_EXE": str(FAKE), "FAKE_EXIT": "23"})
    elif name == "timeout":
        env.update({"CODEX_EXE": str(FAKE), "FAKE_EXIT": "0", "FAKE_SLEEP_S": "2.0", "HOST_MODEL_BROKER_TIMEOUT_S": "1.0"})
    elif name == "unavailable":
        env["CODEX_EXE"] = "/missing/fake-codex"

    start_ns = time.monotonic_ns()
    process = subprocess.Popen(
        [sys.executable, str(BROKER), "--ipc", str(ipc), "--repo", "/repo", "--once"],
        env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=0.3 if name == "one-shot-idle" else 5.0)
        killed = False
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        killed = True
    elapsed_ns = time.monotonic_ns() - start_ns
    (out / "process.json").write_text(json.dumps({
        "case": name, "returncode": process.returncode, "killed_by_harness": killed,
        "elapsed_ns": elapsed_ns, "stdout": stdout, "stderr": stderr,
    }, sort_keys=True, indent=2) + "\n")
    for path in sorted(ipc.iterdir()):
        shutil.copy2(path, out / path.name)
    for path in sorted(fake_records.iterdir()):
        shutil.copy2(path, out / path.name)
    print(f"FORMAL_CASE_RETAINED case={name} broker_rc={process.returncode} timeout_kill={killed} fake_invocations={len(list(fake_records.glob('invocation-*.json')))}")
print(f"FORMAL_MATRIX_COMPLETE allocation={FREEZE['allocation']} cases={len(cases)} fake_only=1")
