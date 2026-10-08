"""Independent explicit-check audit for the A02 construction result."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blob(path):
    rel = path.relative_to(REPO).as_posix()
    return subprocess.check_output(["git", "-C", str(REPO), "rev-parse", f"HEAD:{rel}"], text=True).strip()


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    result = json.loads((HERE / "RESULT.json").read_text())
    require(freeze["main_sha"] == "437db9f8c8e77e3ad38a61c2e6a42f5cdb06fcb2", "wrong frozen main")
    merge_base = subprocess.check_output(["git", "-C", str(REPO), "merge-base", "HEAD", freeze["main_sha"]], text=True).strip()
    require(merge_base == freeze["main_sha"], "frozen main is not the branch's exact base")
    require(result["main_sha"] == freeze["main_sha"], "result/freeze main mismatch")
    require(result["runtime"]["python"].startswith("3.11.9 ") and "Windows" in result["runtime"]["platform"],
            "runtime environment provenance mismatch")
    require(result["disposition"] == "PASS_CANDIDATE_CONTROLLER_RECOVERY", "unexpected result disposition")
    require(result["source_blobs"] == freeze["sources"], "source blob pins differ")
    actual = {name: blob(REPO / name) for name in freeze["sources"]}
    require(actual == freeze["sources"], "checkout does not match frozen sources")
    baseline = result["production_reproduction"]
    require(baseline["result"] == "raises_on_rejection", "production failure not reproduced")
    require(baseline["submit_count"] == 1 and baseline["submitted_expected_sequence"] == 1,
            "production path did not issue exactly the frozen stale submit")
    require(baseline["state_before_any_admission"] == [0, None], "rejection advanced admission state")
    require(baseline["latest_after_production_wait"]["sequence"] == 2,
            "production wait did not consume the newer observation before rejection")
    require(result["recovery"]["fresh_sequence"] == 2 and result["recovery"]["health"] == 86 and
            result["recovery"]["ammo"] == 11 and result["recovery"]["planner_turns"] == 1,
            "candidate turn did not use fresh observation data")
    require(result["recovery"]["post_rejection_submits"] == 0, "candidate resubmitted rejected action")
    require(result["trigger"]["current_main_order"] == ["typed_observation", "observation", "rejected"],
            "current-main event order differs")
    require(result["trigger"]["candidate_also_passed_rejection_before_full_observation"] is True,
            "delayed full observation case failed")
    required_controls = {"other_rejection", "binding_changed", "same_sequence", "invalid_health",
                         "invalid_ammo", "missing_image", "old_capture", "timeout", "process_exit"}
    require(set(result["negative_controls"]) == required_controls, "negative-control set incomplete")
    require(set(result["negative_controls"].values()) == {"refused"}, "negative control admitted")
    manifest = {}
    for line in (HERE / "SHA256SUMS.txt").read_text().splitlines():
        digest, name = line.split("  ", 1)
        require(name not in manifest, "duplicate manifest path")
        manifest[name] = digest
        require(sha(HERE / name) == digest, f"hash mismatch: {name}")
    require(set(manifest) == {"FREEZE.json", "README.md", "RESULT.json", "run.py",
                              "raw-normal.stdout.txt", "raw-optimized.stdout.txt",
                              "normal.exit", "optimized.exit", "verify.py"}, "manifest path set mismatch")
    require((HERE / "normal.exit").read_text().strip() == "0", "normal run failed")
    require((HERE / "optimized.exit").read_text().strip() == "0", "optimized run failed")
    require(b"PASS_CANDIDATE_CONTROLLER_RECOVERY" in (HERE / "raw-normal.stdout.txt").read_bytes(),
            "normal raw does not show pass")
    require(b"PASS_CANDIDATE_CONTROLLER_RECOVERY" in (HERE / "raw-optimized.stdout.txt").read_bytes(),
            "optimized raw does not show pass")
    print(f"PASS: explicit source, production-branch, candidate, controls, and {len(manifest)} artifact checks")


if __name__ == "__main__":
    main()
