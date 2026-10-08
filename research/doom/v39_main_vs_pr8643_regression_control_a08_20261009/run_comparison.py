"""Compare current main and latest PR #8643 against the candidate controller tests."""
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


def git_blob(ref, path):
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", f"{ref}:{path}"], text=True
    ).strip()
    data = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
    return blob, data


def imported_modules(source):
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".", 1)[0]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module.split(".", 1)[0]


def source_tree(ref):
    names = subprocess.check_output(
        ["git", "-C", str(REPO), "ls-tree", "-r", "--name-only", ref,
         "--", "research/doom", "research/live_control"], text=True
    ).splitlines()
    modules = {}
    for prefix in ("research/doom", "research/live_control"):
        for path in names:
            if path.endswith(".py") and Path(path).parent.as_posix() == prefix:
                modules.setdefault(Path(path).stem, path)
    return modules


def build_overlay(temp, controller_ref, candidate_ref):
    controller_path = FREEZE["controller_path"]
    test_path = FREEZE["test_path"]
    main_modules = source_tree(controller_ref)
    pending = [controller_path, test_path]
    sources = {}
    replacements = {controller_path: controller_ref, test_path: candidate_ref}

    while pending:
        item = pending.pop()
        if item.endswith(".py") and item.startswith("research/"):
            path = item
        else:
            path = main_modules.get(item)
            if path is None:
                continue
        if path in sources:
            continue
        ref = replacements.get(path, controller_ref)
        blob, data = git_blob(ref, path)
        sources[path] = {"ref": ref, "blob": blob,
                         "sha256": hashlib.sha256(data).hexdigest()}
        if path != test_path:
            pending.extend(imported_modules(data))

    overlay = Path(temp)
    for path, identity in sources.items():
        _, data = git_blob(identity["ref"], path)
        target = overlay / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return sources


def run(overlay, optimized):
    doom = overlay / "research" / "doom"
    live = overlay / "research" / "live_control"
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((str(doom), str(live)))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [sys.executable, "-B"] + (["-O"] if optimized else [])
    cmd.extend(["-m", "unittest", "discover", "-s", str(doom),
                "-p", Path(FREEZE["test_path"]).name, "-v"])
    result = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True)
    return {"exit_code": result.returncode, "stdout": result.stdout,
            "stderr": result.stderr}


def main():
    results = {}
    source_records = {}
    for variant, ref in (("main", FREEZE["main_commit"]),
                         ("candidate", FREEZE["candidate_commit"])):
        with tempfile.TemporaryDirectory(prefix=f"v39-a07-{variant}-") as temp:
            source_records[variant] = build_overlay(
                temp, controller_ref=ref,
                candidate_ref=FREEZE["candidate_commit"])
            results[variant] = {
                mode: run(Path(temp), optimized=(mode == "optimized"))
                for mode in ("normal", "optimized")
            }
    for variant, modes in results.items():
        for mode, result in modes.items():
            (ROOT / f"{variant}.{mode}.stdout.txt").write_text(
                result["stdout"], encoding="utf-8")
            (ROOT / f"{variant}.{mode}.stderr.txt").write_text(
                result["stderr"], encoding="utf-8")

    main_target_failures = all(
        all(name in results["main"][mode]["stderr"]
            for name in FREEZE["expected_main_regressions"])
        and f"Ran {FREEZE['test_count']} tests" in results["main"][mode]["stderr"]
        for mode in ("normal", "optimized"))
    candidate_passes = all(
        results["candidate"][mode]["exit_code"] == 0 and
        f"Ran {FREEZE['test_count']} tests" in results["candidate"][mode]["stderr"] and
        results["candidate"][mode]["stderr"].rstrip().endswith("OK")
        for mode in ("normal", "optimized"))
    summary = {
        "schema": "v39-main-vs-pr8643-regression-control-result-v1",
        "main_commit": FREEZE["main_commit"],
        "candidate_commit": FREEZE["candidate_commit"],
        "dependency_base_commit": FREEZE["dependency_base_commit"],
        "test_path": FREEZE["test_path"],
        "test_count": FREEZE["test_count"],
        "sources": source_records,
        "runs": {variant: {mode: {"exit_code": result["exit_code"]}
                           for mode, result in modes.items()}
                 for variant, modes in results.items()},
        "expected_main_regressions": FREEZE["expected_main_regressions"],
        "decision": "DISCRIMINATING_BASELINE" if main_target_failures and candidate_passes
                    else "UNEXPECTED",
        "scope": f"The exact {FREEZE['test_count']}-test controller suite from PR #8643 head {FREEZE['candidate_commit'][:7]} runs against current main {FREEZE['main_commit'][:7]} and candidate controller/dependencies, normal and optimized Python. Each overlay contains only the test/controller import closure. CPU-only fixtures; no Doom, model, GUI, OS input, or live allocation.",
    }
    (ROOT / "RESULT.json").write_text(json.dumps(summary, indent=2) + "\n",
                                      encoding="utf-8")
    print(json.dumps({key: summary[key] for key in
                      ("main_commit", "candidate_commit", "test_count", "runs", "decision")},
                     indent=2))
    return 0 if summary["decision"] == "DISCRIMINATING_BASELINE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
