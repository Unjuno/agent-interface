from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
VERIFY = HERE / "verify_runtime_preview_candidate_v1.py"
SUMS = HERE / "make_sha256sums_v1.py"

CHECKER = """from pathlib import Path
import json, hashlib, sys
root = Path(sys.argv[1])
pre = root / 'research/live_control/results/integrated-efficiency-live-01/preregistration.json'
ok = pre.is_file()
if ok:
    data = json.loads(pre.read_text())
    for name, expected in data['sources'].items():
        path = root / 'research/live_control' / name
        ok = ok and path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected
    for name in ('report.json', 'audit.json'):
        ok = ok and (pre.parent / name).is_file()
print(json.dumps({'passed': ok}))
raise SystemExit(0 if ok else 1)
"""

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def make_good(root: Path) -> None:
    for rel in ("runtime/setup-golden-demo-v3.sh", "runtime/golden-demo-v3.sh"):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/sh\nexit 0\n")
        path.chmod(0o755)
    for rel in ("runtime/golden_desktop_demo_v3.py", "runtime/requirements-golden.txt", "runtime/README.md"):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n")
    checker = root / "release/golden_artifact_closure_v1/check_golden_artifact_closure.py"
    checker.parent.mkdir(parents=True, exist_ok=True)
    checker.write_text(CHECKER)
    source = root / "research/live_control/source.txt"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"source")
    retained = root / "research/live_control/results/integrated-efficiency-live-01"
    retained.mkdir(parents=True, exist_ok=True)
    (retained / "preregistration.json").write_text(json.dumps({"sources": {"source.txt": sha(b"source")}}))
    (retained / "report.json").write_text("{}")
    (retained / "audit.json").write_text("{}")
    support = root / "release/runtime_preview_v1/support.json"
    support.parent.mkdir(parents=True, exist_ok=True)
    support.write_text(json.dumps({
        "schema": "agent-interface-runtime-preview-support-v1",
        "tested_host": "WSLg",
        "release_candidate_sha": "a" * 40,
        "research_preview": True,
    }))
    subprocess.run([sys.executable, str(SUMS), str(root)], check=True, capture_output=True)

def verify(root: Path) -> tuple[int, dict]:
    process = subprocess.run([sys.executable, str(VERIFY), str(root)], capture_output=True, text=True)
    return process.returncode, json.loads(process.stdout)

def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory) / "good"
        make_good(base)
        code, result = verify(base)
        assert code == 0 and result["passed"] is True

        mode = Path(directory) / "bad-mode"
        shutil.copytree(base, mode)
        (mode / "runtime/golden-demo-v3.sh").chmod(0o644)
        code, result = verify(mode)
        assert code == 1 and "launcher_executable" in result["failures"]

        tampered = Path(directory) / "bad-checksum"
        shutil.copytree(base, tampered)
        (tampered / "runtime/README.md").write_text("tampered\n")
        code, result = verify(tampered)
        assert code == 1 and "checksums" in result["failures"]

        closure = Path(directory) / "bad-closure"
        shutil.copytree(base, closure)
        (closure / "research/live_control/source.txt").unlink()
        subprocess.run([sys.executable, str(SUMS), str(closure)], check=True, capture_output=True)
        code, result = verify(closure)
        assert code == 1 and "golden_retained_closure" in result["failures"]

        support = Path(directory) / "bad-support"
        shutil.copytree(base, support)
        (support / "release/runtime_preview_v1/support.json").write_text("{}")
        subprocess.run([sys.executable, str(SUMS), str(support)], check=True, capture_output=True)
        code, result = verify(support)
        assert code == 1 and "support_metadata" in result["failures"]

    print("PASS 5/5")

if __name__ == "__main__":
    main()
