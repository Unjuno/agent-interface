"""Independent standard-library-only audit of the construction STOP evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
EV = ROOT / "evidence" / "construction_01"
OUT = ROOT / "outputs" / "construction-736514"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

errors = []
freeze_bytes = (SRC / "FREEZE.json").read_bytes()
freeze = json.loads(freeze_bytes)
sidecar = (SRC / "FREEZE.sha256").read_bytes()
if sidecar != (sha(SRC / "FREEZE.json") + "\n").encode("ascii"):
    errors.append("freeze_sidecar")
for name, digest in freeze["source_sha256"].items():
    if sha(SRC / name) != digest:
        errors.append("source:" + name)
stop = json.loads((EV / "STOP.json").read_bytes())
receipt = json.loads((EV / "CONSTRUCTION_INVOCATION.json").read_bytes())
stdout = (EV / "docker.stdout.bin").read_bytes()
stderr = (EV / "docker.stderr.bin").read_bytes()
if stop.get("status") != "STOP_CONSTRUCTION_OUTPUT_NOT_EMPTY": errors.append("stop_status")
if stop.get("construction_fit_reached") is not False or stop.get("formal_fit_count") != 0: errors.append("fit_boundary")
if stop.get("construction_invocation_count") != 1 or stop.get("retry_count") != 0: errors.append("invocation_count")
if receipt.get("exit_code") != 1 or receipt.get("raw_exists") is not False or receipt.get("raw_bytes") != 0: errors.append("receipt_exit_or_raw")
if receipt.get("formal_orchestrations") != 0 or receipt.get("construction_orchestrations") != 1 or receipt.get("retries") != 0: errors.append("receipt_counts")
if receipt.get("construction_seed") != 736514 or receipt.get("formal_seeds") != [736711, 736811, 736911]: errors.append("seed_binding")
if receipt.get("freeze_sha256") != sha(SRC / "FREEZE.json"): errors.append("freeze_binding")
if receipt.get("stdout_bytes") != len(stdout) or receipt.get("stdout_sha256") != hashlib.sha256(stdout).hexdigest(): errors.append("stdout_binding")
if receipt.get("stderr_bytes") != len(stderr) or receipt.get("stderr_sha256") != hashlib.sha256(stderr).hexdigest(): errors.append("stderr_binding")
if stdout or b"STOP_CONSTRUCTION_OUTPUT_NOT_EMPTY" not in stderr: errors.append("stop_log")
if (OUT / "construction_raw.json").exists(): errors.append("unexpected_raw")
if sha(EV / "docker.stdout.bin") != receipt.get("stdout_sha256"): errors.append("retained_stdout")
if sha(EV / "docker.stderr.bin") != receipt.get("stderr_sha256"): errors.append("retained_stderr")
result = {"audit": "PASS_STOP_EVIDENCE_AUDIT" if not errors else "FAIL_STOP_EVIDENCE_AUDIT", "errors": errors,
          "freeze_sha256": sha(SRC / "FREEZE.json"), "invocation_receipt_sha256": sha(EV / "CONSTRUCTION_INVOCATION.json"),
          "stdout_sha256": sha(EV / "docker.stdout.bin"), "stderr_sha256": sha(EV / "docker.stderr.bin"),
          "raw_present": (OUT / "construction_raw.json").exists(), "formal_fit_count": stop["formal_fit_count"]}
(EV / "STOP_AUDIT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if not errors else 2)


