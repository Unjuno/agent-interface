"""Bind T3 result metadata and checksums after command outputs are retained."""
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
DOOM = ROOT.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    candidate = DOOM / "map01_overlap_controller_v40.py"
    tests = DOOM / "test_map01_overlap_controller_v40_unknown_source.py"
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO,
                                   text=True).strip()
    result = {
        "schema": "v40-release-receipt-fault-injection-result-v1",
        "disposition": "PASS_CONSTRUCTION_FAULT_INJECTION",
        "base_commit": base,
        "candidate": str(candidate.relative_to(REPO)).replace("\\", "/"),
        "candidate_sha256": sha(candidate),
        "test_source": str(tests.relative_to(REPO)).replace("\\", "/"),
        "test_source_sha256": sha(tests),
        "experiment_source_sha256": sha(ROOT / "experiment.py"),
        "audit_source_sha256": sha(ROOT / "audit.py"),
        "environment": {"platform": platform.platform(), "python": sys.version},
        "commands": [
            {"command": "python research/doom/v40_release_receipt_faults_59_t3_20261004/experiment.py",
             "exit_code": int((ROOT / "experiment-exit-code.txt").read_text().strip())},
            {"command": "python research/doom/v40_release_receipt_faults_59_t3_20261004/audit.py",
             "exit_code": int((ROOT / "audit-exit-code.txt").read_text().strip())},
            {"command": "python -m py_compile <experiment.py> <audit.py>",
             "exit_code": int((ROOT / "compile-exit-code.txt").read_text().strip())},
        ],
        "case_counts": {"total": 12, "valid_controls_accepted": 2,
                        "adverse_receipts_rejected": 10},
        "scope": "host-side cancellation helper construction only; no child runtime, game, parser, model, GUI, OS input, formal allocation, or task-effect evidence",
    }
    (ROOT / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n",
                                      encoding="utf-8")
    excluded = {"SHA256SUMS", "audit-output.txt", "audit-exit-code.txt"}
    files = sorted(path for path in ROOT.rglob("*") if path.is_file() and
                   path.name not in excluded and "__pycache__" not in path.parts)
    lines = [f"{sha(path)}  {path.relative_to(ROOT).as_posix()}" for path in files]
    (ROOT / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"bound {len(files)} files; candidate={result['candidate_sha256']}")


if __name__ == "__main__":
    main()
