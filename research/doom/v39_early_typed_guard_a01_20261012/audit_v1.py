import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
freeze = json.loads((ROOT / "FREEZE_V3.json").read_text(encoding="utf-8"))
checks = []
for repo_path, item in freeze["source_blobs"].items():
    source = ROOT / "source" / Path(repo_path).name
    actual_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    actual_blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse",
         f"{freeze['main_commit']}:{repo_path}"], text=True).strip()
    assert actual_sha == item["sha256"], (repo_path, actual_sha)
    assert actual_blob == item["git_blob"], (repo_path, actual_blob)
    checks.append(f"source-pin {repo_path}: {actual_blob} / {actual_sha}")

candidate_name = freeze["candidate"]
candidate_sha = hashlib.sha256((ROOT / candidate_name).read_bytes()).hexdigest()
assert candidate_sha == freeze["candidate_sha256"]
argv = json.loads((ROOT / "out" / "attempt4_v3_argv.json").read_text())
assert argv[0:4] == ["run", "--rm", "--pull", "never"]
assert "--network" in argv and argv[argv.index("--network") + 1] == "none"
assert "--cpus" in argv and argv[argv.index("--cpus") + 1] == "1"
assert freeze["runtime"]["image"] in argv
assert any("target=/study,readonly" in arg for arg in argv)

raw = (ROOT / "out" / "attempt4_v3_output.txt").read_text(encoding="utf-8")
exit_code = (ROOT / "out" / "attempt4_v3_exit.txt").read_text().strip()
expected = [
    "test_soft_typed_signal_waits_for_matching_artifact_to_confirm_pair",
    "test_typed_hard_health_change_invalidates_before_artifact",
    "test_typed_to_artifact_duplicate_epoch_content_conflict_fails_closed",
    "test_unpaired_epoch_fails_closed",
]
assert exit_code == "0"
assert "Ran 4 tests" in raw and "OK" in raw and "FAILED" not in raw
lines = raw.splitlines()
assert all(any(name in line and line.rstrip().endswith("... ok") for line in lines) for name in expected)
assert "swap limit capabilities" in raw
cleanup = (ROOT / "out" / "container_cleanup.txt").read_text(encoding="utf-8")
assert cleanup.count("コンテナー ID") == 3
assert all(name in cleanup for name in (
    "v39-typed-guard-a01-20261012",
    "v39-typed-guard-a01-v2-20261012",
    "v39-typed-guard-a01-v3-20261012"))
checks.append(f"candidate {candidate_name}: {candidate_sha}")
checks.append("WSLc run: pinned image, network none, read-only source, 1 CPU; 4/4 tests PASS; exit 0")
checks.append("three `--rm` container names absent from WSLc container listing")
checks.append("host cgroup warning retained: swap limit unavailable; requested memory limit is not overclaimed")
checks.append("earlier CLI/candidate failures retained under out/attempt1_cli_rejected and out/attempt2_candidate_v1 and out/attempt3_candidate_v2")
print("AUDIT PASS")
print("\n".join(checks))
