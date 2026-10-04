#!/usr/bin/env python3
"""Read-only integrity check; never launches the candidate or formal auditor."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

checksums = {}
for line in (ROOT / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
    digest, name = line.split("  ", 1)
    checksums[name] = digest
for name, expected in checksums.items():
    path = ROOT / name
    assert path.is_file() and sha(path) == expected, f"checksum mismatch: {name}"

freeze = json.loads((ROOT / "freeze.json").read_text(encoding="utf-8"))
for key, name in (("candidate_sha256", "candidate.py"), ("auditor_sha256", "auditor.py"),
                  ("cases_sha256", "cases.json"), ("protocol_sha256", "PROTOCOL.md"),
                  ("freeze_builder_sha256", "freeze_builder.py")):
    assert sha(ROOT / name) == freeze["source_hashes"][key], f"frozen source mismatch: {name}"

raw = json.loads((ROOT / "output/candidate/candidate.raw.json").read_text(encoding="utf-8"))
audit = json.loads((ROOT / "output/auditor/audit.json").read_text(encoding="utf-8"))
assert len(raw["runs"]) == 18
assert audit["method"] == "METHOD_PASS_SCOPED"
assert audit["hypothesis"] == "FAIL_HYPOTHESIS"
assert audit["errors"] == []
assert len(raw["runs"]) == 18
assert all(audit["mutation_rejections"].values()) and len(audit["mutation_rejections"]) == 6

for case, shared, reserved, misses in (
    ("sched_seed_7722", 584, 166, 3),
    ("sched_seed_7723", 586, 168, 2),
    ("sched_seed_7724", 561, 131, 1),
):
    m = audit["metrics"]
    assert m[f"{case}/shared_priority"]["p99_response_ticks"] == shared
    assert m[f"{case}/reserved_server"]["p99_response_ticks"] == reserved
    assert m[f"{case}/shared_priority"]["control_deadline_misses"] == 10
    assert m[f"{case}/reserved_server"]["control_deadline_misses"] == misses
    assert m[f"{case}/shared_priority"]["best_effort_completed"] == 192
    assert m[f"{case}/reserved_server"]["best_effort_completed"] == 190

warning = b"Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap."
for lane in ("candidate", "auditor"):
    out = ROOT / "output" / lane
    meta = json.loads((out / "run-meta.json").read_text(encoding="utf-8"))
    assert meta["exit_code"] == 0 and meta["retry_count"] == 0
    assert warning in (out / "wslc.stderr.log").read_bytes()
print("PASS_RETAINED_EVIDENCE_INTEGRITY; candidate/auditor were not rerun")
