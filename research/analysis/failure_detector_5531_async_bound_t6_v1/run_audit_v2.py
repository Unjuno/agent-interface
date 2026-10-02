"""One-shot corrective independent audit; never regenerates the candidate trace."""
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    manifest = json.loads((HERE / "SOURCE_MANIFEST_V2.json").read_text(encoding="utf-8"))
    source_checks = {}
    for name, expected in manifest["sources"].items():
        actual = sha256(HERE / name)
        source_checks[name] = {"expected": expected, "actual": actual, "matches": actual == expected}
    if not all(item["matches"] for item in source_checks.values()):
        raise SystemExit("audit-v2 source manifest mismatch; no auditor invocation")

    freeze = json.loads((HERE / "AUDIT_V2_FREEZE.json").read_text(encoding="utf-8"))
    raw = HERE / freeze["raw_path"]
    if sha256(raw) != freeze["raw_sha256"]:
        raise SystemExit("preserved raw identity mismatch; no auditor invocation")

    result_dir = HERE / "results/t6-e1-03-audit-correction"
    result_dir.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(HERE / "correction-v1.json", result_dir / "CORRECTION.json")
    audit_path = result_dir / "audit-v2.json"
    argv = [sys.executable, "-B", "audit_v2.py", "--raw", str(raw), "--freeze",
            str(HERE / "AUDIT_V2_FREEZE.json"), "--output", str(audit_path)]
    process = subprocess.Popen(argv, cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    try:
        stdout, stderr = process.communicate(timeout=20)
        timed_out = False
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        timed_out = True
    (result_dir / "auditor-v2.stdout.txt").write_text(stdout, encoding="utf-8")
    (result_dir / "auditor-v2.stderr.txt").write_text(stderr, encoding="utf-8")
    audit = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.is_file() else {}
    execution = {
        "schema": "failure-detector-async-audit-v2-execution-v1",
        "base_main": manifest["base_main"],
        "source_manifest_sha256": sha256(HERE / "SOURCE_MANIFEST_V2.json"),
        "source_checks": source_checks,
        "raw_sha256": sha256(raw),
        "candidate_invocations": 0,
        "auditor_invocations": 1,
        "auditor_pid": process.pid,
        "auditor_argv": argv,
        "auditor_returncode": process.returncode,
        "auditor_timed_out": timed_out,
        "status": audit.get("status", "STOP_NO_AUDIT_V2"),
        "python_version": platform.python_version(),
        "host_platform": platform.platform(),
        "container_used": False,
    }
    (result_dir / "execution-v2.json").write_text(json.dumps(execution, indent=2, sort_keys=True) + "\n",
                                                   encoding="utf-8")
    print(json.dumps(execution, sort_keys=True))
    return 0 if process.returncode == 0 and not timed_out else 1


if __name__ == "__main__":
    raise SystemExit(main())
