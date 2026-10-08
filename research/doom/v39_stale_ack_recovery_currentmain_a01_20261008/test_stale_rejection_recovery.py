import queue
import ast
import inspect
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research" / "doom"))
sys.path.insert(0, str(ROOT / "research" / "live_control"))
from research.live_control.test_running_action_guard_v2 import guard_v2
from research.live_control.test_final_action_admission_v2 import (
    ACTION, turn, validity)
from research.live_control.final_action_admission_v2 import (
    decide_final_admission, record_action_validity)
from research.live_control.running_action_guard_v3 import RunningActionGuardV3
from map01_overlap_controller_v39 import recover_stale_executor_rejection


def ready_guard():
    old = guard_v2()
    return RunningActionGuardV3(old.action, old.final_admission,
                                old.compiler, old.compiler_identity)


def ready_admission():
    return record_action_validity(
        decide_final_admission(turn(), None, 11), ACTION, validity())


class StaleRejectionRecoveryTests(unittest.TestCase):
    def test_controller_wires_stale_rejection_to_discard_and_next_iteration(self):
        tree = ast.parse(inspect.getsource(
            __import__("map01_overlap_controller_v39")))
        main = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "main")
        execute = next(node for node in ast.walk(main)
                       if isinstance(node, ast.FunctionDef) and
                       node.name == "execute_segment")
        self.assertTrue(any(isinstance(node, ast.Call) and
                            isinstance(node.func, ast.Name) and
                            node.func.id == "recover_stale_executor_rejection"
                            for node in ast.walk(execute)))
        refresh = next(node for node in ast.walk(main)
                       if isinstance(node, ast.FunctionDef) and
                       node.name == "refresh_between_segments")
        self.assertTrue(any(isinstance(node, ast.Call) and
                            isinstance(node.func, ast.Name) and
                            node.func.id == "recover_stale_executor_rejection"
                            for node in ast.walk(refresh)))
        routes = [node for node in ast.walk(main) if isinstance(node, ast.If) and
                  "stale_rejection" in ast.unparse(node.test) and
                  "is not None" in ast.unparse(node.test)]
        self.assertGreaterEqual(len(routes), 3)
        terminal_route = next(node for node in routes
                              if any(isinstance(child, ast.Continue)
                                     for child in ast.walk(node)))
        source = ast.unparse(terminal_route)
        self.assertIn("decisions.append", source)
        self.assertIn("discard_reason", source)

    def test_stale_rejection_discards_candidate_and_returns_fresh_observation(self):
        incoming = queue.Queue()
        incoming.put({"event": "typed_observation", "sequence": 3})
        incoming.put({"event": "observation", "sequence": 3, "capture_ns": 30})
        guard = ready_guard()
        result = recover_stale_executor_rejection(
            {"event": "rejected", "reason":
             "latest observation sequence required before input"},
            identifier="plan-0", expected_sequence=2,
            controller_received_ns=15,
            latest={"event": "observation", "sequence": 2, "capture_ns": 20},
            incoming=incoming, wait=lambda *args, **kwargs: self.fail("fresh row already queued"),
            final_action_admission=ready_admission(), running_guard=guard)
        self.assertEqual(result["latest"]["sequence"], 3)
        self.assertEqual(result["admission"]["status"], "REJECTED_EXECUTOR_STALE_SEQUENCE")
        self.assertIsNone(result["admission"]["executor_admission"])
        self.assertFalse(result["admission"]["input_authority_admitted"])
        self.assertEqual(result["guard"]["state"], "REJECTED_BEFORE_PROGRAM_ADMISSION")
        self.assertTrue(result["guard"]["physical_release_verified"])
        self.assertFalse(result["guard"]["current_input_authority"])
        self.assertTrue(result["guard"]["requires_new_decision"])
        self.assertEqual(result["rejection"]["observed_sequence"], 3)

    def test_non_stale_rejection_is_not_retried_as_freshness_recovery(self):
        with self.assertRaisesRegex(ValueError, "stale-sequence rejection"):
            recover_stale_executor_rejection(
                {"event": "rejected", "reason": "unsupported operation"},
                identifier="plan-0", expected_sequence=2,
                controller_received_ns=15,
                latest={"event": "observation", "sequence": 2, "capture_ns": 20},
                incoming=queue.Queue(), wait=lambda *args, **kwargs: None,
                final_action_admission=ready_admission(),
                running_guard=ready_guard())

    def test_recovery_backlog_budget_exhaustion_fails_closed(self):
        incoming = queue.Queue()
        for sequence in range(3, 3 + 1025):
            incoming.put({"event": "observation", "sequence": sequence})
        with self.assertRaisesRegex(RuntimeError, "recovery budget exhausted"):
            recover_stale_executor_rejection(
                {"event": "rejected", "reason":
                "latest observation sequence required before input"},
                identifier="plan-0", expected_sequence=2,
                controller_received_ns=15,
                latest={"event": "observation", "sequence": 2, "capture_ns": 20},
                incoming=incoming, wait=lambda *args, **kwargs: None,
                final_action_admission=ready_admission(),
                running_guard=ready_guard())


if __name__ == "__main__":
    unittest.main()

