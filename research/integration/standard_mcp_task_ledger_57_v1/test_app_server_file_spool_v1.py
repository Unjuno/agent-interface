import json
import hashlib
from pathlib import Path
import tempfile
import threading
import time
import unittest

from app_server_file_spool_v1 import (
    FileSpoolPlanner,
    SpoolError,
    SpoolOutcomeUnknown,
    claim_next,
    publish_request,
    publish_stage,
    wait_for_stage,
)


class AppServerFileSpoolTests(unittest.TestCase):
    schema = {"type": "object", "required": ["tool"]}
    schema_sha256 = hashlib.sha256(json.dumps(schema, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.image = self.root / "attempts" / "attempt-1" / "frame.png"
        self.image.parent.mkdir(parents=True)
        self.image.write_bytes(b"PNG test fixture")

    def tearDown(self):
        self.temp.cleanup()

    def publish(self, attempt_id="attempt-1"):
        return publish_request(
            self.root,
            attempt_id=attempt_id,
            prompt="Choose one registered tool call.",
            output_schema=self.schema,
            image_path=self.image,
            model="gpt-6.1-sol",
            effort="medium",
        )

    def test_request_is_atomic_claimed_once_and_timeout_is_unknown(self):
        self.publish()
        request_path = self.root / "requests" / "attempt-1.json"
        self.assertEqual(json.loads(request_path.read_text())["attempt_id"], "attempt-1")
        self.assertEqual(list((self.root / "requests").glob("*.tmp")), [])

        claimed = claim_next(self.root, expected_model="gpt-6.1-sol",
            expected_effort="medium", expected_schema_sha256=self.schema_sha256)
        self.assertEqual(claimed["attempt_id"], "attempt-1")
        self.assertEqual(claimed["_image_path"], str(self.image.resolve()))
        self.assertIsNone(claim_next(self.root, expected_model="gpt-6.1-sol",
            expected_effort="medium", expected_schema_sha256=self.schema_sha256))

        with self.assertRaises(SpoolOutcomeUnknown) as raised:
            wait_for_stage(self.root, "attempt-1", "started", timeout=0.01)
        self.assertEqual(raised.exception.outcome, "UNKNOWN")
        with self.assertRaises(FileExistsError):
            self.publish()
        self.assertTrue((self.root / "inflight" / "attempt-1.json").is_file())
        self.assertFalse(request_path.exists())

    def test_start_and_completion_receipts_are_distinct_and_immutable(self):
        self.publish()
        claim_next(self.root, expected_model="gpt-6.1-sol", expected_effort="medium",
            expected_schema_sha256=self.schema_sha256)
        publish_stage(self.root, "attempt-1", "started", {
            "thread_id": "thread-1", "turn_id": "turn-1"})
        publish_stage(self.root, "attempt-1", "completed", {
            "status": "completed", "answer": {"tool": "calc"},
            "usage": {"input_tokens": 3, "output_tokens": 2}})
        self.assertEqual(wait_for_stage(self.root, "attempt-1", "started", timeout=0.1)["turn_id"], "turn-1")
        result = wait_for_stage(self.root, "attempt-1", "completed", timeout=0.1)
        self.assertEqual(result["answer"], {"tool": "calc"})
        with self.assertRaises(FileExistsError):
            publish_stage(self.root, "attempt-1", "completed", {"status": "failed"})

    def test_request_rejects_external_images_and_bad_attempt_ids(self):
        outside = self.root.parent / "not-in-spool.png"
        outside.write_bytes(b"external")
        try:
            with self.assertRaises(ValueError):
                publish_request(self.root, attempt_id="attempt-1", prompt="p",
                    output_schema={"type": "object"}, image_path=outside,
                    model="gpt-6.1-sol", effort="medium")
            with self.assertRaises(ValueError):
                publish_request(self.root, attempt_id="../escape", prompt="p",
                    output_schema={"type": "object"}, image_path=self.image,
                    model="gpt-6.1-sol", effort="medium")
        finally:
            outside.unlink(missing_ok=True)

    def test_claim_rejects_image_mutation_without_requeue(self):
        self.publish()
        self.image.write_bytes(b"changed after request publication")
        with self.assertRaisesRegex(SpoolError, "image hash mismatch"):
            claim_next(self.root, expected_model="gpt-6.1-sol", expected_effort="medium",
                expected_schema_sha256=self.schema_sha256)
        self.assertIsNone(claim_next(self.root, expected_model="gpt-6.1-sol",
            expected_effort="medium", expected_schema_sha256=self.schema_sha256))
        self.assertTrue((self.root / "inflight" / "attempt-1.json").is_file())

    def test_claim_enforces_host_model_effort_and_schema_preregistration(self):
        self.publish()
        with self.assertRaisesRegex(SpoolError, "differs from host preregistration"):
            claim_next(self.root, expected_model="other-model", expected_effort="medium",
                expected_schema_sha256=self.schema_sha256)
        self.assertTrue((self.root / "inflight" / "attempt-1.json").is_file())
        self.assertIsNone(claim_next(self.root, expected_model="gpt-6.1-sol",
            expected_effort="medium", expected_schema_sha256=self.schema_sha256))

    def test_file_planner_joins_start_and_terminal_receipts(self):
        planner = FileSpoolPlanner(self.root, model="gpt-6.1-sol", effort="medium",
            expected_schema_sha256=self.schema_sha256, start_timeout=1)
        started = threading.Event()
        finish = threading.Event()
        failures = []

        def host_once():
            deadline = time.monotonic() + 1
            request = None
            while request is None and time.monotonic() < deadline:
                request = claim_next(self.root, expected_model="gpt-6.1-sol",
                    expected_effort="medium", expected_schema_sha256=self.schema_sha256)
                if request is None:
                    time.sleep(0.005)
            if request is None:
                failures.append("request was not published")
                return
            attempt_id = request["attempt_id"]
            publish_stage(self.root, attempt_id, "started", {
                "thread_id": "thread-live", "turn_id": "turn-live"})
            started.set()
            if not finish.wait(timeout=1):
                failures.append("consumer did not complete begin_turn")
                return
            publish_stage(self.root, attempt_id, "completed", {
                "thread_id": "thread-live", "turn_id": "turn-live",
                "status": "completed", "answer_eligible": True,
                "answer": {"tool": "interface_guarded_calc_compiled"},
                "usage": {"last": {"inputTokens": 20, "outputTokens": 7}},
                "error": None, "cancellation_requested": False,
                "completed_agent_messages": 1,
            })

        host = threading.Thread(target=host_once)
        host.start()
        handle = planner.begin_turn("Plan one action.", output_schema=self.schema,
            image_path=self.image)
        self.assertTrue(started.is_set())
        self.assertEqual((handle.thread_id, handle.turn_id), ("thread-live", "turn-live"))
        finish.set()
        result = planner.await_turn(handle, timeout=1)
        host.join(timeout=1)
        self.assertFalse(host.is_alive())
        self.assertEqual(failures, [])
        self.assertTrue(result.answer_eligible)
        self.assertEqual(result.answer["tool"], "interface_guarded_calc_compiled")

    def test_planner_start_timeout_cannot_admit_a_second_attempt(self):
        planner = FileSpoolPlanner(self.root, model="gpt-6.1-sol", effort="medium",
            expected_schema_sha256=self.schema_sha256, start_timeout=0.01)
        with self.assertRaises(SpoolOutcomeUnknown):
            planner.begin_turn("Plan one action.", output_schema=self.schema,
                image_path=self.image)
        with self.assertRaisesRegex(SpoolError, "unknown admission outcome"):
            planner.begin_turn("Do not replay.", output_schema=self.schema,
                image_path=self.image)

    def test_publish_bounds_prompt_and_image_size(self):
        with self.assertRaisesRegex(ValueError, "prompt exceeds"):
            publish_request(self.root, attempt_id="large-prompt", prompt="x" * 300_000,
                output_schema={"type": "object"}, image_path=self.image,
                model="gpt-6.1-sol", effort="medium")
        large = self.root / "attempts" / "large-image" / "frame.png"
        large.parent.mkdir(parents=True)
        large.write_bytes(b"x" * (25 * 1024 * 1024 + 1))
        with self.assertRaisesRegex(ValueError, "image exceeds"):
            publish_request(self.root, attempt_id="large-image", prompt="p",
                output_schema={"type": "object"}, image_path=large,
                model="gpt-6.1-sol", effort="medium")


if __name__ == "__main__":
    unittest.main()
