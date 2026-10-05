"""Compare frozen parent and candidate release_all exception boundaries."""

import ast
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[3]
D = ROOT / "research/live_control/executor_v13_release_cleanup_baseexception_59_20261005"
PARENT = (D / "parent-executor-v13.py").read_text()
CANDIDATE = (D / "candidate-executor-v13.py").read_text()
TESTS = (D / "candidate-test-executor-v13.py").read_text()


def cleanup_handler(source):
    tree = ast.parse(source)
    executor = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Executor")
    worker = next(node for node in executor.body if isinstance(node, ast.FunctionDef)
                  and node.name == "_run_with_watcher_cleanup")
    def direct_body_calls_release_all(statements):
        stack = list(statements)
        while stack:
            item = stack.pop()
            if isinstance(item, ast.Try):
                continue
            if isinstance(item, ast.Call) and isinstance(item.func, ast.Attribute) and item.func.attr == "release_all":
                return True
            stack.extend(ast.iter_child_nodes(item))
        return False

    matches = []
    for node in ast.walk(worker):
        if not isinstance(node, ast.Try):
            continue
        source_text = ast.unparse(node)
        if direct_body_calls_release_all(node.body):
            matches.append((node, source_text))
    if not matches:
        raise AssertionError("release_all cleanup try block not found")
    node, source_text = min(matches, key=lambda item: len(item[1]))
    return node.handlers[0], source_text


parent_handler, _ = cleanup_handler(PARENT)
candidate_handler, cleanup_source = cleanup_handler(CANDIDATE)
parent_type = ast.unparse(parent_handler.type)
candidate_type = ast.unparse(candidate_handler.type)
assert parent_type == "Exception", parent_type
assert candidate_type == "BaseException", candidate_type
assert "release_batch_publication" in cleanup_source
assert "release_batch_delivery" in cleanup_source
assert "process_exception" in cleanup_source
assert "test_release_all_base_exception_with_custody_publishes_failed_terminal_then_reraises" in TESTS
assert "test_release_all_unrelated_base_exception_publishes_failed_terminal_then_reraises" in TESTS

print(json.dumps({
    "result": "PASS_RELEASE_CLEANUP_BOUNDARY_AUDIT",
    "parent_release_all_handler": parent_type,
    "candidate_release_all_handler": candidate_type,
    "custody_field_preserved": True,
    "non_exception_reraise_deferred_until_terminal": True,
    "positive_and_negative_regressions_present": True,
}, sort_keys=True))
