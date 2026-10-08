"""Construction regression for V39 events arriving during completed-future drain."""

import ast
import inspect
import queue
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import map01_overlap_controller_v39 as controller


class InjectingMonitor:
    event_types = frozenset({"observation"})

    def __init__(self, incoming, *, continuous=False):
        self.incoming = incoming
        self.continuous = continuous
        self.observed = []

    def observe(self, row):
        sequence = row["sequence"]
        self.observed.append(sequence)
        if self.continuous or sequence == 11:
            self.incoming.put({"event": "observation", "sequence": sequence + 1})
        if sequence == 12 and not self.continuous:
            return {
                "event": "paired_signal_invalidation",
                "sequence": 12,
                "reason": "hard_health_crossing",
                "requires_new_decision": True,
                "grants_input_authority": False,
            }
        return None


class CompletedFutureDrainTests(unittest.TestCase):
    def test_event_arriving_during_drain_invalidates_answer_before_replan(self):
        incoming = queue.Queue()
        incoming.put({"event": "observation", "sequence": 11})
        monitor = InjectingMonitor(incoming)

        drained = controller.drain_pending_observation_events(
            incoming, monitor, "cover-0")

        self.assertEqual(drained["latest"]["sequence"], 12)
        self.assertEqual(drained["invalidation"]["sequence"], 12)
        self.assertEqual(monitor.observed, [11, 12])
        self.assertTrue(incoming.empty())

        # V39's main must discard this completed answer and continue its outer
        # decision loop before it can reach fresh-state validation/submission.
        tree = ast.parse(inspect.getsource(controller.main))
        calls = [node for node in ast.walk(tree)
                 if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name)
                 and node.func.id == "drain_pending_observation_events"]
        self.assertEqual(len(calls), 1)
        drain_line = calls[0].lineno
        replan_branches = [node for node in ast.walk(tree)
                            if isinstance(node, ast.If)
                            and any(isinstance(child, ast.Continue)
                                    for child in ast.walk(node))
                            and "invalidation" in ast.unparse(node.test)]
        self.assertTrue(replan_branches, "main must continue after an invalidated planner answer")
        replan_branch = min(replan_branches, key=lambda node: node.lineno)
        loop = next(node for node in ast.walk(tree)
                    if isinstance(node, ast.For)
                    and isinstance(node.target, ast.Name)
                    and node.target.id == "index")
        loop_calls = [node for node in ast.walk(loop)
                      if isinstance(node, ast.Call)
                      and isinstance(node.func, ast.Name)]
        refresh_calls = [node for node in loop_calls if node.func.id == "refresh_source"]
        self.assertTrue(refresh_calls)
        self.assertIsInstance(refresh_calls[0].args[0], ast.Name)
        self.assertEqual(refresh_calls[0].args[0].id, "latest")
        latest_assignments = [node for node in ast.walk(loop)
                              if isinstance(node, ast.Assign)
                              and any(isinstance(target, ast.Name)
                                      and target.id == "latest" for target in node.targets)
                              and ast.unparse(node.value) == "drained['latest']"]
        self.assertTrue(latest_assignments, "main must carry the newest drained frame forward")
        discard_line = replan_branch.lineno
        latest_line = latest_assignments[0].lineno
        submit_line = min(node.lineno for node in ast.walk(loop)
                          if isinstance(node, ast.Name)
                          and node.id == "submit_command")
        self.assertLess(drain_line, discard_line)
        self.assertLess(drain_line, latest_line)
        self.assertLess(latest_line, discard_line)
        self.assertLess(discard_line, submit_line)

    def test_continuously_refilled_queue_hits_a_finite_fail_closed_bound(self):
        incoming = queue.Queue()
        incoming.put({"event": "observation", "sequence": 0})
        monitor = InjectingMonitor(incoming, continuous=True)

        drained = controller.drain_pending_observation_events(
            incoming, monitor, "cover-0")

        self.assertEqual(drained["drained_event_count"],
                         controller.COMPLETED_TURN_DRAIN_EVENT_LIMIT)
        self.assertTrue(drained["backlog_pending"])
        with self.assertRaisesRegex(RuntimeError, "refusing planner answer"):
            controller.require_completed_turn_drain_complete(drained)
        main_tree = ast.parse(inspect.getsource(controller.main))
        required_checks = [node for node in ast.walk(main_tree)
                           if isinstance(node, ast.Call)
                           and isinstance(node.func, ast.Name)
                           and node.func.id == "require_completed_turn_drain_complete"]
        answer_reads = [node for node in ast.walk(main_tree)
                        if isinstance(node, ast.Attribute)
                        and isinstance(node.value, ast.Name)
                        and node.value.id == "future" and node.attr == "result"]
        self.assertEqual(len(required_checks), 1)
        self.assertTrue(answer_reads)
        self.assertLess(required_checks[0].lineno, min(node.lineno for node in answer_reads))


if __name__ == "__main__":
    unittest.main()
