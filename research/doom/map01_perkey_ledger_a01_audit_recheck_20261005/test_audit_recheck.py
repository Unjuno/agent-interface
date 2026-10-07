import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"
FROZEN_AUDITOR = INPUTS / "predecessor-audit.py"
CORRECTED_AUDITOR = HERE / "audit_recheck.py"


def prepare_case(root, *, mutate_raw=False, refresh_w_output=False):
    raw_path = root / "raw.json"
    output_path = root / "experiment-output.json"
    shutil.copy2(INPUTS / "raw.json", raw_path)
    shutil.copy2(INPUTS / "experiment-output.json", output_path)
    if mutate_raw:
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        w_row = next(
            row for row in raw["events"]
            if row.get("kind") == "key_interval" and row.get("key") == "W"
        )
        w_row["release_sync_ns"] += 1
        w_row["up_sample_ns"] += 1
        raw_path.write_text(json.dumps(raw), encoding="utf-8")
    if refresh_w_output:
        output = json.loads(output_path.read_text(encoding="utf-8"))
        for case_name in ("complete_correct_inventory", "omitted_underdeclared_inventory"):
            w_row = next(
                row for row in output["cases"][case_name]["intervals"]
                if row["key"] == "W"
            )
            w_row["upper_ns"] += 1
        output_path.write_text(json.dumps(output), encoding="utf-8")
    return raw_path, output_path


def run_auditor(auditor, raw_path, output_path, report_path):
    return subprocess.run(
        [
            sys.executable, str(auditor), "--raw", str(raw_path),
            "--candidate-output", str(output_path), "--report-out", str(report_path),
        ],
        cwd=HERE,
        text=True,
        capture_output=True,
        check=False,
    )


class FrozenAuditorMutationTests(unittest.TestCase):
    def test_frozen_auditor_accepts_stale_interval_after_timestamp_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copy2(FROZEN_AUDITOR, root / "audit.py")
            raw_path, output_path = prepare_case(root, mutate_raw=True)
            run = subprocess.run(
                [sys.executable, str(root / "audit.py")],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(
                run.returncode,
                0,
                "expected to reproduce the known historical fail-open before the additive audit fix",
            )

    def test_corrected_auditor_passes_unmodified_frozen_pair(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw_path, output_path = prepare_case(root)
            report_path = root / "audit.json"
            run = run_auditor(CORRECTED_AUDITOR, raw_path, output_path, report_path)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS_RAW_DERIVED_AUDIT")
            self.assertEqual(
                report["expected_cases_raw_derived"]["complete_correct_inventory"]["intervals"][1]["upper_ns"],
                90,
            )

    def test_corrected_auditor_rejects_stale_output_after_raw_timestamp_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw_path, output_path = prepare_case(root, mutate_raw=True)
            report_path = root / "audit.json"
            run = run_auditor(CORRECTED_AUDITOR, raw_path, output_path, report_path)
            self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "FAIL_AUDIT")
            self.assertFalse(
                report["checks"]["all_candidate_interval_rows_match_raw_derived_bounds"]
            )
            expected_w = next(
                row for row in report["expected_cases_raw_derived"]["complete_correct_inventory"]["intervals"]
                if row["key"] == "W"
            )
            self.assertEqual(expected_w["upper_ns"], 91)

    def test_corrected_auditor_accepts_recomputed_raw_derived_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw_path, output_path = prepare_case(
                root, mutate_raw=True, refresh_w_output=True
            )
            report_path = root / "audit.json"
            run = run_auditor(CORRECTED_AUDITOR, raw_path, output_path, report_path)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            expected_w = next(
                row for row in report["expected_cases_raw_derived"]["complete_correct_inventory"]["intervals"]
                if row["key"] == "W"
            )
            self.assertEqual(expected_w["upper_ns"], 91)


if __name__ == "__main__":
    unittest.main()
