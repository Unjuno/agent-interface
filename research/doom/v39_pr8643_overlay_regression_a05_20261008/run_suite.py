"""Run the frozen PR #8643 pending-observation suite through a small source overlay."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))


def frozen_blob(path, expected):
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse",
         f"{FREEZE['candidate_commit']}:{path}"], text=True).strip()
    data = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
    if blob != expected["blob"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
        raise ValueError(f"frozen overlay mismatch: {path}")
    return data


def run_command(overlay, optimized, pattern):
    package_doom = overlay / "research" / "doom"
    package_live = overlay / "research" / "live_control"
    env = os.environ.copy()
    paths = [package_live, package_doom,
             REPO / "research" / "live_control",
             REPO / "research" / "doom"]
    env["PYTHONPATH"] = os.pathsep.join(str(path) for path in paths)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [sys.executable, "-B"]
    if optimized:
        cmd.append("-O")
    cmd.extend(["-m", "unittest", "discover", "-s", str(package_doom),
                "-p", pattern, "-v"])
    result = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True)
    recorded_command = [arg.replace(str(overlay), "<temporary-overlay>") for arg in cmd]
    return {"command": recorded_command, "exit_code": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def verify_dependency_tree():
    changed = subprocess.check_output(
        ["git", "-C", str(REPO), "diff", "--name-only",
         FREEZE["dependency_base_commit"]], text=True).splitlines()
    status = subprocess.check_output(
        ["git", "-C", str(REPO), "status", "--porcelain", "--untracked-files=all"],
        text=True).splitlines()
    paths = list(changed)
    paths.extend(row[3:] for row in status if len(row) > 3)
    unexpected = [path for path in paths if not any(
        path.replace("\\", "/").startswith(prefix)
        for prefix in FREEZE["allowed_output_prefixes"])]
    if unexpected:
        raise RuntimeError(f"dependency checkout differs outside evidence paths: {unexpected[:8]}")


def main():
    verify_dependency_tree()
    with tempfile.TemporaryDirectory(prefix="v39-a05-overlay-", dir=ROOT) as temp:
        overlay = Path(temp)
        for path, expected in FREEZE["overlay_paths"].items():
            target = overlay / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(frozen_blob(path, expected))
        runs = {}
        for pattern in ("test_map01_v39_pending_observation_drain.py",
                        "test_map01_overlap_controller_v39.py"):
            runs[pattern] = {
                "normal": run_command(overlay, optimized=False, pattern=pattern),
                "optimized": run_command(overlay, optimized=True, pattern=pattern),
            }

    result = {
        "schema": "v39-pr8643-overlay-regression-result-v1",
        "candidate_commit": FREEZE["candidate_commit"],
        "dependency_base_commit": FREEZE["dependency_base_commit"],
        "dependency_tree_unchanged_outside_evidence": True,
        "overlay_paths": sorted(FREEZE["overlay_paths"]),
        "runs": {pattern: {mode: {key: value for key, value in run.items()
                                  if key not in ("stdout", "stderr")}
                           for mode, run in paired.items()}
                 for pattern, paired in runs.items()},
        "decision": "PASS" if all(run["exit_code"] == 0
                                   for paired in runs.values()
                                   for run in paired.values()) else "FAIL",
        "scope": "Exact frozen PR files overlaid onto the retained dependency base, running the pending-observation drain and overlap-controller unittest suites in normal and optimized Python. No full worktree, App Server, model, game, GUI, OS input, or live task.",
    }
    for pattern, paired in runs.items():
        stem = pattern.removesuffix(".py")
        for mode, run in paired.items():
            (ROOT / f"{stem}.{mode}.stdout.txt").write_text(run["stdout"], encoding="utf-8")
            (ROOT / f"{stem}.{mode}.stderr.txt").write_text(run["stderr"], encoding="utf-8")
    (ROOT / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n",
                                      encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
