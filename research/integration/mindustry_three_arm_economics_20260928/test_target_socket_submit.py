"""Contract tests for the single-attempt Mindustry socket submit adapter."""

import unittest
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from arm_coordinator import ArmCoordinator
from target_execution_v1 import dispatch_task_targets
from target_receipts_v1 import (build_palette_receipt,
                                build_world_receipt)
from target_socket_submit_v1 import (JsonlTraceSink, SocketSubmitStop,
                                     TargetSocketSubmitter)


def test_trace_sink(_record):
    pass


def success(action_id, *, cursor=7):
    return {
        "status": "boundary",
        "records": [{"event": "terminal", "id": action_id,
                     "status": "completed", "release": {"verified": True}}],
        "cursor": cursor,
        "authority": "none",
        "acknowledgement": "not implied",
        "command_receipt": {"request_id": action_id, "replayed": False,
                            "state": "stdin_flushed"},
    }


class TargetSocketSubmitTests(unittest.TestCase):
    def command(self, identifier="A1-select-conveyor"):
        return {"op": "submit", "id": identifier,
                "expected_sequence": 5, "steps": [{"op": "observe"}]}

    def test_submitter_cannot_be_constructed_without_explicit_trace_sink(self):
        with self.assertRaises(TypeError):
            TargetSocketSubmitter("/tmp/unused.sock")
        with self.assertRaisesRegex(ValueError, "pre-send trace sink"):
            TargetSocketSubmitter("/tmp/unused.sock", trace_sink=None)

    def test_jsonl_sink_fsyncs_trace_and_refuses_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "socket-trace.jsonl"
            with JsonlTraceSink(path) as sink:
                submitter = TargetSocketSubmitter("/tmp/unused.sock",
                                                  trace_sink=sink)
                submitter._exchange = lambda request: success(
                    request["action_id"])
                submitter(self.command())

            lines = path.read_text(encoding="utf-8").splitlines()
            records = [json.loads(line) for line in lines]
            self.assertEqual([record["event"] for record in records], [
                "submit_prepared", "socket_response"])
            self.assertEqual(records[0]["request"]["command"], self.command())
            self.assertEqual(records[1]["response"]["records"][0]["release"],
                             {"verified": True})
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                JsonlTraceSink(path)
            self.assertEqual(path.read_bytes(), before)

    def test_sends_v2_action_scope_and_returns_release_receipt(self):
        sent = []
        submitter = TargetSocketSubmitter("/tmp/unused.sock", after=3,
                                          trace_sink=test_trace_sink)

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
        submitter = TargetSocketSubmitter("/tmp/unused.sock",
                                          trace_sink=test_trace_sink)
        submitter._exchange = lambda request: calls.append(request) or {
            "status": "unattributed_rejection", "records": [
                {"event": "rejected", "reason": "bad command"}], "cursor": 1,
            "authority": "none", "acknowledgement": "not implied",
            "command_receipt": {"request_id": request["request_id"],
                                    "replayed": False,
                                    "state": "stdin_flushed"}}

        with self.assertRaisesRegex(SocketSubmitStop, "terminal action boundary"):
            submitter(self.command())
        self.assertEqual(submitter.trace_events[-1]["event"], "socket_response")
        self.assertEqual(submitter.trace_events[-1]["response"]["records"][0]["event"],
                         "rejected")
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
                submitter = TargetSocketSubmitter("/tmp/unused.sock",
                                                  trace_sink=test_trace_sink)
                submitter._exchange = lambda _request, value=response: value
                with self.assertRaises(SocketSubmitStop):
                    submitter(self.command())

    def test_authority_and_acknowledgement_metadata_must_remain_non_authorizing(self):
        for field, value in (("authority", "input_allowed"),
                             ("acknowledgement", "accepted")):
            with self.subTest(field=field):
                response = success("A1-select-conveyor") | {field: value}
                submitter = TargetSocketSubmitter("/tmp/unused.sock",
                                                  trace_sink=test_trace_sink)
                submitter._exchange = lambda _request: response
                with self.assertRaisesRegex(SocketSubmitStop, "non-authorizing"):
                    submitter(self.command())

    def test_unix_wire_exchange_serializes_one_json_line_and_parses_response(self):
        wire_response = json.dumps(success("A1-select-conveyor")).encode() + b"\n"

        class FakeSocket:
            def __init__(self):
                self.sent = bytearray()
                self.chunks = [wire_response]
                self.connected = None
                self.timeout = None
                self.closed = False

            def __enter__(self): return self
            def __exit__(self, *_args): self.closed = True
            def settimeout(self, value): self.timeout = value
            def connect(self, path): self.connected = path
            def sendall(self, payload): self.sent.extend(payload)
            def recv(self, _size): return self.chunks.pop(0) if self.chunks else b""

        fake = FakeSocket()
        submitter = TargetSocketSubmitter("/tmp/test.sock", timeout_s=2,
                                          trace_sink=test_trace_sink)
        with patch("target_socket_submit_v1.socket.AF_UNIX", 1, create=True), \
                patch("target_socket_submit_v1.socket.socket",
                      return_value=fake) as factory:
            response = submitter._exchange({"after": 3, "command": self.command()})

        factory.assert_called_once()
        request = json.loads(fake.sent.decode("utf-8"))
        self.assertTrue(fake.sent.endswith(b"\n"))
        self.assertEqual(fake.connected, "/tmp/test.sock")
        self.assertEqual(fake.timeout, 3.0)
        self.assertTrue(fake.closed)
        self.assertEqual(request, {"after": 3, "command": self.command()})
        self.assertEqual(response, success("A1-select-conveyor"))

    def test_transport_exception_consumes_action_without_retry(self):
        calls = []
        journal = []
        submitter = TargetSocketSubmitter("/tmp/unused.sock", trace_sink=journal.append)

        def lost_response(_request):
            calls.append(1)
            raise TimeoutError("response lost")

        submitter._exchange = lost_response
        with self.assertRaisesRegex(SocketSubmitStop, "outcome unknown"):
            submitter(self.command())
        with self.assertRaisesRegex(SocketSubmitStop, "already consumed"):
            submitter(self.command())
        self.assertEqual(calls, [1])
        self.assertEqual([row["event"] for row in journal], [
            "submit_prepared", "transport_outcome_unknown"])

    def test_journal_precedes_exchange_and_preserves_response(self):
        order = []
        journal = []
        submitter = TargetSocketSubmitter("/tmp/unused.sock",
                                          trace_sink=lambda row: (
                                              journal.append(row),
                                              order.append("journal:" + row["event"])))

        def exchange(request):
            order.append("exchange")
            self.assertEqual(journal[0]["event"], "submit_prepared")
            self.assertEqual(journal[0]["request"], request)
            return success(request["action_id"])

        submitter._exchange = exchange
        submitter(self.command())

        self.assertEqual(order, ["journal:submit_prepared", "exchange",
                                 "journal:socket_response"])
        self.assertEqual(journal[1]["response"], success("A1-select-conveyor"))
        self.assertEqual([row["event"] for row in submitter.trace_events], [
            "submit_prepared", "socket_response"])

    def test_pre_send_journal_failure_stops_before_exchange(self):
        exchanges = []

        def fail_sink(_record):
            raise OSError("journal unavailable")

        submitter = TargetSocketSubmitter("/tmp/unused.sock", trace_sink=fail_sink)
        submitter._exchange = lambda request: exchanges.append(request)
        with self.assertRaisesRegex(SocketSubmitStop, "trace sink failed"):
            submitter(self.command())
        with self.assertRaisesRegex(SocketSubmitStop, "already consumed"):
            submitter(self.command())
        self.assertEqual(exchanges, [])

    def test_nonadvancing_cursor_is_not_a_terminal_receipt(self):
        submitter = TargetSocketSubmitter("/tmp/unused.sock", after=8,
                                          trace_sink=test_trace_sink)
        submitter._exchange = lambda request: success(request["action_id"], cursor=8)
        with self.assertRaisesRegex(SocketSubmitStop, "advancing socket event cursor"):
            submitter(self.command())

    def test_task_wrapper_selects_v2_bridge_and_receipt_child(self):
        source = (Path(__file__).with_name("mindustry_three_arm_socket_v2.py")
                  .read_text(encoding="utf-8"))
        self.assertIn("import stopped_socket_v2 as bridge", source)
        self.assertIn("mindustry_three_arm_interactive_v1.py", source)
        self.assertIn("bridge.main()", source)

    def test_dispatch_compiler_composes_with_socket_submit_adapter(self):
        coordinator = ArmCoordinator("plain")
        def observation(sequence):
            return {"sequence": sequence, "pointer_binding": {
                "surface": 91, "geometry": [0, 24, 1280, 760]}}
        candidate = {"op": "target_reference",
                     "point_space": "source_observation_pixels",
                     "points": [{"x": 150, "y": 220}, {"x": 640, "y": 410}],
                     "motion_model": "surface_origin_translation",
                     "confidence_basis": "visually_unambiguous"}
        coordinator.resolve(observation(1), 1280, 760,
                            [{"row": 0, "column": 0, "point": [150, 220]}],
                            lambda _image: candidate)
        sequence = {"value": 1}
        fresh = iter((observation(2), observation(3)))
        submitter = TargetSocketSubmitter("/tmp/unused.sock",
                                          trace_sink=test_trace_sink)
        wire_requests = []

        def exchange(request):
            wire_requests.append(request)
            return success(request["action_id"], cursor=request["after"] + 1)

        submitter._exchange = exchange

        def observe():
            value = next(fresh)
            sequence["value"] = value["sequence"]
            return value

        def receipt(locator, target):
            dependency = [{"sequence": 1, "box": [8, 8, 24, 24]}]
            if target == "palette_point":
                return build_palette_receipt(locator,
                    exact_dependencies=dependency)
            return build_world_receipt(locator,
                exact_dependencies=dependency,
                selection_baseline_sequence=1,
                selection_receipt_sequence=2,
                selection_box=[88, 8, 104, 24], minimum_changed_pixels=16)

        result = dispatch_task_targets(
            coordinator=coordinator, task_id="A1", layout="A",
            observe=observe,
            read_clock=lambda: {"sequence": sequence["value"],
                                "runtime_ns": 100 + sequence["value"]},
            build_receipt=receipt, submit=submitter)

        self.assertEqual([row["target"] for row in result],
                         ["palette_point", "target_point"])
        self.assertEqual([row["execution_receipt"] for row in result], [
            {"request_id": "A1-select-conveyor", "terminal": True,
             "released": True},
            {"request_id": "A1-place-conveyor", "terminal": True,
             "released": True},
        ])
        self.assertEqual([row["action_id"] for row in wire_requests], [
            "A1-select-conveyor", "A1-place-conveyor"])


if __name__ == "__main__":
    unittest.main()
