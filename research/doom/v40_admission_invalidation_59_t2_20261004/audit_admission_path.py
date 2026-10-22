"""Read-only AST audit for V40's cover-admission invalidation path."""
import ast
import hashlib
import json
from pathlib import Path
import sys


def function(tree, name):
    return next((node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name == name), None)


def calls(node, name):
    return [part for part in ast.walk(node)
            if isinstance(part, ast.Call) and isinstance(part.func, ast.Name)
            and part.func.id == name]


def compares_field(node, variable, field, value):
    for part in ast.walk(node):
        if not isinstance(part, ast.Compare):
            continue
        if (isinstance(part.left, ast.Subscript) and
                isinstance(part.left.value, ast.Name) and
                part.left.value.id == variable and
                isinstance(part.left.slice, ast.Constant) and
                part.left.slice.value == field and
                any(isinstance(item, ast.Constant) and item.value == value
                    for item in part.comparators)):
            return True
    return False


def audit(source_bytes):
    tree = ast.parse(source_bytes.decode("utf-8"))
    accept_wait = function(tree, "wait_for_cover_acceptance")
    unplanned_cancel = function(tree, "cancel_unplanned_invalidated_cover")
    main = function(tree, "main")
    loop = next(node for node in ast.walk(main)
                if isinstance(node, ast.For) and isinstance(node.target, ast.Name)
                and node.target.id == "index")

    wait_forwards_monitor = accept_wait is not None and any(
        keyword.arg == "observation_monitor" and
        isinstance(keyword.value, ast.Name) and
        keyword.value.id == "observation_monitor"
        for call in calls(accept_wait, "wait") for keyword in call.keywords)

    nested_submit = next(node for node in ast.walk(loop)
        if isinstance(node, ast.FunctionDef) and node.name == "submit_cover")
    submit_passes_validity_monitor = nested_submit is not None and any(
        len(call.args) >= 3 and isinstance(call.args[2], ast.Name) and
        call.args[2].id == "validity_monitor"
        for call in calls(nested_submit, "wait_for_cover_acceptance"))

    planner_start = min(node.lineno for node in ast.walk(loop)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and
        node.func.id == "begin_model_turn")
    initial_branch = next((node for node in ast.walk(loop)
        if isinstance(node, ast.If) and
        compares_field(node.test, "cover_acceptance", "event", "policy_invalidation")), None)
    initial_cancel_before_planner = (
        initial_branch is not None and initial_branch.lineno < planner_start and
        any(call.lineno < planner_start
            for call in calls(initial_branch, "cancel_unplanned_invalidated_cover")) and
        any(isinstance(part, ast.Continue) for part in ast.walk(initial_branch)))

    renewal_branch = next((node for node in ast.walk(loop)
        if isinstance(node, ast.If) and
        compares_field(node.test, "next_accepted", "event", "policy_invalidation")), None)
    renewal_cancel_path = (
        renewal_branch is not None and
        bool(calls(renewal_branch, "cancel_invalidated_cover")) and
        any(isinstance(part, ast.Break) for part in ast.walk(renewal_branch)))

    checks = {
        "acceptance_wait_forwards_monitor": wait_forwards_monitor,
        "submit_path_uses_selected_validity_monitor": submit_passes_validity_monitor,
        "initial_invalidation_cancels_and_continues_before_planner": initial_cancel_before_planner,
        "renewal_invalidation_uses_planner_cancel_path": renewal_cancel_path,
        "unplanned_cancel_requires_verified_empty_release": (
        unplanned_cancel is not None and
        bool(calls(unplanned_cancel, "terminal_release_verified")) and
            '"op": "cancel"' in ast.get_source_segment(
                source_bytes.decode("utf-8"), unplanned_cancel)),
        "not_started_admission_is_accounted": '"not_started"' in
            source_bytes.decode("utf-8"),
    }
    return {
        "schema": "map01-v40-admission-path-audit-v1",
        "candidate_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "checks": checks,
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "decision": "PASS_ADMISSION_PATH_STRUCTURE" if all(checks.values()) else
                    "FAIL_ADMISSION_PATH_STRUCTURE",
        "scope": "read-only AST/source audit; no child session, game, model, GUI, input, or task-effect validation",
    }


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit_admission_path.py SOURCE OUTPUT_JSON")
    source_path, output_path = map(Path, sys.argv[1:])
    result = audit(source_path.read_bytes())
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if not result["failed_checks"] else 1)


if __name__ == "__main__":
    main()
