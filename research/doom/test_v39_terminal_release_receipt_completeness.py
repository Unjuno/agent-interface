"""Fail-closed tests for V39 cover terminal release receipts."""
import ast
import copy
import json
import unittest
from pathlib import Path


SOURCE = Path(__file__).with_name("map01_overlap_controller_v39.py")
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"))
NAMES = {
    "require_cover_terminal",
    "cancel_initial_cover_before_planner",
    "cancel_invalidated_cover",
}
FUNCTIONS = [node for node in TREE.body
             if isinstance(node, ast.FunctionDef) and node.name in NAMES]
assert {node.name for node in FUNCTIONS} == NAMES
NAMESPACE = {"json": json, "RuntimeError": RuntimeError}
exec(compile(ast.Module(body=FUNCTIONS, type_ignores=[]), str(SOURCE), "exec"),
     NAMESPACE)


class Stdin:
    def write(self, _value):
        pass

    def flush(self):
        pass


class Process:
    stdin = Stdin()


class Planner:
    def interrupt(self, _handle, before_transport=None):
        if before_transport is not None:
            before_transport()
        return {"status": "interrupted"}


BASE_RELEASE = {
    "verified": True,
    "keys_down": [],
    "buttons_down": [],
    "keys_unknown": [],
    "key_state_errors": [],
}


def terminal(release=None, status="cancelled"):
    return {"event": "terminal", "id": "cover-a", "status": status,
            "release": copy.deepcopy(BASE_RELEASE if release is None else release)}


def wait_for(event):
    def wait(predicate):
        if predicate(event):
            return event
        raise AssertionError("expected event did not match wait predicate")
    return wait


class TerminalReleaseReceiptTests(unittest.TestCase):
    def test_known_empty_baseline_is_accepted_by_all_terminal_paths(self):
        NAMESPACE["require_cover_terminal"](terminal(status="completed"))
        NAMESPACE["cancel_initial_cover_before_planner"](
            Process(), wait_for(terminal()), "cover-a")
        NAMESPACE["cancel_invalidated_cover"](
            Planner(), object(), Process(), wait_for(terminal()), "cover-a")

    def test_missing_or_nonempty_unknown_error_fields_are_rejected(self):
        mutations = (
            ("keys_unknown", None),
            ("keys_unknown", ["KEY_W"]),
            ("key_state_errors", None),
            ("key_state_errors", [{"source": "keymap_after"}]),
        )
        paths = (
            lambda row: NAMESPACE["require_cover_terminal"](row),
            lambda row: NAMESPACE["cancel_initial_cover_before_planner"](
                Process(), wait_for(row), "cover-a"),
            lambda row: NAMESPACE["cancel_invalidated_cover"](
                Planner(), object(), Process(), wait_for(row), "cover-a"),
        )
        for field, value in mutations:
            release = copy.deepcopy(BASE_RELEASE)
            if value is None:
                release.pop(field)
            else:
                release[field] = value
            for path_index, exercise in enumerate(paths):
                with self.subTest(field=field, value=value, path=path_index):
                    with self.assertRaises(RuntimeError):
                        exercise(terminal(release))


if __name__ == "__main__":
    unittest.main()
