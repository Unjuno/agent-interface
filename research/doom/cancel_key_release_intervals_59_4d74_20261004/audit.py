"""Independent consistency audit for the retained construction outputs."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
freeze = json.loads((ROOT / "FREEZE.json").read_text())
checks = {}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

candidate_root = ROOT.parents[2]
checks["candidate_source_sha256"] = (
    sha(candidate_root / freeze["candidate_source_path"])
    == freeze["candidate_source_sha256"]
)
checks["candidate_test_sha256"] = (
    sha(candidate_root / freeze["candidate_test_path"])
    == freeze["candidate_test_sha256"]
)
checks["baseline_source_sha256"] = (
    sha(ROOT / "baseline" / "input_owner_v12.py")
    == freeze["baseline_source_sha256"]
)
stop = (ROOT / "baseline" / "out-01.stderr.txt").read_text()
checks["initial_staging_stop"] = (
    (ROOT / "baseline" / "out-01.exit.txt").read_text().strip() == "1"
    and "ModuleNotFoundError: No module named 'lease'" in stop
)
baseline = (ROOT / "baseline" / "out-02.stderr.txt").read_text()
checks["baseline_missing_interval_failure"] = (
    (ROOT / "baseline" / "out-02.exit.txt").read_text().strip() == "1"
    and "KeyError: 'key_release_intervals_ns'" in baseline
)
candidate_out = (ROOT / "candidate.stdout.txt").read_text()
candidate_err = (ROOT / "candidate.stderr.txt").read_text()
checks["candidate_16_tests_pass"] = (
    (ROOT / "candidate.exit.txt").read_text().strip() == "0"
    and "Ran 16 tests" in candidate_err
    and "OK" in candidate_err
)
manifest = (ROOT / "FILES.sha256").read_text().splitlines()
manifest_results = []
for line in manifest:
    expected, rel = line.split("  ", 1)
    manifest_results.append(sha(ROOT / rel) == expected)
checks["manifest_members"] = bool(manifest_results) and all(manifest_results)
checks["manifest_member_count"] = len(manifest_results)
result = {"schema": "cancel-key-release-intervals-audit-v1", "checks": checks,
          "pass": all(value for key, value in checks.items()
                       if key != "manifest_member_count")}
print(json.dumps(result, indent=2))
if not result["pass"]:
    raise SystemExit(1)
