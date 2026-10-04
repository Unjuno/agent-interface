"""Reproduce the predecessor false pass and save the corrected audit outputs."""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"
RESULTS = HERE / "results"


def run(command, *, cwd):
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    pinned = {
        "predecessor-audit.py": freeze["input_sha256"]["predecessor/audit.py"],
        "raw.json": freeze["input_sha256"]["predecessor/raw.json"],
        "experiment-output.json": freeze["input_sha256"]["predecessor/experiment-output.json"],
    }
    for name, digest in pinned.items():
        actual = hashlib.sha256((INPUTS / name).read_bytes()).hexdigest()
        if actual != digest:
            raise SystemExit(f"frozen input mismatch: {name}: {actual}")

    RESULTS.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        raw_path = root / "raw.json"
        output_path = root / "experiment-output.json"
        shutil.copy2(INPUTS / "raw.json", raw_path)
        shutil.copy2(INPUTS / "experiment-output.json", output_path)
        shutil.copy2(INPUTS / "predecessor-audit.py", root / "audit.py")
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        w_row = next(
            row for row in raw["events"]
            if row.get("kind") == "key_interval" and row.get("key") == "W"
        )
        w_row["release_sync_ns"] += 1
        w_row["up_sample_ns"] += 1
        raw_path.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
        (RESULTS / "mutated-raw.json").write_bytes(raw_path.read_bytes())

        baseline = run([sys.executable, str(root / "audit.py")], cwd=root)
        (RESULTS / "baseline-audit.stdout.txt").write_text(baseline.stdout, encoding="utf-8")
        (RESULTS / "baseline-audit.stderr.txt").write_text(baseline.stderr, encoding="utf-8")
        (RESULTS / "baseline-audit.exit").write_text(f"{baseline.returncode}\n", encoding="utf-8")

        corrected = run(
            [
                sys.executable, str(HERE / "audit_recheck.py"),
                "--raw", str(INPUTS / "raw.json"),
                "--candidate-output", str(INPUTS / "experiment-output.json"),
                "--report-out", str(RESULTS / "audit-output.json"),
            ],
            cwd=HERE,
        )
        (RESULTS / "audit.stdout.txt").write_text(corrected.stdout, encoding="utf-8")
        (RESULTS / "audit.stderr.txt").write_text(corrected.stderr, encoding="utf-8")
        (RESULTS / "audit.exit").write_text(f"{corrected.returncode}\n", encoding="utf-8")

        stale = run(
            [
                sys.executable, str(HERE / "audit_recheck.py"),
                "--raw", str(RESULTS / "mutated-raw.json"),
                "--candidate-output", str(INPUTS / "experiment-output.json"),
                "--report-out", str(RESULTS / "mutated-stale-audit.json"),
            ],
            cwd=HERE,
        )
        (RESULTS / "mutated-stale-audit.stdout.txt").write_text(stale.stdout, encoding="utf-8")
        (RESULTS / "mutated-stale-audit.stderr.txt").write_text(stale.stderr, encoding="utf-8")
        (RESULTS / "mutated-stale-audit.exit").write_text(f"{stale.returncode}\n", encoding="utf-8")

    result = {
        "allocation": freeze["allocation"],
        "status": "PASS_AUDIT_MUTATION_SENSITIVITY" if (
            baseline.returncode == 0 and corrected.returncode == 0 and stale.returncode == 1
        ) else "FAIL_AUDIT_RECHECK",
        "frozen_auditor_mutated_raw_exit": baseline.returncode,
        "corrected_auditor_original_pair_exit": corrected.returncode,
        "corrected_auditor_mutated_raw_stale_output_exit": stale.returncode,
        "mutated_field": "W.release_sync_ns and W.up_sample_ns each increased by 1 ns",
        "candidate_invocations_added": 0,
        "live_allocations_added": 0,
        "scope": "raw-derived audit mutation sensitivity over one retained synthetic fixture",
    }
    (RESULTS / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS_AUDIT_MUTATION_SENSITIVITY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
