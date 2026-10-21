"""Construction-only cross-layer schedule using exact current-main functions.

No Doom, GUI, OS input, App Server, or model is started. The production AST
helpers, adapter, source-refresh function, and temporal-sheet/model-input
functions are exercised against inert queue/client doubles.
"""
import ast
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import queue
import tempfile
import threading
import time
import unittest
from pathlib import Path
from textwrap import indent

from PIL import Image

ROOT = Path(__file__).resolve().parent
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
REPO_DOOM = ROOT.parent if ROOT.parent.name == "doom" else None
REPO_ROOT = REPO_DOOM.parent.parent if REPO_DOOM is not None else None


def source_path(local_name, repo_relative):
    local = ROOT / local_name
    if local.exists():
        return local
    if REPO_ROOT is not None:
        return REPO_ROOT / repo_relative
    raise FileNotFoundError(local_name)


CONTROLLER = source_path("map01_overlap_controller_v39.py",
                         "research/doom/map01_overlap_controller_v39.py")
ADAPTER = source_path("persistent_planner_adapter_v2.py",
                      "research/live_control/persistent_planner_adapter_v2.py")
SOURCE_REFRESH = source_path("doom_source_refresh_v1.py",
                             "research/doom/doom_source_refresh_v1.py")


def load_adapter():
    spec = importlib.util.spec_from_file_location("frozen_adapter", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.PersistentPlannerAdapter


def load_current_functions():
    source = CONTROLLER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    top = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    main = top["main"]
    wait_node = next(n for n in ast.walk(main)
                     if isinstance(n, ast.FunctionDef) and n.name == "wait")
    selected = [top[name] for name in (
        "_typed_json_equal", "_signal_pair_matches",
        "_signal_pair_content_matches", "DoomCoverSignalPairMonitor",
        "cancel_invalidated_cover", "begin_model_turn", "temporal_sheet")]
    module = ast.Module(body=selected, type_ignores=[])
    from PIL import Image, ImageDraw
    namespace = {"json": json, "time": time, "Image": Image, "ImageDraw": ImageDraw}
    exec(compile(module, str(CONTROLLER), "exec"), namespace)
    wrapper = ("def make_waiter(incoming, process):\n"
               "    latest = None\n" + indent(ast.unparse(wait_node), "    ") +
               "\n    return wait, lambda: latest\n")
    exec(compile(wrapper, str(CONTROLLER) + "#wait-wrapper", "exec"), namespace)
    return namespace


def load_refresh():
    spec = importlib.util.spec_from_file_location("frozen_source_refresh", SOURCE_REFRESH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.refresh_source


class Guard:
    def __init__(self, name, source_value, source_sequence, source_capture_ns, floor=None):
        self.spec = {"source_value": source_value, "source_sequence": source_sequence}
        self.source_capture_ns = source_capture_ns
        self.name = name
        self.floor = floor

    def evaluate(self, signal):
        value = signal["value"]
        if self.floor is not None and value < self.floor:
            return {"status": "HARD_INVALIDATED", "reason": "below_hard_minimum",
                    "signal_id": self.name, "source_value": self.spec["source_value"],
                    "current_value": value, "hard_minimum": self.floor,
                    "requires_new_decision": True, "grants_input_authority": False,
                    "may_only_preserve_or_reduce_existing_authority": True,
                    "task_success_verified": False}
        return {"status": "UNCHANGED", "reason": "within_validity_envelope",
                "signal_id": self.name, "source_value": self.spec["source_value"],
                "current_value": value, "hard_minimum": self.floor or 0,
                "requires_new_decision": False, "grants_input_authority": False,
                "may_only_preserve_or_reduce_existing_authority": True,
                "task_success_verified": False}


class SignalReader:
    def __init__(self, name):
        self.name = name

    def read(self, row):
        return {"format": "observable-signal-v1", "status": "observed",
                "signal_id": self.name, "value": row[self.name],
                "sequence": row["sequence"], "capture_ns": row["capture_ns"],
                "binding": row["pointer_binding"]}


class Process:
    def __init__(self, timeline):
        self.timeline = timeline
        self.stdin = self

    def write(self, value):
        command = json.loads(value)
        self.timeline.append("executor_" + command["op"] + "_write")

    def flush(self):
        self.timeline.append("executor_flush")

    def poll(self):
        return None


class Client:
    def __init__(self, timeline):
        self.timeline = timeline
        self.interrupt_entered = threading.Event()
        self.ack_gate = threading.Event()
        self.turn_done = threading.Event()
        self.wait_entered = threading.Event()
        self.turn_index = 0
        self.started_inputs = []

    def start_thread(self, **_kwargs):
        return {"thread": {"id": "frozen-thread"}}

    def start_turn(self, _thread_id, inputs, **_kwargs):
        self.started_inputs.append(inputs)
        self.turn_index += 1
        return {"turn": {"id": f"turn-{self.turn_index}"}}

    def wait_turn_completed(self, _thread_id, _turn_id, timeout):
        self.wait_entered.set()
        if not self.turn_done.wait(timeout):
            raise TimeoutError("test fixture did not complete planner turn")
        # Completion wins the server-side race, but answer was already invalidated.
        return {"turn": {"status": "completed", "items": [
            {"type": "agentMessage", "text": '{"state":"active"}'}]}}

    def latest_turn_usage(self, _thread_id, _turn_id):
        return {"input_tokens": 1, "output_tokens": 1}

    def interrupt_turn(self, _thread_id, _turn_id):
        self.timeline.append("planner_interrupt_request")
        self.interrupt_entered.set()
        if not self.ack_gate.wait(2):
            raise TimeoutError("test did not release planner interrupt response")
        self.timeline.append("planner_interrupt_ack")
        self.turn_done.set()
        return {"accepted": True}


class InvalidationReplanCompositionTests(unittest.TestCase):
    def test_cancel_precedes_blocked_interrupt_and_next_turn_uses_fresh_frame(self):
        functions = load_current_functions()
        Adapter = load_adapter()
        refresh_source = load_refresh()
        timeline = []
        client = Client(timeline)
        planner = Adapter(client, model="frozen-mock", effort="low", cwd=".",
                          base_instructions="inert test")
        planner.start_session()
        old_handle = planner.begin_turn("old decision from sequence 10",
                                       output_schema={"type": "object"})

        binding = {"window": 7, "surface": 7}
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            tmp = Path(directory)
            old_image = tmp / "old-frame.png"
            fresh_image = tmp / "fresh-frame.png"
            Image.new("RGB", (1280, 720), (180, 20, 20)).save(old_image)
            Image.new("RGB", (1280, 720), (20, 180, 20)).save(fresh_image)
            startup = {"event": "observation", "sequence": 10, "capture_ns": 100,
                       "image": str(old_image), "health": 70, "ammo": 8,
                       "pointer_binding": binding}
            hard_typed = {"event": "typed_observation", "sequence": 11,
                          "capture_ns": 200, "frame_rgb_sha256": "fresh-hash",
                          "pointer_binding": binding,
                          "signals": {
                              "health": {"format": "observable-signal-v1", "status": "observed",
                                         "signal_id": "health", "value": 60,
                                         "sequence": 11, "capture_ns": 200, "binding": binding},
                              "ammo": {"format": "observable-signal-v1", "status": "observed",
                                       "signal_id": "ammo", "value": 8,
                                       "sequence": 11, "capture_ns": 200, "binding": binding}}}
            fresh_full = {"event": "observation", "sequence": 11, "capture_ns": 200,
                          "image": str(fresh_image), "health": 60, "ammo": 8,
                          "frame_rgb_sha256": "fresh-hash", "pointer_binding": binding}
            terminal = {"event": "terminal", "id": "cover-10", "status": "cancelled",
                        "release": {"verified": True, "keys_down": [], "buttons_down": []}}

            incoming = queue.Queue()
            incoming.put(startup)
            process = Process(timeline)
            wait, get_latest = functions["make_waiter"](incoming, process)
            first = wait(lambda row: row["event"] == "observation", timeout=1)
            self.assertIs(first, startup)
            self.assertEqual(get_latest()["sequence"], 10)

            health_guard = Guard("health", 70, 10, 100, floor=65)
            ammo_guard = Guard("ammo", 8, 10, 100)
            monitor = functions["DoomCoverSignalPairMonitor"](
                {"health": health_guard, "ammo": ammo_guard}, None, None)
            incoming.put(hard_typed)
            boundary = wait(lambda row: row["event"] == "terminal" and
                            row.get("id") == "cover-10", timeout=1,
                            observation_monitor=monitor)
            self.assertEqual(boundary["event"], "policy_invalidation")
            self.assertEqual(boundary["invalidation"]["reason"],
                             "health:below_hard_minimum")

            # The V12/V15 producer route publishes a matching full observation
            # before terminal; the wait closure must retain it while seeking terminal.
            incoming.put(fresh_full)
            incoming.put(terminal)
            future_pool = ThreadPoolExecutor(max_workers=1)
            try:
                planner_future = future_pool.submit(planner.await_turn, old_handle, 5)
                self.assertTrue(client.wait_entered.wait(1))
                result_holder = {}

                def cancel_cover():
                    result_holder["result"] = functions["cancel_invalidated_cover"](
                        planner, old_handle, process, wait, "cover-10")

                cancel_thread = threading.Thread(target=cancel_cover)
                cancel_thread.start()
                self.assertTrue(client.interrupt_entered.wait(1))
                self.assertEqual(timeline, ["executor_cancel_write", "executor_flush",
                                            "planner_interrupt_request"])
                self.assertEqual(get_latest()["sequence"], 10,
                                 "consumer remains blocked on planner ACK before event wait")
                client.ack_gate.set()
                cancel_thread.join(2)
                self.assertFalse(cancel_thread.is_alive())
                planner_result = planner_future.result(timeout=2)
            finally:
                client.ack_gate.set()
                future_pool.shutdown(wait=True)

            self.assertEqual(result_holder["result"][1], terminal)
            self.assertEqual(get_latest()["sequence"], 11)
            self.assertEqual(get_latest()["image"], str(fresh_image))
            self.assertEqual(timeline[:3], ["executor_cancel_write", "executor_flush",
                                            "planner_interrupt_request"])
            self.assertEqual(timeline[3], "planner_interrupt_ack")
            self.assertEqual(planner_result.status, "completed")
            self.assertTrue(planner_result.cancellation_requested)
            self.assertFalse(planner_result.answer_eligible)
            self.assertIsNone(planner_result.answer)

            health_reader, ammo_reader = SignalReader("health"), SignalReader("ammo")
            refreshed, refresh_receipt = refresh_source(
                get_latest(), health_reader, ammo_reader,
                lambda _command: self.fail("already-valid latest frame must not resubmit"),
                wait, "next-source")
            self.assertEqual(refresh_receipt["status"], "already_observed")
            self.assertEqual(refreshed["sequence"], 11)

            sheet = tmp / "next-temporal-sheet.png"
            functions["temporal_sheet"]([old_image, Path(refreshed["image"])], sheet)
            begin = functions["begin_model_turn"]
            functions["win"] = lambda path: str(path)
            new_handle = begin(planner, tmp, sheet, [], 60, 8, None,
                               {"type": "object"})
            self.assertEqual(new_handle.turn_id, "turn-2")
            next_inputs = client.started_inputs[1]
            self.assertEqual(next_inputs[-1], {"type": "localImage", "path": str(sheet)})
            self.assertIn("Current locally verified health: 60.", next_inputs[0]["text"])
            self.assertIn("Current locally verified ammo: 8.", next_inputs[0]["text"])
            with Image.open(sheet) as packed:
                self.assertEqual(packed.getpixel((500, 400)), (20, 180, 20))
                sheet_hash = hashlib.sha256(sheet.read_bytes()).hexdigest()
            result = {
                "classification": "CONSTRUCTION_ONLY_CURRENT_MAIN_FUNCTION_COMPOSITION",
                "source_commit": FREEZE["github_main_sha_at_freeze"],
                "typed_hard_invalidation": {"sequence": 11, "health": 60,
                                            "hard_minimum": 65, "reason":
                                            boundary["invalidation"]["reason"]},
                "timeline": timeline,
                "verified_executor_release": terminal["release"],
                "invalidated_planner_result": {"status": planner_result.status,
                                                "answer_eligible": planner_result.answer_eligible,
                                                "cancellation_requested": planner_result.cancellation_requested,
                                                "answer": planner_result.answer},
                "fresh_observation_used": {"sequence": refreshed["sequence"],
                                           "health": refreshed["health"],
                                           "ammo": refreshed["ammo"],
                                           "image_name": Path(refreshed["image"]).name},
                "source_refresh_status": refresh_receipt["status"],
                "next_turn_input": {"turn_id": new_handle.turn_id,
                                    "image_name": Path(next_inputs[-1]["path"]).name,
                                    "temporal_sheet_sha256": sheet_hash,
                                    "prompt_has_fresh_health": "Current locally verified health: 60." in next_inputs[0]["text"],
                                    "prompt_has_fresh_ammo": "Current locally verified ammo: 8." in next_inputs[0]["text"],
                                    "latest_frame_pixel": list(packed.getpixel((500, 400)))}
            }
            (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n",
                                               encoding="utf-8")


if __name__ == "__main__":
    unittest.main(verbosity=2)
