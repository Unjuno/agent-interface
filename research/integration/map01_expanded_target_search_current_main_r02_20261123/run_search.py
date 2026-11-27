from __future__ import annotations

from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
import platform
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parent
conditions = json.loads((ROOT / "conditions.json").read_text(encoding="utf-8"))
source_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
if conditions.get("source_sha256") != source_sha256:
    raise SystemExit("frozen source hash mismatch")
started = datetime.now(timezone.utc)
monotonic_start = time.monotonic()
existing = [root for root in conditions["roots"] if Path(root).is_dir()]
missing = [root for root in conditions["roots"] if not Path(root).is_dir()]
globs: list[str] = []
for pattern in conditions["filename_globs"]:
    globs.extend(["-g", pattern])
command = ["rg", *conditions["rg_args"], *globs, *existing]
rg_version = subprocess.run(["rg", "--version"], capture_output=True, check=True).stdout.decode("utf-8", errors="replace").splitlines()[0]
timed_out = False
try:
    completed = subprocess.run(
        command,
        capture_output=True,
        timeout=conditions["timeout_seconds"],
        check=False,
    )
    stdout, stderr, exit_code = completed.stdout, completed.stderr, completed.returncode
except subprocess.TimeoutExpired as error:
    timed_out = True
    stdout = error.stdout or b""
    stderr = error.stderr or b""
    exit_code = 124
(ROOT / "raw.stdout.bin").write_bytes(stdout)
(ROOT / "raw.stderr.bin").write_bytes(stderr)
finished = datetime.now(timezone.utc)
result = {
    "run_id": conditions["run_id"],
    "frozen_main_sha": conditions["frozen_main_sha"],
    "source_sha256": source_sha256,
    "python_version": sys.version,
    "platform": platform.platform(),
    "rg_version": rg_version,
    "started_utc": started.isoformat().replace("+00:00", "Z"),
    "finished_utc": finished.isoformat().replace("+00:00", "Z"),
    "elapsed_seconds": round(time.monotonic() - monotonic_start, 6),
    "timeout_seconds": conditions["timeout_seconds"],
    "timed_out": timed_out,
    "exit_code": exit_code,
    "existing_roots": existing,
    "missing_roots": missing,
    "command": command,
    "stdout_bytes": len(stdout),
    "stderr_bytes": len(stderr),
    "candidate_paths": stdout.decode("utf-8", errors="replace").splitlines(),
    "scope": "filename discovery only; no launch/input/install/download",
}
(ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
disposition = (
    "STOP_TIMEOUT_INCOMPLETE" if timed_out else
    "SEARCH_ERROR_INCOMPLETE" if exit_code not in (0, 1) else
    "CANDIDATES_FOUND_REQUIRES_SEPARATE_OWNERSHIP_AND_HASH_CHECK" if result["candidate_paths"] else
    "NO_CANDIDATE_IN_FROZEN_ROOTS"
)
summary = [
    "# MAP01 expanded local target search R02",
    "",
    f"Disposition: **{disposition}**.",
    "",
    f"Frozen source: `{conditions['frozen_main_sha']}`. The search ran once on Windows with `{len(existing)}` existing roots and `{len(missing)}` absent roots; elapsed {result['elapsed_seconds']} seconds; exit {exit_code}; timeout={timed_out}.",
    "",
    f"Matching paths: {len(result['candidate_paths'])}.",
    *([f"- `{path}`" for path in result["candidate_paths"]] or ["No matching candidate path was returned."]),
    "",
    "This is filename discovery only. A match still requires ownership, source, size/hash, and intended IWAD/map verification before any launch. No application was launched, no input was sent, and nothing was installed or downloaded.",
    "A negative result applies only to the frozen roots and filename patterns; it does not establish absence from the full disk or another account.",
    "",
    "Raw stdout/stderr, exact conditions, source hash, and the result audit are retained in this packet.",
]
(ROOT / "RESULT.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
manifest_names = [
    "CONDITIONS.md", "conditions.json", "run_search.py", "result.json",
    "raw.stdout.bin", "raw.stderr.bin", "RESULT.md"
]
(ROOT / "SHA256SUMS.txt").write_text("".join(
    f"{hashlib.sha256((ROOT / name).read_bytes()).hexdigest()}  {name}\n"
    for name in manifest_names
), encoding="ascii")
print(json.dumps(result, indent=2))
