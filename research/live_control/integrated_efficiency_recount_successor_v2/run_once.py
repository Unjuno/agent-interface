"""One-shot runner retaining host test and independent recount outputs."""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
FREEZE = HERE / "FREEZE.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: run_once.py REPOSITORY_ROOT OUTPUT_DIRECTORY")
    root, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if freeze.get("schema") != "integrated-efficiency-recount-v2-freeze-v1":
        raise SystemExit("STOP_FREEZE_SCHEMA")
    if out.exists():
        raise SystemExit(f"STOP_OUTPUT_EXISTS: {out}")
    if out.relative_to(root).as_posix() != freeze["outputs"]["path"]:
        raise SystemExit("STOP_OUTPUT_PATH_MISMATCH")
    for rel, expected in freeze["source_sha256"].items():
        if digest(HERE / rel) != expected:
            raise SystemExit(f"STOP_SOURCE_HASH: {rel}")
    manifest_path = root / freeze["input_manifest_path"]
    if digest(manifest_path) != freeze["input_manifest_sha256"]:
        raise SystemExit("STOP_INPUT_MANIFEST_HASH")

    out.mkdir(parents=True, exist_ok=False)
    started = time.time_ns()
    test_cmd = [sys.executable, "-B", str(HERE / "test_recount_v2.py")]
    test = subprocess.run(test_cmd, cwd=root, capture_output=True, text=True)
    (out / "test.stdout.txt").write_text(test.stdout, encoding="utf-8")
    (out / "test.stderr.txt").write_text(test.stderr, encoding="utf-8")
    (out / "test.exit-code").write_text(f"{test.returncode}\n", encoding="ascii")

    audit = None
    if test.returncode == 0:
        audit_cmd = [sys.executable, "-B", str(HERE / "audit_recount_v2.py"),
                     str(root), str(out / "audit-output"), str(FREEZE), str(manifest_path)]
        audit = subprocess.run(audit_cmd, cwd=root, capture_output=True, text=True)
        (out / "audit.stdout.txt").write_text(audit.stdout, encoding="utf-8")
        (out / "audit.stderr.txt").write_text(audit.stderr, encoding="utf-8")
        (out / "audit.exit-code").write_text(f"{audit.returncode}\n", encoding="ascii")

    receipt = {
        "schema": "integrated-efficiency-recount-v2-host-run-v1",
        "allocation": freeze["allocation"],
        "status": "PASS_RECOUNT_PROVENANCE_AND_ACCOUNTING_SCOPED"
                  if test.returncode == 0 and audit is not None and audit.returncode == 0
                  else "FAIL_OR_STOP_RECOUNT_V2",
        "runtime": sys.version,
        "platform": sys.platform,
        "python_executable": sys.executable,
        "commands": {"tests": test_cmd,
                      "audit": None if audit is None else audit_cmd},
        "test_exit_code": test.returncode,
        "audit_exit_code": None if audit is None else audit.returncode,
        "started_ns": started,
        "ended_ns": time.time_ns(),
        "no_model_gui_input_or_network": True,
        "docker_used": False,
    }
    (out / "execution.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
