"""Drive the real V39 pending-cover loop with fake protocol events."""
import ast
import io
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "live_control")]
import map01_overlap_controller_v39 as controller

RENEWED = "cover-0-renew-1"


def pending_cover_loop():
    source = Path(controller.__file__)
    tree = ast.parse(source.read_bytes(), filename=str(source))
    main = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "main")
    loop = next(node for node in ast.walk(main)
                if isinstance(node, ast.While) and ast.unparse(node.test) == "not future.done()"
                and any(isinstance(child, ast.Name) and child.id == "next_cover"
                        for child in ast.walk(node)))
    module = ast.parse("""
def run(future, wait, submit_cover, invalidation_monitor, planner, process,
        recover_cover_owner):
    current_cover = "cover-0"
    current_terminal = invalidation = planner_interrupt = None
    cover_ids = [current_cover]
    cover_terminals = []
    cover_renewal_gaps_ms = []
    index = 0
    planner_handle = "pending-turn"
    failure_cleanup = SimpleNamespace(set_stage=lambda stage: None)
    args = SimpleNamespace(out=None)
    return invalidation, current_terminal, cover_terminals, planner_interrupt
""")
    module.body[0].body.insert(-1, loop)
    namespace = {**vars(controller), "SimpleNamespace": SimpleNamespace}
    exec(compile(ast.fix_missing_locations(module), str(source), "exec"), namespace)
    return namespace["run"]


def terminal(cover, *, status, stamp):
    return {"event": "terminal", "id": cover, "status": status, "terminal_ns": stamp,
            "release": {"event": "owner_release", "verified": True, "keys_down": [], "buttons_down": [],
                        "keys_unknown": [], "key_state_errors": []}}


class RenewalObservationTests(unittest.TestCase):
    def run_renewal(self, result):
        observation = {"event": "typed_observation", "sequence": 8}
        old = terminal("cover-0", status="completed", stamp=100)
        retired = terminal(RENEWED, status="cancelled", stamp=300)
        waiting = iter((old, retired))

        def wait(predicate, **options):
            row = next(waiting)
            self.assertTrue(predicate(row))
            if row is retired:
                self.assertEqual(json.loads(process.stdin.getvalue()), {"op": "cancel", "id": RENEWED})
                planner.invalidate_turn.assert_called_once_with("pending-turn")
                planner.interrupt.assert_not_called()
            return row

        def submit(identifier, consumed_events=None):
            self.assertEqual(identifier, RENEWED)
            if consumed_events is not None:
                consumed_events.append(observation)
            return {"event": "accepted", "id": identifier, "accepted_ns": 200}

        future = SimpleNamespace(done=Mock(side_effect=(False, False, True)))
        observer = SimpleNamespace(event_types={"typed_observation"}, observe=Mock())
        if isinstance(result, Exception):
            observer.observe.side_effect = result
        else:
            observer.observe.return_value = result
        planner = SimpleNamespace(invalidate_turn=Mock(return_value={"outcome": "invalidated"}),
                                  interrupt=Mock(return_value={"outcome": "interrupted"}))
        recovery = Mock()
        process = SimpleNamespace(stdin=io.StringIO())
        settled = pending_cover_loop()(future, wait, submit, observer, planner, process, recovery)
        observer.observe.assert_called_once_with(observation)
        return settled, process, planner, recovery

    def test_hard_invalidation_consumed_before_ack_cancels_exact_renewal(self):
        invalidation = {"reason": "health_below_floor", "requires_new_decision": True}
        result, process, planner, recovery = self.run_renewal(invalidation)
        evidence, final_terminal, all_terminals, interrupt = result
        self.assertEqual(evidence, invalidation)
        self.assertEqual(json.loads(process.stdin.getvalue()), {"op": "cancel", "id": RENEWED})
        self.assertEqual([row["id"] for row in all_terminals], ["cover-0", RENEWED])
        self.assertEqual(final_terminal["status"], "cancelled")
        self.assertEqual(interrupt["outcome"], "interrupted")
        planner.invalidate_turn.assert_called_once_with("pending-turn")
        planner.interrupt.assert_called_once_with("pending-turn")
        recovery.assert_called_once_with(final_terminal, "policy_invalidated_cover")

    def test_benign_renewal_ack_observation_does_not_cancel(self):
        (invalidation, terminal_row, _, interrupt), process, planner, recovery = self.run_renewal(None)
        self.assertIsNone(invalidation)
        self.assertIsNone(terminal_row)
        self.assertIsNone(interrupt)
        self.assertEqual(process.stdin.getvalue(), "")
        planner.invalidate_turn.assert_not_called()
        recovery.assert_not_called()

    def test_unreadable_renewal_ack_observation_cancels_and_invalidates_planner(self):
        result, process, planner, _ = self.run_renewal(ValueError("invalid synthetic signal"))
        self.assertEqual(result[0]["reason"], "renewal_observation_unverified")
        self.assertTrue(result[0]["requires_new_decision"])
        self.assertEqual(json.loads(process.stdin.getvalue()), {"op": "cancel", "id": RENEWED})
        planner.invalidate_turn.assert_called_once_with("pending-turn")
