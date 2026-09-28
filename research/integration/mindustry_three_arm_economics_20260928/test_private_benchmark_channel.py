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
from raw_lifecycle_adapter import attach_private_lifecycle
from raw_allocation_audit_v2 import RawAuditError, reconstruct as reconstruct_v2
from test_raw_allocation_audit_v2 import raw_v2
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


def ns_values(value):
    if type(value) is dict:
        for key, item in value.items():
            if key.endswith("_ns") and type(item) is int:
                yield item
            else:
                yield from ns_values(item)
    elif type(value) is list:
        for item in value:
            yield from ns_values(item)


def run_complete_fake_channel(root: Path, arm: str) -> dict:
    root.mkdir()
    initial = snapshot()
    channel = PrivateBenchmarkChannel(root, timeout_s=2, poll_s=0.005)
    write_json(root / "before-1.json", initial)
    (root / "ready-1.ack").write_text("ready", encoding="utf-8")

    def mod_side():
        for epoch in range(1, 7):
            wait_for(root / f"checkpoint-{epoch}.request")
            state = copy.deepcopy(initial)
            state["tick"] += epoch
            write_json(root / f"after-{epoch}.json", state)
            (root / f"checkpoint-{epoch}.ack").write_text("checkpoint", encoding="utf-8")
            wait_for(root / f"reset-{epoch}.request")
            reset = copy.deepcopy(initial)
            reset["tick"] += epoch
            write_json(root / f"reset-{epoch}.json", reset)
            (root / f"reset-{epoch}.ack").write_text("reset", encoding="utf-8")
            wait_for(root / f"reset-{epoch}.verified")
            if epoch == 3:
                (root / "geometry-4.request").write_text("geometry", encoding="utf-8")
                wait_for(root / "geometry-4.receipt")
            if epoch < 6:
                (root / f"ready-{epoch + 1}.ack").write_text("ready", encoding="utf-8")

    worker = threading.Thread(target=mod_side, daemon=True)
    worker.start()
    channel.await_initial_ready()
    for epoch, task_id in enumerate(("A1", "A2", "A3", "B1", "B2", "B3"), 1):
        channel.request_checkpoint()
        # The synthetic raw task events carry millisecond-scale offsets; leave
        # an explicit host interval before the independent score timestamp.
        time.sleep(0.01)
        channel.complete_task(task_id, evaluation())
        if epoch == 3:
            channel.release_geometry_transition(
                {"surface": 91, "geometry": [0, 24, 1280, 760]},
                {"surface": 91, "geometry": [0, 24, 1216, 760]})
    worker.join(timeout=2)
    if worker.is_alive():
        raise TimeoutError("fake private mod did not complete the six-task handshake")
    return channel.raw_lifecycle_events(arm)


def assemble_raw_from_private_channels(root: Path) -> dict:
    evidence = {arm: run_complete_fake_channel(root / arm, arm)
                for arm in ("plain", "ephemeral", "persistent")}
    raw = raw_v2()
    for arm, rows in evidence.items():
        for index, task_id in enumerate(("A1", "A2", "A3", "B1", "B2", "B3")):
            task = raw["arms"][arm][index]
            old_start = task["started_ns"]
            new_start = rows["task_started_ns"][index + 1]
            shift = new_start - old_start

            def shift_times(value):
                if type(value) is dict:
                    return {key: (item + shift if key.endswith("_ns")
                        and type(item) is int else shift_times(item))
                        for key, item in value.items()}
                if type(value) is list:
                    return [shift_times(item) for item in value]
                return value

            raw["arms"][arm][index] = shift_times(task)
            raw["arms"][arm][index]["ended_ns"] = max(
                rows["score_checked_ns"][task_id],
                *ns_values(raw["arms"][arm][index])) + 1
        raw = attach_private_lifecycle(raw, arm, rows)
    return raw


class PrivateBenchmarkChannelTests(unittest.TestCase):
    def test_raw_adapter_refuses_incomplete_private_lifecycle_evidence(self):
        with self.assertRaisesRegex(RawAuditError, "exact private lifecycle"):
            attach_private_lifecycle(raw_v2(), "plain", {})

    def test_complete_six_task_handshake_exports_raw_auditor_lifecycle_events(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = assemble_raw_from_private_channels(Path(directory))

            for arm in ("plain", "ephemeral", "persistent"):
                for task in raw["arms"][arm]:
                    observations = task["observation_events"]
                    self.assertEqual([row["capture_ns"] for row in observations],
                        sorted(row["capture_ns"] for row in observations), arm)
                    self.assertEqual(len({row["sequence"] for row in observations}),
                        len(observations), arm)
                    self.assertTrue(all(task["started_ns"] <= row["capture_ns"]
                        <= task["ended_ns"] for row in observations),
                        (arm, task["task_id"], task["started_ns"],
                         task["ended_ns"], observations))
            trace = reconstruct_v2(raw)
            self.assertEqual(len(trace["arms"]["plain"]), 6)
            self.assertEqual(len(trace["arms"]["persistent"]), 6)
            self.assertEqual(len(trace["arms"]["persistent"][3]["model_calls"]), 1)

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
