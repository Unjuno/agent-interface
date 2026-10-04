"""Host-only filesystem handshake tests for the private mod channel."""

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from private_benchmark_channel import (PrivateBenchmarkChannel,
                                       PrivateProtocolStop)
from arm_coordinator import ArmCoordinator
from raw_lifecycle_adapter import attach_private_lifecycle
from raw_allocation_audit_v2 import RawAuditError, reconstruct as reconstruct_v2
from target_execution_v1 import dispatch_task_targets
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
    coordinator = ArmCoordinator(arm)
    model_sequences = []
    dispatch_capture = []
    for epoch, task_id in enumerate(("A1", "A2", "A3", "B1", "B2", "B3"), 1):
        layout = "A" if epoch <= 3 else "B"
        width = 1280 if layout == "A" else 1216
        source = {"sequence": epoch * 10,
            "pointer_binding": {"surface": 91,
                "geometry": [0, 24, width, 760]}}
        def model_call(_observation):
            model_sequences.append(epoch)
            return {"op": "target_reference",
                "point_space": "source_observation_pixels",
                "points": [{"x": 150, "y": 220}, {"x": 640, "y": 410}],
                "motion_model": "surface_origin_translation",
                "confidence_basis": "visually_unambiguous"}
        old_reference_sequence = (coordinator.cached.source_sequence
                                  if coordinator.cached is not None else None)
        routed = coordinator.resolve(source, width, 760,
            [{"row": 0, "column": 0, "point": [150, 220]}], model_call)
        if routed["task"].task_id != task_id:
            raise AssertionError("coordinator task differs from private epoch")

        sequences = {"value": source["sequence"]}
        dispatch_observations = []

        def observe():
            sequences["value"] += 1
            row = {"sequence": sequences["value"],
                   "pointer_binding": source["pointer_binding"]}
            dispatch_observations.append(copy.deepcopy(row))
            return row

        def compile_request(locator, _clock, current_task, target, _receipt):
            return {"id": f"{current_task}-{target}", "target": target,
                    "expected_sequence": locator["validated_sequence"]}

        with patch("target_execution_v1.compile_receipt_target_click",
                   side_effect=compile_request):
            target_results = dispatch_task_targets(
                coordinator=coordinator, task_id=task_id, layout=layout,
                observe=observe,
                read_clock=lambda: {"sequence": sequences["value"],
                                    "runtime_ns": 1_000_000 + sequences["value"]},
                build_receipt=lambda _locator, target: {"target": target},
                submit=lambda request: {"request_id": request["id"],
                                        "terminal": True, "released": True})
        if ([row["target"] for row in target_results]
                != ["palette_point", "target_point"]):
            raise AssertionError("two ordered target dispatches required per task")
        if [row["locator"]["validated_sequence"] for row in target_results] != [
                epoch * 10 + 1, epoch * 10 + 2]:
            raise AssertionError("target dispatches must bind distinct fresh observations")
        if arm == "persistent" and layout == "B" and epoch == 4:
            if (routed["record"]["old_reference_status"] != "stale"
                    or routed["record"]["old_reference_pointer_admissions"] != 0
                    or old_reference_sequence is None):
                raise AssertionError("A3→B1 old reference must refuse before repair")
        dispatch_capture.append({"task_id": task_id, "layout": layout,
            "route_record": copy.deepcopy(routed["record"]),
            "source_sequence": source["sequence"],
            "source_observation": copy.deepcopy(source),
            "dispatch_observations": dispatch_observations,
            "old_reference_sequence": old_reference_sequence,
            "target_results": copy.deepcopy(target_results)})
        channel.request_checkpoint()
        # The synthetic raw task events carry millisecond-scale offsets; leave
        # an explicit host interval before the independent score timestamp.
        time.sleep(0.01)
        coordinator.score(True)
        channel.complete_task(task_id, evaluation())
        coordinator.reset(True)
        coordinator.advance()
        if epoch == 3:
            channel.release_geometry_transition(
                {"surface": 91, "geometry": [0, 24, 1280, 760]},
                {"surface": 91, "geometry": [0, 24, 1216, 760]})
    worker.join(timeout=2)
    if worker.is_alive():
        raise TimeoutError("fake private mod did not complete the six-task handshake")
    expected_calls = 6 if arm in {"plain", "ephemeral"} else 2
    if len(model_sequences) != expected_calls:
        raise AssertionError("coordinator model-call count differs from frozen arm")
    if coordinator.lifecycle.phase != "complete":
        raise AssertionError("coordinator did not complete the frozen arm")
    return {"lifecycle": channel.raw_lifecycle_events(arm),
            "dispatch_capture": dispatch_capture}


