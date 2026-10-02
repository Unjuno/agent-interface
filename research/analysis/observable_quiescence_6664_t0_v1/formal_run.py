"""Single-shot frozen-input candidate/auditor runner for Issue #6664 T0."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import auditor
import candidate
import scenarios


HERE = Path(__file__).resolve().parent
SOURCES = (
    "README.md", "preregistration.md", "scenarios.py", "candidate.py",
    "auditor.py", "test_scenarios.py", "test_auditor_controls.py",
    "formal_run.py",
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(output_dir: Path) -> int:
    if output_dir.exists():
        raise FileExistsError(f"formal output path already exists: {output_dir}")
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    expected = freeze["source_sha256"]
    observed = {name: _sha((HERE / name).read_bytes()) for name in SOURCES}
    fixture_sha = _sha(scenarios.canonical_bytes())
    if observed != expected or fixture_sha != freeze["fixture_sha256"]:
        raise RuntimeError("frozen source or fixture digest mismatch; no formal run made")

    output_dir.mkdir(parents=True)
    record = {
        "allocation": freeze["allocation"],
        "status": "RUNNING",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "host_scope": "host-local standard library; no container/runtime backend",
        "candidate_invocations": 0,
        "auditor_invocations": 0,
        "frozen_source_sha256": observed,
        "fixture_sha256": fixture_sha,
    }
    (output_dir / "RUN_RECORD.json").write_text(
        json.dumps(record, sort_keys=True, indent=2) + "\n")

    raw = candidate.run()
    record["candidate_invocations"] = 1
    raw_bytes = (json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n").encode()
    (output_dir / "raw.json").write_bytes(raw_bytes)
    (output_dir / "candidate.exit.txt").write_text("0\n")

    classification = auditor.audit(raw)
    record["auditor_invocations"] = 1
    record["auditor_exit"] = 0 if classification["status"] == "PASS_METHOD_SCOPED" else 1
    (output_dir / "classification.json").write_text(
        json.dumps(classification, sort_keys=True, indent=2) + "\n")
    (output_dir / "auditor.exit.txt").write_text(f"{record['auditor_exit']}\n")
    record["finished_utc"] = datetime.now(timezone.utc).isoformat()
    record["status"] = classification["status"]
    record["raw_sha256"] = _sha(raw_bytes)
    (output_dir / "RUN_RECORD.json").write_text(
        json.dumps(record, sort_keys=True, indent=2) + "\n")

    tracked = ["RUN_RECORD.json", "raw.json", "classification.json",
               "candidate.exit.txt", "auditor.exit.txt"]
    lines = [f"{_sha((output_dir / name).read_bytes())}  {name}" for name in tracked]
    (output_dir / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")
    print(json.dumps({"status": record["status"],
                      "case_count": classification.get("case_count"),
                      "false_quiescent": classification.get("false_quiescent"),
                      "output": str(output_dir)}, sort_keys=True))
    return record["auditor_exit"]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 formal_run.py OUTPUT_DIRECTORY")
    raise SystemExit(run(Path(sys.argv[1]).resolve()))
