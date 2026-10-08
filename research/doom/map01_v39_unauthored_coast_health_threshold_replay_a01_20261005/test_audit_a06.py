#!/usr/bin/env python3
"""Synthetic copied-report swap control for the A06 audit correction."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_sums(path):
    rows = path.read_text().replace("\\n", "\n").splitlines()
    return [(value, name) for row in rows for value, name in [row.split("  ", 1)]]


def write_sums(path, entries):
    path.write_text("\\n".join(f"{value}  {name}" for value, name in entries) + "\n")


def copy_inputs(target):
    source = ROOT / "input/a04"
    target.mkdir(parents=True)
    for name in ("PACKAGE_SHA256SUMS.txt", "RAW_SHA256SUMS.txt", "SOURCE_MANIFEST.json",
                 "FREEZE.json", "RESULT.json", "AUDIT.json", "report.json"):
        shutil.copy2(source / name, target / name)
    (target / "runtime").mkdir()
    shutil.copy2(source / "runtime/events.jsonl", target / "runtime/events.jsonl")


def main():
    with tempfile.TemporaryDirectory(prefix="a06-report-swap-") as temporary:
        temp = Path(temporary)
        input_dir = temp / "input/a04"
        copy_inputs(input_dir)
        shutil.copy2(ROOT / "audit.py", temp / "audit.py")
        shutil.copy2(ROOT / "audit_a06.py", temp / "audit_a06.py")
        shutil.copy2(ROOT / "FREEZE.json", temp / "FREEZE.json")

        candidate_dir = temp / "results/a05"
        candidate_dir.mkdir(parents=True)
        shutil.copy2(ROOT / "results/a05/candidate.json", candidate_dir / "candidate.json")

        report_path = input_dir / "report.json"
        report = json.loads(report_path.read_text())
        decision = report["decisions"][4]
        decision["cover_validity_admission"]["source_signal"], decision["policy_invalidation"]["signals"]["health"] = (
            decision["policy_invalidation"]["signals"]["health"],
            decision["cover_validity_admission"]["source_signal"],
        )
        report_path.write_text(json.dumps(report, indent=2) + "\n")
        report_sha = digest(report_path)

        raw_sums_path = input_dir / "RAW_SHA256SUMS.txt"
        raw_entries = read_sums(raw_sums_path)
        raw_entries = [(report_sha if name == "report.json" else value, name)
                       for value, name in raw_entries]
        write_sums(raw_sums_path, raw_entries)

        freeze_path = temp / "FREEZE.json"
        freeze = json.loads(freeze_path.read_text())
        freeze["source_report_sha256"] = report_sha
        freeze_path.write_text(json.dumps(freeze, indent=2) + "\n")

        package_path = input_dir / "PACKAGE_SHA256SUMS.txt"
        package_entries = read_sums(package_path)
        replacements = {
            "results/RAW_SHA256SUMS.txt": digest(raw_sums_path),
        }
        package_entries = [(replacements.get(name, value), name)
                           for value, name in package_entries]
        write_sums(package_path, package_entries)

        legacy_out = temp / "legacy-results/a05"
        legacy_out.mkdir(parents=True)
        legacy_env = os.environ.copy()
        legacy_env["RESULT_DIR"] = str(legacy_out)
        legacy = subprocess.run([sys.executable, str(temp / "audit.py")], cwd=temp,
                                env=legacy_env, text=True, capture_output=True, check=False)

        corrected_out = temp / "corrected-output/audit.json"
        corrected_env = os.environ.copy()
        corrected_env["AUDIT_INPUT_DIR"] = str(input_dir)
        corrected_env["AUDIT_FREEZE_PATH"] = str(freeze_path)
        corrected_env["AUDIT_OUTPUT"] = str(corrected_out)
        corrected = subprocess.run([sys.executable, str(temp / "audit_a06.py")], cwd=temp,
                                   env=corrected_env, text=True, capture_output=True, check=False)

        if legacy.returncode != 0 or "PASS_A04_TRACE_REPLAY_AUDIT" not in legacy.stdout:
            raise SystemExit("expected legacy A05 audit to accept the report-swap control")
        if corrected.returncode == 0 or corrected_out.exists():
            raise SystemExit("A06 must reject the report-swap control before creating output")
        if "AssertionError" not in corrected.stderr:
            raise SystemExit("A06 failed for an unexpected reason")

        result = {
            "control": "decision4_source_monitor_report_reference_swap",
            "temporary_source_sequence": 216,
            "temporary_monitor_sequence": 204,
            "copied_raw_package_and_freeze_manifests_updated": True,
            "legacy_a05_audit_exit_code": legacy.returncode,
            "legacy_a05_status": "PASS_A04_TRACE_REPLAY_AUDIT",
            "audit_a06_exit_code": corrected.returncode,
            "audit_a06_error": "AssertionError",
            "new_a06_output_created": corrected_out.exists(),
            "retained_inputs_modified": False,
        }
        destination = ROOT / "results/a06/audit_report_swap_control.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
            handle.write("\n")
        print(json.dumps(result))


if __name__ == "__main__":
    main()
