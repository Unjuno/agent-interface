#!/usr/bin/env python3
"""Prove A02 rejects a source timestamp changed only in a copied report."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import audit as audit_a01  # noqa: E402
import audit_a02  # noqa: E402


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    original_run = audit_a01.RUN
    retained_before = {name: sha256(original_run / name) for name in (
        "report.json", "runtime/events.jsonl", "runtime/sources.json",
        "runtime/218.png", "audit-v2.json", "retention-manifest.json")}
    with tempfile.TemporaryDirectory(prefix="v39-a02-report-timestamp-") as temporary:
        copied_run = Path(temporary) / "run"
        shutil.copytree(original_run, copied_run)
        report_path = copied_run / "report.json"
        report = json.loads(report_path.read_text())
        source = report["decisions"][5]["cover_validity_admission"]["source_signal"]
        source["capture_ns"] += 1_000_000_000
        report_path.write_text(json.dumps(report, indent=2) + "\n")

        manifest_path = copied_run / "retention-manifest.json"
        manifest = json.loads(manifest_path.read_text())
        row = next(row for row in manifest["files"] if row["path"] == "report.json")
        row["sha256"] = sha256(report_path)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

        audit_a01.RUN = copied_run
        legacy_stdout = io.StringIO()
        with contextlib.redirect_stdout(legacy_stdout):
            audit_a01.main()
        legacy_result = json.loads(legacy_stdout.getvalue())

        audit_a02.RUN = copied_run
        corrected_stdout = io.StringIO()
        try:
            with contextlib.redirect_stdout(corrected_stdout):
                audit_a02.main()
        except SystemExit as error:
            corrected_error = str(error)
        else:
            raise SystemExit("A02 accepted a source capture timestamp absent from raw events")

        if legacy_result["timing_ms"]["source_capture_to_guard_evaluation"] == 9.440718045:
            raise SystemExit("control did not change the legacy derived timing")
        if "source sequence/time/value differs" not in corrected_error:
            raise SystemExit(f"A02 rejected the control for an unexpected reason: {corrected_error}")
        if any(sha256(original_run / name) != value
               for name, value in retained_before.items()):
            raise SystemExit("control modified retained source artifacts")

        result = {
            "control": "decision5_source_capture_timestamp_plus_1s",
            "copied_report_hash_updated_in_copied_retention_manifest": True,
            "legacy_a01_status": "PASS",
            "legacy_a01_reported_source_to_guard_ms": legacy_result["timing_ms"]["source_capture_to_guard_evaluation"],
            "corrected_a02_status": "REJECTED",
            "corrected_a02_error": corrected_error,
            "retained_source_artifacts_modified": False,
        }
        destination = HERE / "results/a02/report_timestamp_control.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
            handle.write("\n")
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
