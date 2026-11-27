import ast
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import queue
import tempfile
import threading
import time
import unittest
from pathlib import Path
from textwrap import indent

ROOT = Path(__file__).resolve().parent
CONTROLLER = ROOT / "sources" / "strict_controller.py"
GUARD_SOURCE = ROOT / "sources" / "observable_signal_guard_v2.py"
ADAPTER_SOURCE = ROOT / "sources" / "persistent_planner_adapter_v2.py"
BINDING = {"focus": 7, "surface": 9, "geometry": [0, 0, 1280, 720]}


def load_sources():
    guard_spec = importlib.util.spec_from_file_location("frozen_guard", GUARD_SOURCE)
    guard_module = importlib.util.module_from_spec(guard_spec)
    guard_spec.loader.exec_module(guard_module)
    adapter_spec = importlib.util.spec_from_file_location("frozen_adapter", ADAPTER_SOURCE)
    adapter_module = importlib.util.module_from_spec(adapter_spec)
    adapter_spec.loader.exec_module(adapter_module)

    tree = ast.parse(CONTROLLER.read_text(encoding="utf-8"))
    top = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    main = top["main"]
    wait_node = next(n for n in ast.walk(main)
                     if isinstance(n, ast.FunctionDef) and n.name == "wait")
    names = ("guard_spec", "ammo_guard_spec", "_typed_json_equal",
             "_signal_pair_matches", "_signal_pair_content_matches",
             "DoomCoverSignalPairMonitor", "terminal_release_is_known_empty",
             "cancel_invalidated_cover")
    namespace = {"json": json, "time": time, "RuntimeError": RuntimeError,
                 "ObservableSignalGuard": guard_module.ObservableSignalGuard}
    exec(compile(ast.Module(body=[top[name] for name in names], type_ignores=[]),
                 str(CONTROLLER), "exec"), namespace)
    wrapper = ("def make_waiter(incoming, process):\n"
               "    latest = None\n" + indent(ast.unparse(wait_node), "    ") +
               "\n    return wait, lambda: latest\n")
    exec(compile(wrapper, str(CONTROLLER) + "#wait-wrapper", "exec"), namespace)
    return namespace, adapter_module.PersistentPlannerAdapter


def signal(name, value, sequence, capture_ns):
    return {"format": "observable-signal-v1", "status": "observed",
            "signal_id": name, "value": value, "sequence": sequence,
            "capture_ns": capture_ns, "binding": BINDING}


def make_monitor(functions):
    health = signal("health", 70, 10, 1_000_000_000)
    ammo = signal("ammo", 6, 10, 1_000_000_000)
    validity = {"signal_id": "health", "critical_health_minimum": 65,
                "maximum_health_loss": 8, "max_source_age_ms": 1000}
    hs = functions["guard_spec"](validity, health, "a10")
    ass = functions["ammo_guard_spec"](ammo, "a10", 1000)
    hg = functions["ObservableSignalGuard"](hs, health, BINDING)
    ag = functions["ObservableSignalGuard"](ass, ammo, BINDING)
    return functions["DoomCoverSignalPairMonitor"]({"health": hg, "ammo": ag}, None, None)


class FakeExecutor:
    def __init__(self, timeline):
        self.timeline = timeline
        self.stdin = self
        self.cancel_commands = []

    def write(self, raw):
        command = json.loads(raw)
        self.timeline.append(f"executor_{command['op']}_write")
        if command["op"] == "cancel":
            self.cancel_commands.append(command)

    def flush(self):
        self.timeline.append("executor_flush")

    def poll(self):
        return None


