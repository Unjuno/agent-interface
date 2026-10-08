"""Read-only publication verification. Never runs the consumed measurement."""
import json, subprocess, sys, tempfile
from pathlib import Path
from restore import restore

ROOT = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix="incfold-review-") as d:
    out = Path(d) / "evidence"
    n = restore(ROOT, out)
    study = out / "research/analysis/incremental_focus_fold_z7r2_v1"
    p = subprocess.run([sys.executable, "-S", "-B", str(study / "verify.py")],
                       cwd=study, capture_output=True, text=True, timeout=30)
    if p.returncode or p.stderr:
        raise SystemExit(f"saved-data verifier failed: {p.returncode}: {p.stderr}")
    result = json.loads(p.stdout)
    if result.get("status") != "PASS_READONLY_RECONSTRUCTION":
        raise SystemExit("unexpected saved-data status")
    result.update(files_restored=n, scientific_actor_runs=0)
    print(json.dumps(result, sort_keys=True))