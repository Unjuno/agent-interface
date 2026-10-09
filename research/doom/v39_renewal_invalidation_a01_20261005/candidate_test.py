"""Source-extracted FIFO regression for V39 renewal admission races.
Run: python candidate_test.py [path/to/map01_overlap_controller_v39.py]
Uses only the Python standard library; no Doom/model/input runtime.
"""
import ast
import copy
import json
import sys
from pathlib import Path

controller_path = (Path(sys.argv[1]) if len(sys.argv) > 1 else
                   Path(__file__).resolve().parents[1] / "map01_overlap_controller_v39.py")
tree = ast.parse(controller_path.read_text(encoding="utf-8"))
main = next(node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main")
branch = next(node for node in ast.walk(main)
              if isinstance(node, ast.If) and "next_accepted" in ast.dump(node.test)
              and "policy_invalidation" in ast.dump(node.test))
helper_names = {"resolve_invalidated_cover_submission", "cancel_invalidated_cover",
                "resolve_invalidated_cover_renewal"}
helpers = [node for node in tree.body
           if isinstance(node, ast.FunctionDef) and node.name in helper_names]
factory = ast.parse(
    "def renewal_branch(next_accepted, next_cover, planner, planner_handle, "
    "process, wait, cover_terminals, cover_ids, current_terminal):\n"
    "    invalidation = None\n"
    "    planner_interrupt = None\n"
    "    current_cover = 'old'\n").body[0]
factory.body.append(ast.While(test=ast.Constant(True),
                              body=copy.deepcopy(branch.body), orelse=[]))
factory.body.extend(ast.parse(
    "return invalidation, planner_interrupt, current_cover, current_terminal, "
    "cover_terminals, cover_ids\n").body)
module = ast.fix_missing_locations(ast.Module(body=[*helpers, factory], type_ignores=[]))
scope = {"json": json}
exec(compile(module, str(controller_path), "exec"), scope)


class Stream:
    def __init__(self):
        self.writes = []
    def write(self, value):
        self.writes.append(value)
    def flush(self):
        pass


class Process:
    def __init__(self):
        self.stdin = Stream()


class Planner:
    def __init__(self):
        self.interrupted = []
    def interrupt(self, handle):
        self.interrupted.append(handle)
        return {"status": "interrupted"}


old_terminal = {"event": "terminal", "id": "old", "status": "completed",
                "release": {"verified": True, "keys_down": [], "buttons_down": []}}
for accepted in (False, True):
    planner, process, handle = Planner(), Process(), object()
    ids, terminals = ["old"], [old_terminal]
    accepted_row = {"event": "accepted", "id": "renewal"}
    rejected_row = {"event": "rejected", "reason": "stale_sequence"}
    cancelled_terminal = {
        "event": "terminal", "id": "renewal", "status": "cancelled",
        "release": {"verified": True, "keys_down": [], "buttons_down": []}}
    rows = iter(([accepted_row, cancelled_terminal] if accepted else [rejected_row]))

    def wait(predicate):
        row = next(rows)
        assert predicate(row), row
        return row

    result = scope["renewal_branch"](
        {"event": "policy_invalidation", "invalidation": {"reason": "hard"}},
        "renewal", planner, handle, process, wait, terminals, ids, old_terminal)
    assert result[0] == {"reason": "hard"}
    assert result[1] == {"status": "interrupted"}
    assert result[2] == "old"
    assert result[3] is (cancelled_terminal if accepted else old_terminal)
    assert terminals == ([old_terminal, cancelled_terminal] if accepted else [old_terminal])
    assert ids == (["old", "renewal"] if accepted else ["old"])
    assert len(process.stdin.writes) == (1 if accepted else 0)
    assert planner.interrupted == [handle]
print("TDD candidate integrated renewal invalidation: PASS 2/2")
