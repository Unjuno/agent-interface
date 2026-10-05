"""Mechanical audit for the Windows pipe scorer polling evidence package."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))

def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\\0".encode("ascii") + data).hexdigest()

for rel, expected in freeze["candidate_blobs"].items():
    actual = git_blob_sha(ROOT / rel)
    if actual != expected:
        raise SystemExit(f"FAIL blob {rel}: expected {expected}, got {actual}")

source = (ROOT / "research/doom/main_thread_scorer_polling_v1.py").read_text(encoding="utf-8")
tests = (ROOT / "research/doom/test_main_thread_scorer_polling_v1.py").read_text(encoding="utf-8")
required_source = (
    'if os.name == "nt":',
    "_wait_windows_readable(fd, timeout_s)",
    "PeekNamedPipe",
    "WaitForSingleObject",
    "ready, _, _ = select.select([fd], [], [], timeout_s)",
    "ERROR_BROKEN_PIPE",
)
required_tests = (
    "test_windows_pipe_delayed_command_stays_on_owner_thread",
    "test_windows_pipe_eof_is_readable_after_writer_closes",
    'self.assertEqual(seen, ["PING", "STOP"])',
    "self.assertTrue(stats.eof)",
)
for needle in required_source:
    if needle not in source:
        raise SystemExit(f"FAIL missing source contract: {needle}")
for needle in required_tests:
    if needle not in tests:
        raise SystemExit(f"FAIL missing test contract: {needle}")

print("PASS: candidate Git blob identities and Windows/non-Windows polling contracts match FREEZE.json")
