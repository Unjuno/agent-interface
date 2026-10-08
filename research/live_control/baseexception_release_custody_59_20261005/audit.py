"""Independent source-shape audit for the ExecutorV13 custody regression."""

import ast
import json
import pathlib
import subprocess


ROOT = pathlib.Path(__file__).resolve().parents[3]
REL = "research/live_control/executor_v13.py"
PARENT = (ROOT / "research/live_control/baseexception_release_custody_59_20261005/parent-commit.txt").read_text().strip()


def source_at(revision):
    if revision == "candidate":
        return (ROOT / REL).read_text()
    return subprocess.run(
        ["git", "show", f"{PARENT}:{REL}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def worker_handler_names(source):
    tree = ast.parse(source)
    executor = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Executor")
    worker = next(
        node for node in executor.body
        if isinstance(node, ast.FunctionDef) and node.name == "_run_with_watcher_cleanup"
    )
    names = []
    for node in ast.walk(worker):
        if isinstance(node, ast.ExceptHandler):
            names.append(ast.unparse(node.type) if node.type is not None else "bare")
    return worker, names


parent_worker, parent_handlers = worker_handler_names(source_at("parent"))
candidate_source = source_at("candidate")
candidate_worker, candidate_handlers = worker_handler_names(candidate_source)
assert "Exception" in parent_handlers and "BaseException" not in parent_handlers, parent_handlers
assert "BaseException" in candidate_handlers, candidate_handlers
assert "release_batch_delivery" in candidate_source
assert "release_batch_publication" in candidate_source
assert any(isinstance(node, ast.Raise) for node in ast.walk(candidate_worker))

print(json.dumps({
    "result": "PASS_SOURCE_SHAPE",
    "parent_handlers": parent_handlers,
    "candidate_handlers": candidate_handlers,
    "custody_field_preserved": True,
    "explicit_reraise_present": True,
}, sort_keys=True))