class DelayedPlannerClient:
    def __init__(self, timeline):
        self.timeline = timeline
        self.interrupt_entered = threading.Event()
        self.ack_gate = threading.Event()
        self.turn_done = threading.Event()
        self.wait_entered = threading.Event()

    def start_thread(self, **_kwargs):
        return {"thread": {"id": "frozen-thread"}}

    def start_turn(self, _thread_id, _inputs, **_kwargs):
        return {"turn": {"id": "turn-1"}}

    def wait_turn_completed(self, _thread_id, _turn_id, timeout):
        self.wait_entered.set()
        if not self.turn_done.wait(timeout):
            raise TimeoutError("fixture did not complete old planner answer")
        return {"turn": {"status": "completed", "items": [
            {"type": "agentMessage", "text": '{"state":"active"}'}]}}

    def latest_turn_usage(self, _thread_id, _turn_id):
        return {"input_tokens": 1, "output_tokens": 1}

    def interrupt_turn(self, _thread_id, _turn_id):
        self.timeline.append("planner_interrupt_request")
        self.interrupt_entered.set()
        if not self.ack_gate.wait(2):
            raise TimeoutError("fixture did not release interrupt ACK")
        self.timeline.append("planner_interrupt_ack")
        self.turn_done.set()
        return {"accepted": True}


