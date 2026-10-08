"""Run PR #8643's new controller regression tests against exact current main."""
import ast
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


def source_bytes(path, identity):
    ref = FREEZE[identity["ref"]]
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", f"{ref}:{path}"], text=True
    ).strip()
    data = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
    if blob != identity["blob"] or hashlib.sha256(data).hexdigest() != identity["sha256"]:
        raise ValueError(f"frozen source mismatch: {path}")
    return data


def ref_bytes(ref, path):
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", f"{ref}:{path}"], text=True
    ).strip()
    data = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
    return blob, data


def import_names(source):
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".", 1)[0]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module.split(".", 1)[0]


def extract_main_dependencies(overlay):
    main = FREEZE["main_commit"]
    names = subprocess.check_output(
        ["git", "-C", str(REPO), "ls-tree", "-r", "--name-only", main,
         "--", "research/doom", "research/live_control"], text=True
    ).splitlines()
    module_paths = {}
    for prefix in ("research/doom", "research/live_control"):
        for path in names:
            if path.endswith(".py") and Path(path).parent.as_posix() == prefix:
                module_paths.setdefault(Path(path).stem, path)

    replaced = set(FREEZE["overlay_paths"])
    controller_path = "research/doom/map01_overlap_controller_v39.py"
    pending = [controller_path]
    visited = set()
    sources = []
    while pending:
        path = pending.pop()
        if path in visited:
            continue
        visited.add(path)
        blob, data = ref_bytes(main, path)
        for name in import_names(data):
            dependency = module_paths.get(name)
            if dependency and dependency not in visited and dependency not in replaced:
                pending.append(dependency)
        if path in replaced:
            continue
        target = overlay / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        sources.append({"path": path, "blob": blob,
                        "sha256": hashlib.sha256(data).hexdigest()})
    return sorted(sources, key=lambda row: row["path"])


def run(overlay, optimized):
    doom = overlay / "research" / "doom"
    live = overlay / "research" / "live_control"
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(str(path) for path in (doom, live))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [sys.executable, "-B"]
    if optimized:
        cmd.append("-O")
    cmd.extend(["-m", "unittest", "discover", "-s", str(doom),
                "-p", "test_map01_overlap_controller_v39.py", "-v"])
    result = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True)
    return {"exit_code": result.returncode, "stdout": result.stdout,
            "stderr": result.stderr}


def main():
    with tempfile.TemporaryDirectory(prefix="v39-main-a06-control-") as temp:
        overlay = Path(temp)
        dependencies = extract_main_dependencies(overlay)
        for path, identity in FREEZE["overlay_paths"].items():
            target = overlay / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source_bytes(path, identity))
        results = {mode: run(overlay, optimized=(mode == "optimized"))
                   for mode in ("normal", "optimized")}

    for mode, result in results.items():
        (ROOT / f"{mode}.stdout.txt").write_text(result["stdout"], encoding="utf-8")
        (ROOT / f"{mode}.stderr.txt").write_text(result["stderr"], encoding="utf-8")
    summary = {
        "schema": "v39-main-vs-pr8643-regression-control-result-v1",
        "main_commit": FREEZE["main_commit"],
        "candidate_commit": FREEZE["candidate_commit"],
        "dependency_base_commit": FREEZE["dependency_base_commit"],
        "overlay_paths": sorted(FREEZE["overlay_paths"]),
        "dependency_sources": dependencies,
        "runs": {mode: {"exit_code": result["exit_code"]}
                 for mode, result in results.items()},
        "expected_discriminating_failures": [
            "test_stale_partial_action_does_not_reuse_discarded_remaining_cover",
            "test_initial_cover_invalidation_cancels_before_planner_and_requires_empty_release",
        ],
        "decision": "DISCRIMINATING_BASELINE" if all(
            result["exit_code"] != 0 for result in results.values()) else "UNEXPECTED",
        "scope": "Candidate PR #8643's nine controller tests against the current-main controller and its statically import-reachable direct research/doom and research/live_control Python modules extracted from the pinned main commit, normal and optimized Python. CPU-only test fixtures; no Doom, model, GUI, OS input, or live allocation.",
    }
    (ROOT / "RESULT.json").write_text(json.dumps(summary, indent=2) + "\n",
                                      encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if summary["decision"] == "DISCRIMINATING_BASELINE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
