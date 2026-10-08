"""Write stable SHA256SUMS for this package and the tested source inputs."""
import hashlib
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
paths = [
    "research/doom/doom_typed_release_backend_v3.py",
    "research/doom/test_doom_typed_release_backend_v3.py",
    "research/doom/map01-v39-release-cleanup-overlap-v1/README.md",
    "research/doom/map01-v39-release-cleanup-overlap-v1/PLAN.md",
    "research/doom/map01-v39-release-cleanup-overlap-v1/RUN_COMMANDS.md",
    "research/doom/map01-v39-release-cleanup-overlap-v1/FREEZE.json",
    "research/doom/map01-v39-release-cleanup-overlap-v1/FOLLOWUP_EXECUTION.json",
    "research/doom/map01-v39-release-cleanup-overlap-v1/RESULT.md",
    "research/doom/map01-v39-release-cleanup-overlap-v1/RESULT.json",
    "research/doom/map01-v39-release-cleanup-overlap-v1/audit.py",
    "research/doom/map01-v39-release-cleanup-overlap-v1/test_audit.py",
    "research/doom/map01-v39-release-cleanup-overlap-v1/run_baseline.py",
    "research/doom/map01-v39-release-cleanup-overlap-v1/write_checksums.py",
    "research/doom/map01-v39-release-cleanup-overlap-v1/WSLC_INFO.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/WSLC_IMAGE.json",
    "research/doom/map01-v39-release-cleanup-overlap-v1/results/HOST_PYTHON.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/results/RAW_BASELINE_DIRECT_BOUNDARY.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/results/BASELINE_DIRECT_EXIT.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/results/RAW_BASELINE.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/results/BASELINE_EXIT.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/results/RAW_CANDIDATE.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/results/CANDIDATE_EXIT.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/results/RAW_CANDIDATE_WSLC_DIRECT_BOUNDARY.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/results/CANDIDATE_WSLC_EXIT.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/results/RAW_ADJACENT.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/results/ADJACENT_EXIT.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/results/RAW_OWNER_WRAPPER_HOST.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/results/OWNER_WRAPPER_EXIT.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/results/RAW_AUDIT_WSLC_INITIAL.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/results/RAW_AUDIT.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/results/AUDIT_EXIT.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/results/RAW_AUDITOR_TESTS.txt",
]
lines = []
for rel in paths:
    data = (REPO / rel).read_bytes()
    lines.append(f"{hashlib.sha256(data).hexdigest()}  {rel}")
(HERE / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {len(lines)} SHA256 entries")
