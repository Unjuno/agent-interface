import hashlib
import json
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent
repo = root.parents[3]
freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8-sig"))
run = json.loads((root / "RUN.json").read_text(encoding="utf-8-sig"))
for relative, expected in freeze["source_sha256"].items():
    actual = hashlib.sha256((repo / relative).read_bytes()).hexdigest().upper()
    assert actual == expected.upper(), (relative, expected, actual)
baseline = root / "baseline/doom_controller_failure_cleanup_v1.py"
blob = subprocess.check_output(["git", "-C", str(repo), "hash-object", str(baseline)], text=True).strip()
assert blob == freeze["baseline_helper_git_blob_sha1"]
assert run["baseline"]["exit_code"] == 1
assert "FAILED (failures=1)" in (root / "BASELINE_REGRESSION_OUTPUT.txt").read_text(encoding="utf-8-sig")
assert run["candidate"]["windows_exit"] == run["candidate"]["wslc_exit"] == 0
windows = (root / "WINDOWS_TEST_OUTPUT.txt").read_text(encoding="utf-8-sig")
wslc = (root / "WSLC_TEST_OUTPUT.txt").read_text(encoding="utf-8-sig")
assert "Ran 33 tests" in windows and "OK (skipped=2)" in windows
assert "Ran 33 tests" in wslc and "OK" in wslc and "skipped" not in wslc
assert "cgroup is not mounted" in wslc
static = json.loads((root / "STATIC_CHECKS.json").read_text(encoding="utf-8-sig"))
assert static["compile_exit"] == static["diff_check_exit"] == 0
print("PASS: exact frozen source hashes, baseline blob, expected red, Windows 33/2-skip, WSLc 33/no-skip, and cgroup warning verified")
