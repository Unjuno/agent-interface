import threading
import unittest
from pathlib import Path

from research.live_control.persistent_planner_adapter_v2 import (
    PersistentPlannerAdapter, PlannerProtocolError,
)


SCHEMA = {
    "type": "object",
    "properties": {"action": {"type": "string"}},
    "required": ["action"],
    "additionalProperties": False,
}


class FakeClient:
    def __init__(self, completions, usage=None):
        self.completions = list(completions)
        self.usage = usage
        self.thread_count = 0
        self.turn_count = 0
        self.interrupts = []
        self.started = []
        self.release_completion = threading.Event()
        self.close_calls = []
        self.fail_interrupt = False

    def close(self, timeout=5):
        self.close_calls.append(timeout)
        self.release_completion.set()

    def start_thread(self, **params):
        self.thread_count += 1
        return {"thread": {"id": f"thread-{self.thread_count}"}}

    def start_turn(self, thread_id, inputs, **params):
        self.turn_count += 1
        self.started.append((thread_id, inputs, params))
        return {"turn": {"id": f"turn-{self.turn_count}"}}

    def wait_turn_completed(self, thread_id, turn_id, timeout=120):
        completion = self.completions.pop(0)
        if completion == "WAIT":
            if not self.release_completion.wait(timeout):
                raise TimeoutError
            completion = self.completions.pop(0)
        return {"threadId": thread_id, "turn": {"id": turn_id, **completion}}

    def latest_turn_usage(self, thread_id, turn_id):
        return self.usage

    def interrupt_turn(self, thread_id, turn_id):
        self.interrupts.append((thread_id, turn_id))
        if self.fail_interrupt:
            raise OSError("synthetic transport failure")
        return {}


def adapter(client):
    result = PersistentPlannerAdapter(
        client, model="gpt-5.6-luna", effort="low", cwd="C:/repo",
        base_instructions="Return JSON only.")
    result.start_session()
    return result


def completed(text='{"action":"forward"}'):
    return {"status": "completed", "items": [{"type": "agentMessage", "text": text}]}


