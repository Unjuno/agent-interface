"""Run the frozen construction and save each command's first output."""
import json
import subprocess
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
OUT = PACKAGE / "out"


def main():
    OUT.mkdir(exist_ok=True)
    py_files = [
        "audit_readonly_v2.py", "probe_legacy_mutation.py",
        "test_readonly_audit.py", "run_frozen_checks.py", "verify_manifest.py",
    ]
    commands = [
        ("pycompile", [sys.executable, "-B", "-m", "py_compile",
                        *[str(PACKAGE / name) for name in py_files]]),
        ("tests", [sys.executable, "-B", "-m", "unittest", "-v",
                    "research.doom.v39_readonly_audit_59_v2_20261005.test_readonly_audit"]),
        ("mutability_probe", [sys.executable, "-B",
                               str(PACKAGE / "probe_legacy_mutation.py"),
                               "--experiment-id",
                               "V39-READONLY-AUDIT-59-A02-V2-20261005",
                               "--out", "MUTABILITY_RESULT_A02.json"]),
        ("readonly_audit", [sys.executable, "-B",
                             str(PACKAGE / "audit_readonly_v2.py")]),
    ]
    results = []
    for name, command in commands:
        completed = subprocess.run(command, cwd=REPO, capture_output=True,
                                   text=True, check=False)
        (OUT / f"{name}.stdout.txt").write_text(completed.stdout,
                                                 encoding="utf-8")
        (OUT / f"{name}.stderr.txt").write_text(completed.stderr,
                                                 encoding="utf-8")
        (OUT / f"{name}.exit.txt").write_text(f"{completed.returncode}\n",
                                                encoding="utf-8")
        results.append({"name": name, "command": command,
                        "exit_code": completed.returncode,
                        "stdout_file": f"out/{name}.stdout.txt",
                        "stderr_file": f"out/{name}.stderr.txt",
                        "exit_file": f"out/{name}.exit.txt"})
        print(f"{name}: exit {completed.returncode}")
        if completed.stdout.strip():
            print(completed.stdout.strip())
        if completed.stderr.strip():
            print(completed.stderr.strip())
        if completed.returncode:
            break
    runs = {"schema": "v39-readonly-audit-v2-run-log-v1",
            "experiment_id": "V39-READONLY-AUDIT-59-A02-V2-20261005",
            "source_commit": "719ef679c977a925db3a6d1fe15f9cd93cf2b42c",
            "python": sys.version,
            "cwd": str(REPO),
            "runs": results}
    (PACKAGE / "RUNS.json").write_text(json.dumps(runs, indent=2) + "\n",
                                       encoding="utf-8")
    return next((row["exit_code"] for row in results if row["exit_code"]), 0)


if __name__ == "__main__":
    raise SystemExit(main())
