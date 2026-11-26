"""Drive the real V39 pending-cover loop with fake protocol events."""
import ast
import io
import json
import os
import select
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

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
        recover_cover_owner, out=None):
    current_cover = "cover-0"
    current_terminal = invalidation = planner_interrupt = None
    cover_ids = [current_cover]
    cover_terminals = []
    cover_renewal_gaps_ms = []
    index = 0
    planner_handle = "pending-turn"
    failure_cleanup = SimpleNamespace(set_stage=lambda stage: None)
    args = SimpleNamespace(out=out)
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
    def run_renewal(self, result, *, followup_error=None):
        observation = {"event": "typed_observation", "sequence": 8}
        followup = {"event": "typed_observation", "sequence": 9}
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

        def submit(identifier, consumed_events=None, *, renewal=False):
            self.assertEqual(identifier, RENEWED)
            self.assertTrue(renewal)
            if consumed_events is not None:
                consumed_events.append(observation)
                if followup_error is not None:
                    consumed_events.append(followup)
            return {"event": "accepted", "id": identifier, "accepted_ns": 200}

        future = SimpleNamespace(done=Mock(side_effect=(False, False, True)))
        observer = SimpleNamespace(event_types={"typed_observation"}, observe=Mock())
        if followup_error is not None:
            observer.observe.side_effect = (result, followup_error)
        elif isinstance(result, Exception):
            observer.observe.side_effect = result
        else:
            observer.observe.return_value = result
        planner = SimpleNamespace(invalidate_turn=Mock(return_value={"outcome": "invalidated"}),
                                  interrupt=Mock(return_value={"outcome": "interrupted"}))
        recovery = Mock()
        process = SimpleNamespace(stdin=io.StringIO())
        settled = pending_cover_loop()(future, wait, submit, observer, planner, process, recovery)
        if followup_error is None:
            observer.observe.assert_called_once_with(observation)
        else:
            self.assertEqual([call.args[0] for call in observer.observe.call_args_list], [observation, followup])
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

    def test_later_reader_error_does_not_replace_observed_hard_reason(self):
        hard = {"reason": "health_below_floor", "requires_new_decision": True}
        result, process, planner, _ = self.run_renewal(hard, followup_error=ValueError("late unreadable frame"))
        self.assertEqual(result[0], {**hard, "observation_error_type": "ValueError"})
        self.assertEqual(json.loads(process.stdin.getvalue()), {"op": "cancel", "id": RENEWED})
        planner.invalidate_turn.assert_called_once_with("pending-turn")

    def test_uncertain_ack_attempts_owned_cancel_and_aborts_planner(self):
        timeout = TimeoutError("renewal ACK missing")
        malformed = {"event": "accepted", "id": RENEWED}
        reverse_time = {"event": "accepted", "id": RENEWED, "accepted_ns": 99}
        future_time = {"event": "accepted", "id": RENEWED, "accepted_ns": 10**30}
        for response, terminal_kind in ((timeout, "missing"), (malformed, "released"),
                                        (reverse_time, "not_empty"), (future_time, "released")):
            with self.subTest(response=response), TemporaryDirectory() as directory:
                old = terminal("cover-0", status="completed", stamp=100)
                ending = terminal(RENEWED, status="cancelled", stamp=300)
                if terminal_kind == "not_empty":
                    ending["release"]["keys_unknown"] = ["Up"]
                planner = SimpleNamespace(invalidate_turn=Mock(return_value={"outcome": "invalidated"}),
                                          abort_pending_turn=Mock(return_value={"outcome": "aborted"}))
                recover = Mock()
                reader, writer = os.pipe()
                cancellations = []
                with os.fdopen(reader, "r") as messages, os.fdopen(writer, "w") as stream:
                    def wait(predicate, **options):
                        if predicate(old):
                            return old
                        self.assertTrue(predicate(ending))
                        self.assertEqual(options["timeout"], controller.COVER_RENEWAL_IO_SECONDS)
                        planner.invalidate_turn.assert_called_once_with("pending-turn")
                        self.assertTrue(select.select([reader], [], [], 0.25)[0])
                        cancellations.append(json.loads(messages.readline()))
                        if terminal_kind == "missing":
                            raise TimeoutError("renewal terminal missing")
                        return ending

                    def submit(identifier, consumed_events, *, renewal):
                        self.assertTrue(renewal)
                        self.assertEqual(identifier, RENEWED)
                        if isinstance(response, Exception):
                            raise response
                        return response

                    future = SimpleNamespace(done=Mock(side_effect=(False, False)))
                    cause = TimeoutError if response is timeout else ValueError
                    with self.assertRaises(cause) as raised:
                        pending_cover_loop()(future, wait, submit, None, planner,
                                             SimpleNamespace(stdin=stream), recover, Path(directory))
                if response is timeout:
                    self.assertIs(raised.exception, timeout)
                receipt = json.loads((Path(directory) / "cover-renewal-unverified.json").read_bytes())
                self.assertEqual(raised.exception.cover_renewal_receipt, receipt)
                self.assertEqual(receipt["id"], RENEWED)
                self.assertEqual(cancellations, [{"op": "cancel", "id": RENEWED}])
                self.assertEqual(receipt["admission"], "UNKNOWN")
                self.assertEqual(receipt["verified_empty_release"], terminal_kind == "released")
                self.assertEqual(receipt["input_recovery_required"], terminal_kind != "released")
                self.assertIs(receipt["grants_input_authority"], False)
                planner.abort_pending_turn.assert_called_once_with()
                recover.assert_not_called()

    def test_uncertain_renewal_reaches_outer_cleanup_without_joining(self):
        pool = Mock()
        error = TimeoutError("renewal ACK did not arrive")
        error.cover_renewal_receipt = {"admission": "UNKNOWN", "planner_abort_error": "TimeoutError"}
        with patch.object(controller, "ThreadPoolExecutor", return_value=pool):
            with self.assertRaises(TimeoutError) as raised:
                with controller.pending_cover_planner_pool():
                    raise error
        self.assertIs(raised.exception, error)
        pool.shutdown.assert_called_once_with(wait=False, cancel_futures=True)

    def test_full_renewal_pipe_times_out_and_restores_blocking_mode(self):
        reader, writer = os.pipe()
        with os.fdopen(reader, "rb"), os.fdopen(writer, "w") as stream:
            os.set_blocking(writer, False)
            chunk = b"x" * os.fpathconf(writer, "PC_PIPE_BUF")
            while True:
                try:
                    os.write(writer, chunk)
                except BlockingIOError:
                    break
            os.set_blocking(writer, True)
            with self.assertRaisesRegex(TimeoutError, "did not become writable"):
                controller.send_bounded_cover_command(stream, {"op": "cancel", "id": RENEWED}, timeout=.01)
            self.assertTrue(os.get_blocking(writer))

    def test_late_pipe_readiness_does_not_write_after_deadline(self):
        reader, writer = os.pipe()
        with os.fdopen(reader, "rb"), os.fdopen(writer, "w") as stream:
            with patch.object(controller.select, "select", return_value=([], [writer], [])), \
                 patch.object(controller.time, "monotonic", side_effect=(0.0, 0.0, 2.1)):
                with self.assertRaisesRegex(TimeoutError, "after its deadline"):
                    controller.send_bounded_cover_command(stream, {"op": "cancel", "id": RENEWED})
            self.assertEqual(select.select([reader], [], [], 0)[0], [])
            self.assertTrue(os.get_blocking(writer))