class PersistentPlannerAdapterTests(unittest.TestCase):
    def test_completed_structured_answer_is_eligible_and_usage_is_preserved(self):
        client = FakeClient([completed()], usage={"inputTokens": 7, "outputTokens": 3})
        planner = adapter(client)
        handle = planner.begin_turn("observe", output_schema=SCHEMA, image_path="C:/frame.png")
        result = planner.await_turn(handle)
        self.assertTrue(result.answer_eligible)
        self.assertEqual(result.answer, {"action": "forward"})
        self.assertEqual(result.usage, {"inputTokens": 7, "outputTokens": 3})
        self.assertEqual(client.started[0][1][1], {
            "type": "localImage", "path": str(Path("C:/frame.png"))})

    def test_interrupted_turn_never_admits_partial_or_completed_answer(self):
        client = FakeClient([completed()])
        planner = adapter(client)
        handle = planner.begin_turn("observe", output_schema=SCHEMA)
        self.assertEqual(planner.interrupt(handle)["outcome"], "requested")
        result = planner.await_turn(handle)
        self.assertFalse(result.answer_eligible)
        self.assertTrue(result.cancellation_requested)
        self.assertIn("invalidated observation", result.error)

    def test_abort_pending_turn_closes_transport_and_unblocks_waiter(self):
        client = FakeClient(["WAIT", completed()])
        planner = adapter(client)
        handle = planner.begin_turn("observe", output_schema=SCHEMA)
        box = {}
        waiter = threading.Thread(target=lambda: box.setdefault("result", planner.await_turn(handle)))
        waiter.start()
        client.fail_interrupt = True
        self.assertEqual(planner.interrupt(handle)["outcome"], "request_error")
        planner.abort_pending_turn()
        waiter.join(1)
        self.assertFalse(waiter.is_alive())
        self.assertEqual(client.close_calls, [5])
        self.assertFalse(box["result"].answer_eligible)
        self.assertTrue(box["result"].cancellation_requested)

    def test_duplicate_interrupt_sends_only_one_request(self):
        client = FakeClient([{"status": "interrupted", "items": []}])
        planner = adapter(client)
        handle = planner.begin_turn("observe", output_schema=SCHEMA)
        self.assertEqual(planner.interrupt(handle)["outcome"], "requested")
        self.assertEqual(planner.interrupt(handle)["outcome"], "already_requested")
        self.assertEqual(client.interrupts, [("thread-1", "turn-1")])
        self.assertFalse(planner.await_turn(handle).answer_eligible)

    def test_before_transport_hook_runs_after_local_invalidation(self):
        events = []

        class EventClient(FakeClient):
            def interrupt_turn(self, thread_id, turn_id):
                events.append("interrupt_transport")
                return super().interrupt_turn(thread_id, turn_id)

        client = EventClient([{"status": "interrupted", "items": []}])
        planner = adapter(client)
        handle = planner.begin_turn("observe", output_schema=SCHEMA)

        def cancel_input():
            self.assertTrue(planner._cancellation_requested)
            events.append("cancel_input")

        result = planner.interrupt(handle, before_transport=cancel_input)

        self.assertEqual(events, ["cancel_input", "interrupt_transport"])
        self.assertEqual(result["outcome"], "requested")
        self.assertFalse(planner.await_turn(handle).answer_eligible)

    def test_before_transport_hook_runs_for_already_terminal_turn(self):
        client = FakeClient([completed()])
        planner = adapter(client)
        handle = planner.begin_turn("observe", output_schema=SCHEMA)
        planner.await_turn(handle)
        events = []

        result = planner.interrupt(handle, before_transport=lambda: events.append("cancel_input"))

        self.assertEqual(result, {"outcome": "already_terminal", "status": "completed"})
        self.assertEqual(events, ["cancel_input"])
        self.assertEqual(client.interrupts, [])

    def test_before_transport_error_does_not_skip_remote_interrupt(self):
        client = FakeClient([{"status": "interrupted", "items": []}])
        planner = adapter(client)
        handle = planner.begin_turn("observe", output_schema=SCHEMA)

        def fail_cancel_input():
            raise OSError("synthetic executor write failure")

        result = planner.interrupt(handle, before_transport=fail_cancel_input)

        self.assertEqual(result["outcome"], "requested")
        self.assertIn("synthetic executor write failure", result["before_transport_error"])
        self.assertEqual(client.interrupts, [("thread-1", "turn-1")])

    def test_completion_wins_race_before_interrupt(self):
        client = FakeClient([completed()])
        planner = adapter(client)
        handle = planner.begin_turn("observe", output_schema=SCHEMA)
        result = planner.await_turn(handle)
        self.assertTrue(result.answer_eligible)
        self.assertEqual(planner.interrupt(handle), {
            "outcome": "already_terminal", "status": "completed"})
        self.assertEqual(client.interrupts, [])

    def test_interrupt_wins_race_while_completion_waits(self):
        client = FakeClient(["WAIT", completed()])
        planner = adapter(client)
        handle = planner.begin_turn("observe", output_schema=SCHEMA)
        box = {}
        waiter = threading.Thread(target=lambda: box.setdefault("result", planner.await_turn(handle)))
        waiter.start()
        self.assertEqual(planner.interrupt(handle)["outcome"], "requested")
        client.release_completion.set()
        waiter.join(1)
        self.assertFalse(box["result"].answer_eligible)

    def test_missing_usage_remains_unknown(self):
        planner = adapter(FakeClient([completed()], usage=None))
        result = planner.await_turn(planner.begin_turn("observe", output_schema=SCHEMA))
        self.assertIsNone(result.usage)

    def test_malformed_or_ambiguous_messages_fail_closed(self):
        cases = [
            {"status": "completed", "items": []},
            completed("not json"),
            completed('{"wrong":"field"}'),
            {"status": "completed", "items": [
                {"type": "agentMessage", "text": "{}"},
                {"type": "agentMessage", "text": "{}"}]},
        ]
        client = FakeClient(cases)
        planner = adapter(client)
        for _ in cases:
            result = planner.await_turn(planner.begin_turn("observe", output_schema=SCHEMA))
            self.assertFalse(result.answer_eligible)

    def test_session_identity_is_continuous_and_reset_is_explicit(self):
        client = FakeClient([completed(), completed()])
        planner = adapter(client)
        first = planner.begin_turn("one", output_schema=SCHEMA)
        planner.await_turn(first)
        second = planner.begin_turn("two", output_schema=SCHEMA)
        self.assertEqual(first.thread_id, second.thread_id)
        planner.await_turn(second)
        planner.start_session()
        third = planner.begin_turn("three", output_schema=SCHEMA)
        self.assertNotEqual(second.thread_id, third.thread_id)
        with self.assertRaises(PlannerProtocolError):
            planner.interrupt(second)

    def test_overlapping_turns_and_reset_with_active_turn_are_rejected(self):
        planner = adapter(FakeClient([completed()]))
        planner.begin_turn("one", output_schema=SCHEMA)
        with self.assertRaises(PlannerProtocolError):
            planner.begin_turn("two", output_schema=SCHEMA)
        with self.assertRaises(PlannerProtocolError):
            planner.start_session()

    def test_action_contract_bounds_and_const_fail_closed(self):
        bounded = {
            "type": "object",
            "properties": {
                "label": {"type": "string", "minLength": 2, "maxLength": 4},
                "index": {"type": "integer", "minimum": 0, "maximum": 2},
                "condition": {"type": "string", "const": "visible"},
                "items": {"type": "array", "minItems": 1, "maxItems": 2,
                          "uniqueItems": True, "items": {"type": "string"}},
            },
            "required": ["label", "index", "condition", "items"],
            "additionalProperties": False,
        }
        bad = [
            '{"label":"x","index":1,"condition":"visible","items":["a"]}',
            '{"label":"okay","index":3,"condition":"visible","items":["a"]}',
            '{"label":"okay","index":1,"condition":"hidden","items":["a"]}',
            '{"label":"okay","index":1,"condition":"visible","items":[]}',
            '{"label":"okay","index":1,"condition":"visible","items":["a","a"]}',
        ]
        client = FakeClient([completed(text) for text in bad])
        planner = adapter(client)
        for _ in bad:
            result = planner.await_turn(planner.begin_turn("observe", output_schema=bounded))
            self.assertFalse(result.answer_eligible)
        good = completed('{"label":"okay","index":2,"condition":"visible","items":["a","b"]}')
        planner = adapter(FakeClient([good]))
        result = planner.await_turn(planner.begin_turn("observe", output_schema=bounded))
        self.assertTrue(result.answer_eligible)


if __name__ == "__main__":
    unittest.main()
