"""Dependency-free check of PR #7843's selector on its current-main merge tree."""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path


MAIN_REF = "origin/main"
PR_REF = "origin/pr/7843"
CONTROLLER = "research/doom/map01_overlap_controller_v39.py"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def main() -> None:
    merge_tree = git("merge-tree", "--write-tree", MAIN_REF, PR_REF)
    source = subprocess.check_output(
        ["git", "show", f"{merge_tree}:{CONTROLLER}"], text=True
    )
    module = ast.parse(source, filename=CONTROLLER)
    selector = next(
        node for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "session_command"
    )
    parser = next(
        node for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "parser"
        and node.func.attr == "add_argument"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "--measurement-session"
    )
    if not any(
        keyword.arg == "action"
        and isinstance(keyword.value, ast.Constant)
        and keyword.value.value == "store_true"
        for keyword in parser.keywords
    ):
        raise AssertionError("measurement selector is not an opt-in boolean flag")

    namespace = {"sys": sys, "HERE": Path("research/doom")}
    exec(compile(ast.Module(body=[selector], type_ignores=[]), CONTROLLER, "exec"), namespace)
    args = Namespace(seed=990605, load_fixture_manifest=Path("fixture.json"))
    default = namespace["session_command"](args, Path("runtime"))
    if Path(default[1]).name != "session_map01_v12.py":
        raise AssertionError(f"default did not preserve V12: {default!r}")
    args.measurement_session = True
    measured = namespace["session_command"](args, Path("runtime"))
    if Path(measured[1]).name != "session_map01_v15.py":
        raise AssertionError(f"opt-in did not select V15: {measured!r}")
    if measured[2:] != default[2:]:
        raise AssertionError("selection changed arguments beyond the session path")

    result = {
        "schema": "map01-v39-pr7843-current-main-selector-check-v1",
        "decision": "PASS_SELECTOR_ON_CURRENT_MAIN_MERGE_TREE",
        "main_ref": MAIN_REF,
        "main_commit": git("rev-parse", MAIN_REF),
        "pr_ref": PR_REF,
        "pr_head": git("rev-parse", PR_REF),
        "merge_tree": merge_tree,
        "controller_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "parser_boolean_opt_in": True,
        "default_session": Path(default[1]).name,
        "opt_in_session": Path(measured[1]).name,
        "remaining_child_arguments_identical": True,
        "scope": "selector and command construction only; no session process or game started",
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
