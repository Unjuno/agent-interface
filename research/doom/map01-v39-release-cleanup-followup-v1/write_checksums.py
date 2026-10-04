"""Write hashes for this additive repair record and its tested source inputs."""
import hashlib
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
paths = [
    "research/doom/doom_typed_release_backend_v3.py",
    "research/doom/test_doom_typed_release_backend_v3.py",
    "research/doom/map01-v39-release-cleanup-followup-v1/PLAN.md",
    "research/doom/map01-v39-release-cleanup-followup-v1/RUN_COMMANDS.md",
    "research/doom/map01-v39-release-cleanup-followup-v1/RESULT.md",
    "research/doom/map01-v39-release-cleanup-followup-v1/RESULT.json",
    "research/doom/map01-v39-release-cleanup-followup-v1/PARENT_SOURCE_SHA256.txt",
    "research/doom/map01-v39-release-cleanup-followup-v1/audit.py",
    "research/doom/map01-v39-release-cleanup-followup-v1/write_checksums.py",
    "research/doom/map01-v39-release-cleanup-followup-v1/results/RAW_PARENT_RED.txt",
    "research/doom/map01-v39-release-cleanup-followup-v1/results/PARENT_RED_EXIT.txt",
    "research/doom/map01-v39-release-cleanup-followup-v1/results/RAW_BACKEND_TESTS.txt",
    "research/doom/map01-v39-release-cleanup-followup-v1/results/BACKEND_EXIT.txt",
    "research/doom/map01-v39-release-cleanup-followup-v1/results/RAW_OWNER_TESTS.txt",
    "research/doom/map01-v39-release-cleanup-followup-v1/results/OWNER_EXIT.txt",
    "research/doom/map01-v39-release-cleanup-followup-v1/results/RAW_STATIC_CHECKS.txt",
    "research/doom/map01-v39-release-cleanup-followup-v1/results/STATIC_EXIT.txt",
    "research/doom/map01-v39-release-cleanup-followup-v1/results/RAW_AUDIT.txt",
    "research/doom/map01-v39-release-cleanup-followup-v1/results/AUDIT_EXIT.txt",
]
lines = [
    f"{hashlib.sha256((REPO / rel).read_bytes()).hexdigest()}  {rel}"
    for rel in paths
]
(HERE / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {len(lines)} SHA256 entries")
