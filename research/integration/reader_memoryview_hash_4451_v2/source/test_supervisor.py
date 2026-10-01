"""Construction-only executable checks for complete and interrupted runs."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STUDY = ROOT.parent
IMAGE_ID = json.loads((STUDY / "FREEZE.json").read_text(encoding="utf-8"))["container_image_id"]


def invoke(*args, timeout=30):
    return subprocess.run(
        [sys.executable, "-B", str(ROOT / "supervise.py"), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def test_normal_construction():
    with tempfile.TemporaryDirectory(prefix="reader-memoryview-normal-") as directory:
        out = Path(directory) / "normal"
        process = invoke(
            "--phase", "construction", "--out", str(out), "--image-id", IMAGE_ID,
        )
        assert process.returncode == 0, process.stdout + process.stderr
        raw = json.loads((out / "RAW.json").read_text(encoding="utf-8"))
        assert len(raw["resource"]) == 6
        assert len(raw["contracts"]) == 2
        assert raw["stop_reason"] is None
        assert (out / "PROGRESS.jsonl").exists()
        supervisor = out.parent / "normal.SUPERVISOR.json"
        assert json.loads(supervisor.read_text(encoding="utf-8"))["return_code"] == 0
        audit = subprocess.run(
            [sys.executable, "-B", str(ROOT / "audit.py"), str(out / "RAW.json")],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
        assert audit.returncode == 0 and "PASS_CONSTRUCTION" in audit.stdout, audit.stdout + audit.stderr
        controls = subprocess.run(
            [sys.executable, "-B", str(ROOT / "controls.py")],
            cwd=ROOT, capture_output=True, text=True, timeout=120,
        )
        assert controls.returncode == 0 and '"rejected": 16' in controls.stdout, controls.stdout + controls.stderr


def test_supervisor_timeout_retains_partial_evidence():
    with tempfile.TemporaryDirectory(prefix="reader-memoryview-timeout-") as directory:
        out = Path(directory) / "interrupted"
        process = invoke(
            "--phase", "construction",
            "--out", str(out),
            "--image-id", IMAGE_ID,
            "--timeout-seconds", "1.0",
            "--inject-worker-delay-seconds", "5.0",
            timeout=10,
        )
        assert process.returncode == 124, process.stdout + process.stderr
        stop = json.loads((out / "STOP.json").read_text(encoding="utf-8"))
        partial = json.loads((out / "RAW_PARTIAL.json").read_text(encoding="utf-8"))
        assert stop["reason"] == "STOP_SUPERVISOR_TIMEOUT"
        assert stop["completed_resource_workers"] == 0
        assert stop["started_workers"] == 1
        assert len(stop["corpus_sha256"]) == 64
        assert partial["stop_reason"] == "STOP_SUPERVISOR_TIMEOUT"
        assert partial["journal_sha256"] == stop["journal_sha256"]
        assert partial["worker_starts"][0]["worker_id"] == "001"
        assert (out / "worker-001.stdout").exists()
        assert (out / "worker-001.stderr").exists()
        assert not (out / "RAW.json").exists()
        stop_audit = subprocess.run(
            [sys.executable, "-B", str(ROOT / "stop_audit.py"), str(out / "STOP.json")],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
        assert stop_audit.returncode == 0 and "PASS_STOP_EVIDENCE_RETAINED" in stop_audit.stdout, stop_audit.stdout + stop_audit.stderr


def main():
    test_normal_construction()
    test_supervisor_timeout_retains_partial_evidence()
    print(json.dumps({"status": "PASS_CONSTRUCTION_SUPERVISOR", "normal": 1, "injected_timeout": 1}))


if __name__ == "__main__":
    main()
