"""Contract tests for the single-attempt Mindustry socket submit adapter."""

import unittest
from pathlib import Path

from target_socket_submit_v1 import SocketSubmitStop, TargetSocketSubmitter


def success(action_id, *, cursor=7):
    return {
        "status": "boundary",
        "records": [{"event": "terminal", "id": action_id,
                     "status": "completed", "release": {"verified": True}}],
        "cursor": cursor,
        "command_receipt": {"request_id": action_id, "replayed": False,
                            "state": "stdin_flushed"},
    }


class TargetSocketSubmitTests(unittest.TestCase):
    def command(self, identifier="A1-select-conveyor"):
        return {"op": "submit", "id": identifier,
                "expected_sequence": 5, "steps": [{"op": "observe"}]}

    def test_sends_v2_action_scope_and_returns_release_receipt(self):
        sent = []
        submitter = TargetSocketSubmitter("/tmp/unused.sock", after=3)

        def exchange(request):
            sent.append(request)
            return success(request["action_id"], cursor=11)

        submitter._exchange = exchange
        receipt = submitter(self.command())

        self.assertEqual(receipt, {"request_id": "A1-select-conveyor",
                                   "terminal": True, "released": True})
        self.assertEqual(sent[0]["after"], 3)
        self.assertEqual(sent[0]["events"], ["terminal", "rejected"])
        self.assertEqual(sent[0]["action_id"], sent[0]["request_id"])
        self.assertEqual(sent[0]["command"], self.command())
        self.assertEqual(submitter.cursor, 11)

    def test_unattributed_rejection_fails_closed_and_is_not_retried(self):
        calls = []
        submitter = TargetSocketSubmitter("/tmp/unused.sock")
        submitter._exchange = lambda request: calls.append(request) or {
            "status": "unattributed_rejection", "records": [
                {"event": "rejected", "reason": "bad command"}], "cursor": 1,
                "command_receipt": {"request_id": request["request_id"],
                                    "replayed": False,
                                    "state": "stdin_flushed"}}

        with self.assertRaisesRegex(SocketSubmitStop, "terminal action boundary"):
            submitter(self.command())
        with self.assertRaisesRegex(SocketSubmitStop, "already consumed"):
            submitter(self.command())
        self.assertEqual(len(calls), 1)

    def test_unverified_release_or_wrong_action_cannot_be_promoted(self):
        cases = [
            success("A1-select-conveyor") | {"records": [{
                "event": "terminal", "id": "A1-select-conveyor",
                "release": {"verified": False}}]},
            success("other-action"),
            success("A1-select-conveyor") | {"command_receipt": {
                "request_id": "wrong", "state": "stdin_flushed",
                "replayed": False}},
            success("A1-select-conveyor") | {"command_receipt": {
                "request_id": "A1-select-conveyor", "state": "write_uncertain",
                "replayed": False}},
        ]
        for response in cases:
            with self.subTest(response=response):
                submitter = TargetSocketSubmitter("/tmp/unused.sock")
                submitter._exchange = lambda _request, value=response: value
                with self.assertRaises(SocketSubmitStop):
                    submitter(self.command())

    def test_transport_exception_consumes_action_without_retry(self):
        calls = []
        submitter = TargetSocketSubmitter("/tmp/unused.sock")

        def lost_response(_request):
            calls.append(1)
            raise TimeoutError("response lost")

        submitter._exchange = lost_response
        with self.assertRaisesRegex(SocketSubmitStop, "outcome unknown"):
            submitter(self.command())
        with self.assertRaisesRegex(SocketSubmitStop, "already consumed"):
            submitter(self.command())
        self.assertEqual(calls, [1])

    def test_nonadvancing_cursor_is_not_a_terminal_receipt(self):
        submitter = TargetSocketSubmitter("/tmp/unused.sock", after=8)
        submitter._exchange = lambda request: success(request["action_id"], cursor=8)
        with self.assertRaisesRegex(SocketSubmitStop, "advancing socket event cursor"):
            submitter(self.command())

    def test_task_wrapper_selects_v2_bridge_and_receipt_child(self):
        source = (Path(__file__).with_name("mindustry_three_arm_socket_v2.py")
                  .read_text(encoding="utf-8"))
        self.assertIn("import stopped_socket_v2 as bridge", source)
        self.assertIn("mindustry_three_arm_interactive_v1.py", source)
        self.assertIn("bridge.main()", source)


if __name__ == "__main__":
    unittest.main()