def assemble_raw_from_private_channels(root: Path,
                                       dispatch_output: Path | None = None) -> dict:
    capture = {arm: run_complete_fake_channel(root / arm, arm)
               for arm in ("plain", "ephemeral", "persistent")}
    raw = raw_v2()
    for arm, captured in capture.items():
        rows = captured["lifecycle"]
        for index, task_id in enumerate(("A1", "A2", "A3", "B1", "B2", "B3")):
            task = raw["arms"][arm][index]
            dispatch = captured["dispatch_capture"][index]
            route_record = dispatch["route_record"]
            if (route_record["task_id"] != task_id
                    or route_record["layout"] != task["layout"]
                    or route_record["route"] != task["route"]
                    or route_record["model_calls"] != len(task["model_call_events"])):
                raise AssertionError("composed route differs from frozen raw task")

            source_sequence = dispatch["source_sequence"]
            if task["model_call_events"]:
                source_hash = task["model_call_events"][0]["image_sha256"]
                task["model_call_events"][0]["source_sequence"] = source_sequence
            else:
                source_hash = task["observation_events"][0]["image_sha256"]
            task["observation_events"] = [{
                "sequence": source_sequence,
                "capture_ns": task["started_ns"] + 100,
                "image_sha256": source_hash,
                "model_visible": bool(task["model_call_events"]),
            }]
            for capture_index, observation in enumerate(
                    dispatch["dispatch_observations"], start=1):
                task["observation_events"].append({
                    "sequence": observation["sequence"],
                    "capture_ns": task["started_ns"] + 100 + capture_index * 100,
                    "image_sha256": hashlib.sha256(
                        f"{arm}/{task_id}/dispatch-{capture_index}".encode()).hexdigest(),
                    "model_visible": False,
                })

            attempts, feedback, releases = [], [], []
            if route_record["old_reference_status"] is not None:
                if arm != "persistent" or index != 3:
                    raise AssertionError("only persistent B1 may refuse an old reference")
                attempts.append({"attempt_id": f"{arm}-{task_id}-old-reference",
                    "status": "REFUSED", "old_reference": True,
                    "admission_ns": None})
                repair = task["repair_events"][0]
                repair.update({"old_reference_status": route_record["old_reference_status"],
                    "old_reference_sequence": dispatch["old_reference_sequence"],
                    "observed_sequence": source_sequence,
                    "fresh_source_sequence": source_sequence})

            for target_index, result in enumerate(dispatch["target_results"]):
                target = result["target"]
                request = result["request"]
                expected_target = ("palette_point" if target_index == 0
                                   else "target_point")
                if (target != expected_target
                        or request.get("target") != expected_target
                        or request.get("expected_sequence")
                           != result["locator"]["validated_sequence"]
                        or result["execution_receipt"] != {
                            "request_id": request["id"], "terminal": True,
                            "released": True}):
                    raise AssertionError("dispatch evidence failed request/receipt join")
                attempt_id = f"{arm}-{task_id}-{target}"
                admission_ns = task["started_ns"] + 1_000 + target_index * 500
                attempts.append({"attempt_id": attempt_id, "status": "ADMITTED",
                    "old_reference": False, "admission_ns": admission_ns})
                feedback.append({"attempt_id": attempt_id,
                                 "observed_ns": admission_ns + 100})
                releases.append({"attempt_id": attempt_id,
                    "released_ns": admission_ns + 200, "button_up": True,
                    "keys_empty": True,
                    "receipt_id": "release-" + request["id"]})
            task["input_events"] = attempts
            task["input_feedback_events"] = feedback
            task["release_events"] = releases

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
    if dispatch_output is not None:
        dispatch_output.parent.mkdir(parents=True, exist_ok=True)
        dispatch_output.write_text(json.dumps({
            "schema": "mindustry_target_dispatch_capture_v1",
            "arms": {arm: captured["dispatch_capture"]
                     for arm, captured in capture.items()},
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
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
            for arm in ("plain", "ephemeral", "persistent"):
                for task in raw["arms"][arm]:
                    admitted = [row for row in task["input_events"]
                                if row["status"] == "ADMITTED"]
                    self.assertEqual(len(admitted), 2, (arm, task["task_id"]))
                    self.assertEqual(len(task["release_events"]), 2,
                                     (arm, task["task_id"]))
                    self.assertTrue(all(row["button_up"] and row["keys_empty"]
                                        for row in task["release_events"]))
                    if arm == "persistent" and task["task_id"] == "B1":
                        refused = [row for row in task["input_events"]
                                   if row["status"] == "REFUSED"]
                        self.assertEqual(len(refused), 1)
                        self.assertTrue(refused[0]["old_reference"])

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
