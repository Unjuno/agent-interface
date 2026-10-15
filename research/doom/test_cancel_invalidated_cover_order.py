import json
import sys
import threading
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "live_control")]
import map01_overlap_controller_v39 as controller
from persistent_planner_adapter_v2 import PersistentPlannerAdapter


class CancelOrderingTests(unittest.TestCase):
    def test_executor_cancel_is_flushed_before_planner_interrupt_ack_wait(self):
        events = []
        interrupt_entered = threading.Event()
        release_interrupt = threading.Event()

        class Stdin:
            def write(self, _value):
                events.append("cancel_write")

            def flush(self):
                events.append("cancel_flush")

        class Process:
            stdin = Stdin()

        class Client:
            def start_thread(self, **_params):
                return {"thread": {"id": "thread-1"}}

            def start_turn(self, *_args, **_params):
                return {"turn": {"id": "turn-1"}}

            def interrupt_turn(self, _thread_id, _turn_id):
                self.assert_invalidated()
                events.append("interrupt_request")
                interrupt_entered.set()
                if not release_interrupt.wait(1):
                    raise TimeoutError("test did not release interrupt response")
                events.append("interrupt_response")
                return {}

            def assert_invalidated(self):
                if not planner._cancellation_requested:
                    raise AssertionError("planner answer was not invalidated before transport")

        planner = PersistentPlannerAdapter(
            Client(), model="mock", effort="low", cwd=".", base_instructions="")
        planner.start_session()
        handle = planner.begin_turn("observe", output_schema={"type": "object"})

        terminal = {
            "event": "terminal",
            "id": "cover-1",
            "status": "cancelled",
            "release": {"event": "owner_release", "verified": True,
                        "keys_down": [], "buttons_down": [],
                        "keys_unknown": [], "key_state_errors": []},
        }
        result = {}

        def run_helper():
            result["value"] = controller.cancel_invalidated_cover(
                planner, handle, Process(), lambda _predicate: terminal, "cover-1")

        worker = threading.Thread(target=run_helper)
        worker.start()
        try:
            self.assertTrue(interrupt_entered.wait(1), "planner interrupt was not entered")
            self.assertEqual(
                events,
                ["cancel_write", "cancel_flush", "interrupt_request"],
            )
        finally:
            release_interrupt.set()
            worker.join(1)

        self.assertFalse(worker.is_alive(), "cancel helper did not finish")
        self.assertEqual(events[-1], "interrupt_response")
        self.assertIs(result["value"][1], terminal)

    def test_cancel_write_error_still_interrupts_and_waits_for_verified_release(self):
        events = []

        class Client:
            def start_thread(self, **_params):
                return {"thread": {"id": "thread-1"}}

            def start_turn(self, *_args, **_params):
                return {"turn": {"id": "turn-1"}}

            def interrupt_turn(self, _thread_id, _turn_id):
                events.append("interrupt_request")
                return {}

        class Stdin:
            def write(self, _value):
                raise OSError("synthetic executor write failure")

            def flush(self):
                events.append("cancel_flush")

        class Process:
            stdin = Stdin()

        planner = PersistentPlannerAdapter(
            Client(), model="mock", effort="low", cwd=".", base_instructions="")
        planner.start_session()
        handle = planner.begin_turn("observe", output_schema={"type": "object"})
        terminal = {
            "event": "terminal",
            "id": "cover-2",
            "status": "cancelled",
            "release": {"event": "owner_release", "verified": True,
                        "keys_down": [], "buttons_down": [],
                        "keys_unknown": [], "key_state_errors": []},
        }

        def wait(_predicate):
            events.append("terminal_wait")
            return terminal

        with self.assertRaisesRegex(RuntimeError, "synthetic executor write failure"):
            controller.cancel_invalidated_cover(
                planner, handle, Process(), wait, "cover-2")

        self.assertEqual(events, ["interrupt_request", "terminal_wait"])

    def test_ready_failed_terminal_is_not_inspected_during_blocked_planner_interrupt(self):
        """Characterize the unresolved synchronous planner dependency, not a bound."""
        entered = threading.Event()
        resume = threading.Event()
        inspected = threading.Event()
        result = {}
        events = []
        terminal = {"event": "terminal", "id": "cover-stalled", "status": "failed",
                    "release": {"event": "owner_release", "verified": False,
                                "keys_down": [38], "buttons_down": [],
                                "keys_unknown": [38], "key_state_errors": []}}

        class Client:
            def start_thread(self, **_params):
                return {"thread": {"id": "thread-1"}}

            def start_turn(self, *_args, **_params):
                return {"turn": {"id": "turn-1"}}

            def interrupt_turn(self, _thread_id, _turn_id):
                events.append("planner_interrupt_entered")
                entered.set()
                if not resume.wait(3):
                    raise TimeoutError("test gate was not released")
                events.append("planner_interrupt_returned")
                return {}

        class Stdin:
            def write(self, value):
                self_request = json.loads(value)
                if self_request != {"op": "cancel", "id": "cover-stalled"}:
                    raise AssertionError("wrong cancellation target")
                events.append("cancel_written")

            def flush(self):
                events.append("cancel_flushed")

        class Process:
            stdin = Stdin()

        planner = PersistentPlannerAdapter(
            Client(), model="mock", effort="low", cwd=".", base_instructions="")
        planner.start_session()
        handle = planner.begin_turn("observe", output_schema={"type": "object"})

        def wait(predicate):
            if not predicate(terminal):
                raise AssertionError("failed terminal was excluded")
            events.append("failed_terminal_inspected")
            inspected.set()
            return terminal

        def run_helper():
            try:
                result["value"] = controller.cancel_invalidated_cover(
                    planner, handle, Process(), wait, "cover-stalled")
            except BaseException as error:
                result["error"] = error

        worker = threading.Thread(target=run_helper)
        worker.start()
        try:
            self.assertTrue(entered.wait(1))
            self.assertTrue(planner._cancellation_requested)
            self.assertTrue(worker.is_alive())
            self.assertFalse(inspected.is_set())
            print(json.dumps({"case": "ready-failed-cover-terminal-planner-interrupt-held",
                              "terminal_ready": terminal, "terminal_inspected": False,
                              "planner_transport_resumed": False,
                              "answer_locally_invalidated": True,
                              "events": list(events),
                              "scope": "in-process substitutes; no physical input claim"}), flush=True)
        finally:
            resume.set()
            worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertTrue(inspected.is_set())
        self.assertNotIn("value", result)
        self.assertIsInstance(result["error"], RuntimeError)
        self.assertIn("did not verify empty release", str(result["error"]))
        self.assertEqual(events, ["cancel_written", "cancel_flushed",
                                 "planner_interrupt_entered", "planner_interrupt_returned",
                                 "failed_terminal_inspected"])


if __name__ == "__main__":
    unittest.main()
