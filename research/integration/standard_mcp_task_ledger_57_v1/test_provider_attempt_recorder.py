import json
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ledger import LedgerValidationError, summarize, validate_record
from provider_attempt_recorder import (
    AttemptJournalError,
    IncompleteProviderAttemptError,
    ProviderAttemptRecorder,
)


class ProviderAttemptRecorderTests(unittest.TestCase):
    def test_resolved_raw_directory_escape_is_rejected_before_write(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "run"
            outside = Path(temp) / "outside"
            root.mkdir()
            outside.mkdir()
            raw_path = root / "raw"
            original_resolve = Path.resolve

            def resolve_with_external_raw(path, strict=False):
                if path == raw_path:
                    return outside
                return original_resolve(path, strict=strict)

            with patch.object(Path, "resolve", autospec=True,
                              side_effect=resolve_with_external_raw):
                with self.assertRaises(AttemptJournalError):
                    ProviderAttemptRecorder(root)
            self.assertEqual(list(outside.iterdir()), [])

    def test_durable_start_precedes_call_and_raw_bytes_are_bound_to_result(self):
        with tempfile.TemporaryDirectory() as temp:
            ticks = iter((10, 20))
            recorder = ProviderAttemptRecorder(temp, clock_ns=lambda: next(ticks))

            def provider_call():
                rows = [json.loads(line) for line in
                        (Path(temp) / "attempts.jsonl").read_text().splitlines()]
                self.assertEqual(rows[0]["event"], "model_attempt_started")
                return {
                    "status": "completed",
                    "usage": {"status": "reported", "input_tokens": 17,
                              "output_tokens": 3},
                    "response_bytes": b'{"text":"use target"}',
                }

            recorder.invoke("attempt-01", b'{"prompt":"task"}', provider_call)
            result = recorder.reconcile()
            session_id = json.loads(
                (Path(temp) / "attempts.jsonl").read_text().splitlines()[0]
            )["session_id"]

            self.assertTrue(result["complete"])
            self.assertEqual(result["events"], [{
                "kind": "model_attempt",
                "seq": 1,
                "attempt_id": "attempt-01",
                "session_id": session_id,
                "status": "completed",
                "started_ns": 10,
                "ended_ns": 20,
                "usage": {"status": "reported", "input_tokens": 17,
                          "output_tokens": 3},
                "response_status": "raw_retained",
                "raw_refs": [
                    {"path": "raw/attempt-01.request.bin",
                     "sha256": hashlib.sha256(b'{"prompt":"task"}').hexdigest()},
                    {"path": "raw/attempt-01.response.bin",
                     "sha256": hashlib.sha256(b'{"text":"use target"}').hexdigest()},
                ],
            }])
            self.assertEqual(len(result["raw_refs"]), 2)
            self.assertEqual((Path(temp) / result["raw_refs"][0]["path"]).read_bytes(),
                             b'{"prompt":"task"}')
            self.assertEqual((Path(temp) / result["raw_refs"][1]["path"]).read_bytes(),
                             b'{"text":"use target"}')

    def test_unfinished_started_attempt_cannot_be_reconciled_as_zero_calls(self):
        with tempfile.TemporaryDirectory() as temp:
            recorder = ProviderAttemptRecorder(temp, clock_ns=lambda: 10)
            recorder.begin("attempt-01", b'{"prompt":"task"}')

            with self.assertRaises(IncompleteProviderAttemptError):
                recorder.reconcile()

    def test_timeout_is_retained_with_unknown_usage_and_no_response(self):
        with tempfile.TemporaryDirectory() as temp:
            ticks = iter((10, 30))
            recorder = ProviderAttemptRecorder(temp, clock_ns=lambda: next(ticks))

            def provider_call():
                raise TimeoutError("transport timed out")

            with self.assertRaises(TimeoutError):
                recorder.invoke("attempt-01", b'{"prompt":"task"}', provider_call)

            result = recorder.reconcile()
            self.assertEqual(result["events"][0]["status"], "timeout")
            self.assertEqual(result["events"][0]["usage"], {
                "status": "unavailable", "input_tokens": None,
                "output_tokens": None,
            })
            self.assertEqual(len(result["raw_refs"]), 1)
            totals = summarize([{**result["events"][0], "seq": 1}])
            self.assertIsNone(totals["input_tokens"])
            self.assertEqual(totals["usage_status"], "incomplete")

    def test_partial_usage_stays_incomplete_in_shared_ledger_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            ticks = iter((10, 20))
            recorder = ProviderAttemptRecorder(temp, clock_ns=lambda: next(ticks))
            recorder.invoke("attempt-01", b"request", lambda: {
                "status": "completed",
                "usage": {"status": "partial", "input_tokens": 17,
                          "output_tokens": None},
                "response_bytes": b"response",
            })

            event = {**recorder.reconcile()["events"][0], "seq": 1}
            totals = summarize([event])
            self.assertIsNone(totals["input_tokens"])
            self.assertIsNone(totals["output_tokens"])
            self.assertEqual(totals["usage_status"], "incomplete")

    def test_attempt_id_joins_the_provider_generation_to_mcp_tool_calls(self):
        with tempfile.TemporaryDirectory() as temp:
            ticks = iter((10, 20, 21, 22))
            recorder = ProviderAttemptRecorder(temp, clock_ns=lambda: next(ticks))
            recorder.invoke("generation-01", b"request", lambda: {
                "status": "completed",
                "usage": {"status": "reported", "input_tokens": 11,
                          "output_tokens": 2},
                "response_bytes": b"tool call: interface_guarded_compiled",
            })
            tool_result = {"status": "completed", "task_success": True}
            tool_result_bytes = json.dumps(tool_result, sort_keys=True,
                                           separators=(",", ":")).encode("utf-8")

            def call_tool():
                rows = [json.loads(line) for line in
                        (Path(temp) / "attempts.jsonl").read_text().splitlines()]
                self.assertTrue(any(row.get("event") == "tool_call_started" and
                                    row.get("call_id") == "mcp-01" for row in rows))
                return {"result": tool_result,
                        "response_bytes": tool_result_bytes}

            recorder.invoke_tool(
                "generation-01", "mcp-01", "interface_guarded_compiled",
                b'{"method":"interface_guarded_compiled"}', call_tool,
            )
            receipt = recorder.reconcile()
            events = receipt["events"]

            summary = validate_record({
                "schema": "agent-interface/standard-mcp-task-ledger-v1",
                "run_id": "run-01",
                "comparison": {"arm": "integrated", "block": 1,
                               "order": 1, "task_seed": "seed-01"},
                "task": {"task_id": "task-01", "fixture_sha256": "a" * 64,
                         "scorer_sha256": "b" * 64},
                "source": {"commit": "c" * 40, "route_sha256": "d" * 64},
                "environment_sha256": "e" * 64,
                "model": {"id": "model-x", "effort": "low",
                          "request_config_sha256": "f" * 64},
                "raw_refs": receipt["raw_refs"],
                "events": events,
            })
            self.assertEqual(summary["model_attempt_count"], 1)
            self.assertEqual(summary["tool_call_count"], 1)
            self.assertEqual(summary["input_tokens"], 11)
            self.assertIsNone(summary["task_success"])
            self.assertEqual(events[1]["response_status"], "matched")

    def test_overlapping_attempts_reconcile_in_start_order(self):
        with tempfile.TemporaryDirectory() as temp:
            ticks = iter((10, 20, 30, 40))
            recorder = ProviderAttemptRecorder(temp, clock_ns=lambda: next(ticks))
            recorder.begin("generation-01", b"request-1")
            recorder.begin("generation-02", b"request-2")
            usage = {"status": "unavailable", "input_tokens": None,
                     "output_tokens": None}

            recorder.finish("generation-02", status="completed", usage=usage,
                            response_bytes=b"response-2")
            recorder.finish("generation-01", status="timeout", usage=usage)

            events = recorder.reconcile()["events"]
            self.assertEqual([event["attempt_id"] for event in events],
                             ["generation-01", "generation-02"])

    def test_changed_raw_response_invalidates_reconciliation(self):
        with tempfile.TemporaryDirectory() as temp:
            ticks = iter((10, 20))
            recorder = ProviderAttemptRecorder(temp, clock_ns=lambda: next(ticks))
            recorder.invoke("attempt-01", b"request", lambda: {
                "status": "completed",
                "usage": {"status": "reported", "input_tokens": 1,
                          "output_tokens": 1},
                "response_bytes": b"response",
            })
            (Path(temp) / "raw" / "attempt-01.response.bin").write_bytes(b"changed")

            with self.assertRaises(AttemptJournalError):
                recorder.reconcile()

    def test_malformed_provider_usage_is_preserved_as_unknown(self):
        with tempfile.TemporaryDirectory() as temp:
            ticks = iter((10, 20))
            recorder = ProviderAttemptRecorder(temp, clock_ns=lambda: next(ticks))
            recorder.invoke("attempt-01", b"request", lambda: {
                "status": "completed",
                "usage": {"status": "reported", "input_tokens": "many",
                          "output_tokens": 1},
                "response_bytes": b"response",
            })

            event = recorder.reconcile()["events"][0]
            self.assertEqual(event["status"], "malformed")
            self.assertEqual(event["usage"], {
                "status": "unavailable", "input_tokens": None,
                "output_tokens": None,
            })

    def test_mcp_timeout_is_retained_without_independent_task_success(self):
        with tempfile.TemporaryDirectory() as temp:
            ticks = iter((10, 20, 21, 22))
            recorder = ProviderAttemptRecorder(temp, clock_ns=lambda: next(ticks))
            recorder.invoke("generation-01", b"request", lambda: {
                "status": "completed",
                "usage": {"status": "reported", "input_tokens": 8,
                          "output_tokens": 2},
                "response_bytes": b"generation response",
            })

            def call_tool():
                raise TimeoutError("MCP transport timed out")

            with self.assertRaises(TimeoutError):
                recorder.invoke_tool(
                    "generation-01", "mcp-01", "interface_guarded_compiled",
                    b"tool request", call_tool,
                )

            receipt = recorder.reconcile()
            totals = summarize(receipt["events"])
            self.assertEqual(receipt["events"][1]["result"], {
                "status": "raised", "exception_type": "TimeoutError",
            })
            self.assertEqual(receipt["events"][1]["response_status"], "unavailable")
            self.assertIsNone(totals["task_success"])

    def test_unfinished_tool_call_blocks_reconciliation_and_new_session(self):
        with tempfile.TemporaryDirectory() as temp:
            ticks = iter((10, 20, 21, 30))
            recorder = ProviderAttemptRecorder(temp, clock_ns=lambda: next(ticks))
            recorder.invoke("generation-01", b"request", lambda: {
                "status": "completed",
                "usage": {"status": "unavailable", "input_tokens": None,
                          "output_tokens": None},
                "response_bytes": b"generation response",
            })
            recorder.begin_tool_call("generation-01", "mcp-01",
                                     "interface_guarded_compiled", b"tool request")

            with self.assertRaises(IncompleteProviderAttemptError):
                recorder.reconcile()
            restarted = ProviderAttemptRecorder(temp, clock_ns=lambda: 30)
            with self.assertRaises(IncompleteProviderAttemptError):
                restarted.begin("generation-02", b"another request")

    def test_raw_tool_response_mismatch_is_visible_in_reconciled_event(self):
        with tempfile.TemporaryDirectory() as temp:
            ticks = iter((10, 20, 21, 22))
            recorder = ProviderAttemptRecorder(temp, clock_ns=lambda: next(ticks))
            recorder.invoke("generation-01", b"request", lambda: {
                "status": "completed",
                "usage": {"status": "unavailable", "input_tokens": None,
                          "output_tokens": None},
                "response_bytes": b"generation response",
            })
            recorder.invoke_tool(
                "generation-01", "mcp-01", "interface_guarded_compiled",
                b"tool request", lambda: {
                    "result": {"status": "completed"},
                    "response_bytes": b'{"status":"different"}',
                },
            )

            receipt = recorder.reconcile()
            self.assertEqual(receipt["events"][1]["response_status"], "mismatch")
            with self.assertRaises(LedgerValidationError):
                summarize(receipt["events"])

    def test_a_new_recorder_cannot_resume_or_skip_an_unfinished_attempt(self):
        with tempfile.TemporaryDirectory() as temp:
            first = ProviderAttemptRecorder(temp, clock_ns=lambda: 10)
            first.begin("attempt-01", b"request")
            after_restart = ProviderAttemptRecorder(temp, clock_ns=lambda: 20)

            with self.assertRaises(IncompleteProviderAttemptError):
                after_restart.begin("attempt-02", b"another request")


if __name__ == "__main__":
    unittest.main()