class ActualGuardCancelCompositionTests(unittest.TestCase):
    def test_health_crossing_cancels_before_ack_and_rejects_late_answer(self):
        functions, Adapter = load_sources()
        timeline = []
        client = DelayedPlannerClient(timeline)
        planner = Adapter(client, model="frozen-mock", effort="low", cwd=".",
                          base_instructions="inert construction fixture")
        planner.start_session()
        handle = planner.begin_turn("old plan from observation sequence 10",
                                    output_schema={"type": "object"})
        incoming = queue.Queue()
        executor = FakeExecutor(timeline)
        wait, get_latest = functions["make_waiter"](incoming, executor)
        startup = {"event": "observation", "sequence": 10,
                   "capture_ns": 1_000_000_000, "health": 70, "ammo": 6,
                   "pointer_binding": BINDING}
        incoming.put(startup)
        self.assertIs(wait(lambda row: row["event"] == "observation", timeout=1), startup)

        monitor = make_monitor(functions)
        typed = {"event": "typed_observation", "sequence": 11,
                 "capture_ns": 1_100_000_000, "pointer_binding": BINDING,
                 "signals": {"health": signal("health", 64, 11, 1_100_000_000),
                             "ammo": signal("ammo", 6, 11, 1_100_000_000)}}
        incoming.put(typed)
        boundary = wait(lambda row: row["event"] == "terminal" and
                        row.get("id") == "cover-a10", timeout=1,
                        observation_monitor=monitor)
        self.assertEqual(boundary["event"], "policy_invalidation")
        self.assertEqual(boundary["invalidation"]["reason"],
                         "health:below_hard_minimum")
        self.assertTrue(boundary["invalidation"]["requires_new_decision"])
        self.assertFalse(boundary["invalidation"]["grants_input_authority"])

        terminal = {"event": "terminal", "id": "cover-a10", "status": "cancelled",
                    "release": {"verified": True, "keys_down": [], "buttons_down": [],
                                "keys_unknown": [], "key_state_errors": []}}
        incoming.put(terminal)
        pool = ThreadPoolExecutor(max_workers=1)
        try:
            old_answer = pool.submit(planner.await_turn, handle, 5)
            self.assertTrue(client.wait_entered.wait(1))
            completion = {}

            def cancel():
                completion["value"] = functions["cancel_invalidated_cover"](
                    planner, handle, executor, wait, "cover-a10")

            cancel_thread = threading.Thread(target=cancel)
            cancel_thread.start()
            self.assertTrue(client.interrupt_entered.wait(1))
            self.assertEqual(timeline, ["executor_cancel_write", "executor_flush",
                                        "planner_interrupt_request"])
            self.assertEqual(executor.cancel_commands, [{"op": "cancel", "id": "cover-a10"}])
            client.ack_gate.set()
            cancel_thread.join(2)
            self.assertFalse(cancel_thread.is_alive())
            result = old_answer.result(timeout=2)
        finally:
            client.ack_gate.set()
            pool.shutdown(wait=True)

        self.assertEqual(completion["value"][1], terminal)
        self.assertEqual(timeline, ["executor_cancel_write", "executor_flush",
                                    "planner_interrupt_request", "planner_interrupt_ack"])
        self.assertEqual(result.status, "completed")
        self.assertTrue(result.cancellation_requested)
        self.assertFalse(result.answer_eligible)
        self.assertIsNone(result.answer)
        self.assertEqual(terminal["release"],
                         {"verified": True, "keys_down": [], "buttons_down": [],
                          "keys_unknown": [], "key_state_errors": []})
        receipt = {"case": "health_floor_crossing_with_blocked_interrupt_ack",
                   "invalidation": boundary["invalidation"]["reason"],
                   "cancel_commands": executor.cancel_commands,
                   "timeline": timeline,
                   "planner_result": {"status": result.status,
                                      "cancellation_requested": result.cancellation_requested,
                                      "answer_eligible": result.answer_eligible,
                                      "answer": result.answer},
                   "terminal_release": terminal["release"],
                   "latest_observation_sequence": get_latest()["sequence"],
                   "classification": "CONSTRUCTION_ONLY_SOURCE_COMPOSITION"}
        print("A11_COMPOSED_RESULT=" + json.dumps(receipt, sort_keys=True))


    def test_legacy_accepts_but_strict_candidate_rejects_incomplete_receipts(self):
        def extract(source, strict):
            tree = ast.parse(source.read_text(encoding="utf-8"))
            top = {node.name: node for node in tree.body
                   if isinstance(node, ast.FunctionDef)}
            nodes = ([top["terminal_release_is_known_empty"]]
                     if strict else []) + [top["cancel_invalidated_cover"]]
            namespace = {"json": json, "RuntimeError": RuntimeError}
            exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec"),
                 namespace)
            return namespace["cancel_invalidated_cover"]

        legacy = extract(ROOT / "sources" / "main_controller.py", False)
        strict = extract(CONTROLLER, True)
        incomplete = (
            {"verified": True, "keys_down": [], "buttons_down": [],
             "key_state_errors": []},
            {"verified": True, "keys_down": [], "buttons_down": [],
             "keys_unknown": ["KEY_W"], "key_state_errors": []},
            {"verified": True, "keys_down": [], "buttons_down": [],
             "keys_unknown": []},
            {"verified": True, "keys_down": [], "buttons_down": [],
             "keys_unknown": [], "key_state_errors": [{"source": "keymap_after"}]},
        )

        class Process:
            def __init__(self):
                self.writes = []
                self.stdin = self
            def write(self, value): self.writes.append(json.loads(value))
            def flush(self): pass

        class Planner:
            def __init__(self): self.interrupts = 0
            def interrupt(self, _handle, before_transport=None):
                if before_transport is not None: before_transport()
                self.interrupts += 1
                return {"status": "interrupted"}

        def exercise(function, release):
            process = Process()
            planner = Planner()
            terminal = {"event": "terminal", "id": "cover-a10",
                        "status": "cancelled", "release": release}
            result = function(planner, object(), process,
                              lambda predicate: terminal if predicate(terminal)
                              else self.fail("matching terminal was not accepted"),
                              "cover-a10")
            return result, process, planner

        for release in incomplete:
            with self.subTest(release=release):
                legacy_result, legacy_process, legacy_planner = exercise(legacy, release)
                self.assertEqual(legacy_process.writes, [{"op": "cancel", "id": "cover-a10"}])
                self.assertEqual(legacy_planner.interrupts, 1)
                self.assertEqual(legacy_result[1]["release"], release)
                with self.assertRaisesRegex(RuntimeError, "invalidated cover did not verify empty release"):
                    exercise(strict, release)


if __name__ == "__main__":
    unittest.main(verbosity=2)
