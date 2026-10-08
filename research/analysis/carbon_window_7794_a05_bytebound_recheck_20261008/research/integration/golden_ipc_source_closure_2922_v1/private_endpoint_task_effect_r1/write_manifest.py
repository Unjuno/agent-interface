"""Create a deterministic SHA256 manifest for the retained task-effect bundle."""
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = sorted(
    [p for p in (HERE / "raw").rglob("*") if p.is_file()]
    + [HERE / name for name in
       ("REPORT.md", "run_task_effect.py", "audit.py", "test_audit.py", "write_manifest.py",
        "session_cli_chromium_task_effect_probe.py")]
)
lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(HERE)}"
         for path in FILES]
(HERE / "SHA256SUMS").write_text("\n".join(lines) + "\n")
print(f"wrote {len(lines)} hashes")
