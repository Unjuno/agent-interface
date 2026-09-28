"""Host-only filesystem handshake tests for the private mod channel."""

import copy
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest

from private_benchmark_channel import (PrivateBenchmarkChannel,
                                       PrivateProtocolStop)
from test_private_reset_audit import evaluation, snapshot


def wait_for(path, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.005)
    raise TimeoutError(str(path))


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


class PrivateBenchmarkChannelTests(unittest.TestCase):
    def test_positive_score_reset_audit_then_next_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            before = snapshot()
            channel = PrivateBenchmarkChannel(root, timeout_s=2, poll_s=0.005)
            write_json(root / "before-1.json", before)
            (root / "ready-1.ack").write_text("ready", encoding="utf-8")
            self.assertEqual(channel.await_initial_ready(), before)

            def mod_side():
                wait_for(root / "checkpoint-1.request")
                after = copy.deepcopy(before)
                next(tile for tile in after["tiles"]
                     if (tile["x"], tile["y"]) == (137, 52)).update(
                         block="conveyor", team=1, rotation=1)
                after["copper"] -= 1
                write_json(root / "after-1.json", after)
                (root / "checkpoint-1.ack").write_text("checkpoint", encoding="utf-8")
                wait_for(root / "reset-1.request")
                reset = copy.deepcopy(before)
                reset["tick"] += 1
                write_json(root / "reset-1.json", reset)
                (root / "reset-1.ack").write_text("reset applied", encoding="utf-8")
                wait_for(root / "reset-1.verified")
                (root / "ready-2.ack").write_text("next ready", encoding="utf-8")

            worker = threading.Thread(target=mod_side, daemon=True)
            worker.start()
            channel.request_checkpoint()
            reset = channel.complete_task("A1", evaluation())
            worker.join(timeout=2)
            self.assertFalse(worker.is_alive())
            self.assertEqual(reset["tiles"], before["tiles"])
            self.assertEqual((channel.epoch, channel.phase), (2, "ready"))

    def test_failed_task_score_writes_no_reset_request(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            channel = PrivateBenchmarkChannel(root, timeout_s=2, poll_s=0.005)
            write_json(root / "before-1.json", snapshot())
            (root / "ready-1.ack").write_text("ready", encoding="utf-8")
            channel.await_initial_ready()

            def mod_side():
                wait_for(root / "checkpoint-1.request")
                write_json(root / "after-1.json", snapshot())
                (root / "checkpoint-1.ack").write_text("checkpoint", encoding="utf-8")

            worker = threading.Thread(target=mod_side, daemon=True)
            worker.start()
            channel.request_checkpoint()
            bad = evaluation()
            bad["status"] = "CONTRADICTED"
            bad["contract_satisfied"] = False
            with self.assertRaisesRegex(PrivateProtocolStop, "score; reset forbidden"):
                channel.complete_task("A1", bad)
            worker.join(timeout=2)
            self.assertTrue((root / "score-fail-1.receipt").is_file())
            self.assertFalse((root / "reset-1.request").exists())
            self.assertEqual(channel.phase, "stopped")

    def test_reset_audit_failure_withholds_next_task_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            before = snapshot()
            channel = PrivateBenchmarkChannel(root, timeout_s=2, poll_s=0.005)
            write_json(root / "before-1.json", before)
            (root / "ready-1.ack").write_text("ready", encoding="utf-8")
            channel.await_initial_ready()

            def mod_side():
                wait_for(root / "checkpoint-1.request")
                write_json(root / "after-1.json", before)
                (root / "checkpoint-1.ack").write_text("checkpoint", encoding="utf-8")
                wait_for(root / "reset-1.request")
                wrong = copy.deepcopy(before)
                wrong["copper"] += 10
                write_json(root / "reset-1.json", wrong)
                (root / "reset-1.ack").write_text("reset applied", encoding="utf-8")

            worker = threading.Thread(target=mod_side, daemon=True)
            worker.start()
            channel.request_checkpoint()
            with self.assertRaisesRegex(PrivateProtocolStop, "reset audit failed"):
                channel.complete_task("A1", evaluation())
            worker.join(timeout=2)
            self.assertTrue((root / "reset-1.fail").is_file())
            self.assertFalse((root / "reset-1.verified").exists())
            self.assertFalse((root / "ready-2.ack").exists())
            self.assertEqual(channel.phase, "stopped")


if __name__ == "__main__":
    unittest.main()
