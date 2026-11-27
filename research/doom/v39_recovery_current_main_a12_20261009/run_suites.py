"""Run the latest PR #8643's four directly affected suites from an exact overlay."""
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


def git_blob(path):
    ref = FREEZE["source_commit"]
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", f"{ref}:{path}"], text=True
    ).strip()
    data = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
    return blob, data


def imports_from(data):
    for node in ast.walk(ast.parse(data)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".", 1)[0]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module.split(".", 1)[0]


def build_overlay(overlay):
    ref = FREEZE["source_commit"]
    names = subprocess.check_output(
        ["git", "-C", str(REPO), "ls-tree", "-r", "--name-only", ref,
         "--", "research/doom", "research/live_control"], text=True
    ).splitlines()
    modules = {}
    for prefix in ("research/doom", "research/live_control"):
        for path in names:
            if path.endswith(".py") and Path(path).parent.as_posix() == prefix:
                modules.setdefault(Path(path).stem, path)

    pending = [row["path"] for row in FREEZE["suites"]]
    sources = {}
    while pending:
        item = pending.pop()
        if item in sources:
            continue
        if item.startswith("research/") and item.endswith(".py"):
            path = item
        else:
            path = modules.get(item)
            if path is None:
                continue
        blob, data = git_blob(path)
        sources[path] = {"blob": blob, "sha256": hashlib.sha256(data).hexdigest()}
        target = overlay / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        pending.extend(imports_from(data))
    return sources


def run_one(overlay, suite, optimized):
    test_path = suite["path"]
    start = overlay / Path(test_path).parent
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((str(overlay / "research" / "doom"),
                                         str(overlay / "research" / "live_control")))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [sys.executable, "-B"] + (["-O"] if optimized else [])
    cmd.extend(["-m", "unittest", "discover", "-s", str(start),
                "-p", Path(test_path).name, "-v"])
    result = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True)
    return {"exit_code": result.returncode, "stdout": result.stdout,
            "stderr": result.stderr}


def main():
    with tempfile.TemporaryDirectory(prefix="v39-pr8643-a09-") as temp:
        overlay = Path(temp)
        sources = build_overlay(overlay)
        results = {suite["key"]: {
            mode: run_one(overlay, suite, optimized=(mode == "optimized"))
            for mode in ("normal", "optimized")
        } for suite in FREEZE["suites"]}

    summary_runs = {}
    all_pass = True
    for suite in FREEZE["suites"]:
        key = suite["key"]
        summary_runs[key] = {}
        for mode, result in results[key].items():
            (ROOT / f"{key}.{mode}.stdout.txt").write_text(
                result["stdout"], encoding="utf-8")
            (ROOT / f"{key}.{mode}.stderr.txt").write_text(
                result["stderr"], encoding="utf-8")
            summary_runs[key][mode] = {"exit_code": result["exit_code"]}
            all_pass &= result["exit_code"] == 0 and (
                f"Ran {suite['tests']} tests" in result["stderr"] and
                result["stderr"].rstrip().endswith("OK"))

    summary = {
        "schema": "v39-postmerge-main-affected-suite-result-v1",
        "source_commit": FREEZE["source_commit"],
        "dependency_base_commit": FREEZE["dependency_base_commit"],
        "sources": sources,
        "suites": FREEZE["suites"],
        "runs": summary_runs,
        "decision": "PASS" if all_pass else "FAIL",
        "scope": "Four exact affected suites run from a temporary overlay of candidate source and static imports, normal and optimized Python. Deterministic CPU fixtures only; no Doom, model, GUI, OS input, live threat, or live allocation.",
    }
    (ROOT / "RESULT.json").write_text(json.dumps(summary, indent=2) + "\n",
                                      encoding="utf-8")
    print(json.dumps({"source_commit": summary["source_commit"],
                      "suite_count": len(summary["suites"]),
                      "runs": summary["runs"], "decision": summary["decision"]},
                     indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
