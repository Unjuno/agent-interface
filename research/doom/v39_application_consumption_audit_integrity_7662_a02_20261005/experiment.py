"""Run the frozen #7662 saved-result auditor on baseline and one raw mutation."""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze_path = ROOT / "FREEZE.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    frozen = ROOT / "frozen"
    baseline_dir = ROOT / "cases" / "baseline"
    mutated_dir = ROOT / "cases" / "label_swap"
    baseline_dir.mkdir(parents=True, exist_ok=False)
    mutated_dir.mkdir(parents=True, exist_ok=False)
    shutil.copytree(frozen, baseline_dir, dirs_exist_ok=True)
    shutil.copytree(frozen, mutated_dir, dirs_exist_ok=True)

    baseline_raw_path = baseline_dir / "raw" / "A01.json"
    mutated_raw_path = mutated_dir / "raw" / "A01.json"
    original_raw = json.loads(baseline_raw_path.read_text(encoding="utf-8"))
    mutated_raw = json.loads(json.dumps(original_raw))
    for implementation in ("baseline", "candidate"):
        cases = mutated_raw["interval_sweep"][implementation]["cases"]
        ordered = cases[freeze["mutation"]["ordered_index"]]
        unordered = cases[freeze["mutation"]["unordered_index"]]
        ordered["expected_ordered"] = False
        ordered["status"] = "adapter_edge_receipt_incomplete"
        ordered["down_edge_interval_ns"] = None
        ordered["up_edge_interval_ns"] = None
        unordered["expected_ordered"] = True
        unordered["status"] = "adapter_edge_brackets_paired"
        unordered["down_edge_interval_ns"] = unordered["down"]
        unordered["up_edge_interval_ns"] = unordered["up"]
    mutated_raw_path.write_text(json.dumps(mutated_raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    records = {}
    for label, case_dir, raw_path in (
        ("baseline", baseline_dir, baseline_raw_path),
        ("mutated", mutated_dir, mutated_raw_path),
    ):
        completed = subprocess.run(
            [sys.executable, "audit_a01.py"], cwd=case_dir,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        (ROOT / f"{label.upper()}.stdout.txt").write_bytes(completed.stdout)
        (ROOT / f"{label.upper()}.stderr.txt").write_bytes(completed.stderr)
        (ROOT / f"{label.upper()}.exit.txt").write_text(str(completed.returncode) + "\n", encoding="utf-8")
        (case_dir / "auditor.stdout").write_bytes(completed.stdout)
        (case_dir / "auditor.stderr").write_bytes(completed.stderr)
        (case_dir / "auditor.exit.txt").write_text(str(completed.returncode) + "\n", encoding="utf-8")
        (case_dir / "auditor.stdout").write_bytes(completed.stdout)
        (case_dir / "auditor.stderr").write_bytes(completed.stderr)
        (case_dir / "auditor.exit.txt").write_text(str(completed.returncode) + "\n", encoding="utf-8")
        saved = json.loads((case_dir / "raw" / "AUDIT.json").read_text(encoding="utf-8"))
        records[label] = {
            "directory": f"cases/{label if label == 'baseline' else 'label_swap'}",
            "exit_code": completed.returncode,
            "audit_status": saved.get("status"),
            "raw_sha256": sha(raw_path),
            "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
        }

    run = {
        "experiment_id": freeze["experiment_id"],
        "freeze_sha256": sha(freeze_path),
        "frozen_raw_sha256": sha(frozen / "raw" / "A01.json"),
        "invocations": 2,
        "baseline": records["baseline"],
        "mutated": records["mutated"],
        "scope": "One saved-result auditor invocation per frozen arm; no candidate or live allocation rerun.",
    }
    outcome = "FAIL_AUDITOR_ACCEPTS_LABEL_SWAP" if (
        records["baseline"]["exit_code"] == 0 and
        records["baseline"]["audit_status"] == "PASS_SAVED_RESULT_AUDIT" and
        records["mutated"]["exit_code"] == 0 and
        records["mutated"]["audit_status"] == "PASS_SAVED_RESULT_AUDIT"
    ) else "HOLD_FALSE_PASS_NOT_REPRODUCED"
    run["outcome"] = outcome
    encoded = json.dumps(run, indent=2, sort_keys=True) + "\n"
    (ROOT / "RUN.json").write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
