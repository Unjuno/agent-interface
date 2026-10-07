"""Run the new regression against the exact PR #7378 parent source."""
from pathlib import Path
import shutil
import subprocess
import tempfile


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RESULTS = HERE / "results"
BASE = "fbed929f629dabaa9ae752019d0ee7151d4d2298"

RESULTS.mkdir(exist_ok=True)
baseline = subprocess.run(
    ["git", "show", f"{BASE}:research/doom/doom_typed_release_backend_v3.py"],
    cwd=REPO, check=True, capture_output=True,
).stdout
with tempfile.TemporaryDirectory(prefix="v39-cleanup-baseline-") as temp:
    run_dir = Path(temp)
    (run_dir / "doom_typed_release_backend_v3.py").write_bytes(baseline)
    shutil.copy2(REPO / "research/doom/test_doom_typed_release_backend_v3.py",
                 run_dir / "test_doom_typed_release_backend_v3.py")
    proc = subprocess.run(
        ["python", "test_doom_typed_release_backend_v3.py",
         "Tests.test_cleanup_inside_explicit_release_bracket_is_not_ordinary"],
        cwd=run_dir, capture_output=True, text=True,
    )
raw = proc.stdout + proc.stderr
(RESULTS / "RAW_BASELINE.txt").write_text(raw, encoding="utf-8")
if proc.returncode == 0:
    raise SystemExit("FAIL: baseline unexpectedly passed the cleanup-overlap regression")
(RESULTS / "BASELINE_EXIT.txt").write_text(
    f"expected regression failure; observed exit={proc.returncode}\n", encoding="utf-8")
print(raw, end="")
print(f"EXPECTED_BASELINE_FAILURE exit={proc.returncode}")
