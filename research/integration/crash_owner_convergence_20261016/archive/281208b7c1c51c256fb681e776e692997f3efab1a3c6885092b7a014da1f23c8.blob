"""Current-main V39 cancellation through real Executor V3 and Xvfb InputOwner."""
import argparse
import ast
import copy
import hashlib
import json
import os
import select
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOKEN = "v39-executor-cancel-active-key-a01"
ACTION = {"commands": [{"action": "fire", "extent": "short"}]}
SCHEMA = {"type": "object", "required": ["commands"],
          "additionalProperties": False,
          "properties": {"commands": {"type": "array", "minItems": 1,
                                        "items": {"type": "object"}}}}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Lease:
    def __init__(self, focus, token):
        import threading
        self.deadline = time.perf_counter_ns() + 20_000_000_000
        self.expected_focus = focus
        self.intent_token = token
        self.cancel = threading.Event()
        self.focus_invalid = False

    def check(self):
        if self.cancel.is_set():
            raise RuntimeError("cancelled")
        if time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("expired")

    def record_interruption(self, row):
        self.interruption = row


class SignalReader:
    def __init__(self, signal_id):
        self.signal_id = signal_id

    def read(self, observation):
        return observation["signals"][self.signal_id]


class EventSink:
    def __init__(self):
        self.events = []
        self.cv = threading.Condition()

    def emit(self, event):
        with self.cv:
            self.events.append(dict(event))
            self.cv.notify_all()

    def wait_for(self, predicate, timeout=5):
        deadline = time.monotonic() + timeout
        with self.cv:
            while True:
                for row in self.events:
                    if predicate(row):
                        return dict(row)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Executor V3 event wait expired")
                self.cv.wait(remaining)


class XvfbBackend:
    """Minimal Executor V3 backend whose effects use the actual current owner."""
    def __init__(self, owner, lease):
        self.owner = owner
        self.owner_lease = lease
        self.sequence = 2
        self.lease = None
        self.down = []
        self.started = threading.Event()
        self.released = None

    def validate(self, steps):
        if (type(steps) is not list or len(steps) != 1
                or steps[0] != {"op": "hold", "keys": ["a"], "duration_ms": 5000}):
            raise ValueError("unexpected bounded Xvfb hold program")

    def execute(self, step, cancel, identifier, index):
        for key in step["keys"]:
            self.owner.call("down", self.owner_lease, key)
            self.down.append(key)
        self.started.set()
        deadline = time.monotonic() + 6
        while not cancel.is_set():
            if time.monotonic() >= deadline:
                return
            cancel.wait(0.005)
        from executor_v3 import Cancelled
        raise Cancelled()

    def release_all(self):
        keys = list(self.down)
        if keys:
            transitions = self.owner.call("up_batch", self.owner_lease, keys)
            verified = (type(transitions) is list and len(transitions) == len(keys)
                        and all(row.get("owner_thread_keyup_verified") is True
                                for row in transitions))
            self.released = transitions
            self.down.clear()
        else:
            transitions = []
            verified = True
        return {"verified": verified, "keys_down": list(self.down),
                "buttons_down": [], "owner_transitions": transitions}


class ExecutorBridge:
    def __init__(self, executor, sink):
        self.executor = executor
        self.sink = sink
        self.stdin = self
        self._buffer = ""
        self.cancel_match = None
        self.terminal = None
        self.events_seen = []

    def write(self, value):
        self._buffer += value

    def flush(self):
        request = json.loads(self._buffer)
        self._buffer = ""
        if (type(request) is not dict or set(request) != {"op", "id"}
                or request["op"] != "cancel"):
            raise ValueError("unexpected controller/executor protocol command")
        self.cancel_match = self.executor.cancel(request["id"])

    def wait_terminal(self, predicate):
        self.terminal = self.sink.wait_for(
            lambda row: row.get("event") == "terminal" and predicate(row), timeout=5)
        self.events_seen = [dict(row) for row in self.sink.events]
        return dict(self.terminal)


class FakeClient:
    def __init__(self, monitor, current, key_query, bridge, runtime):
        self.monitor = monitor
        self.current = current
        self.key_query = key_query
        self.bridge = bridge
        self.runtime = runtime
        self.events = []
        self.inputs = []
        self.invalidation = None
        self.key_down_before_observation = None
        self.key_down_after_cancel = None
        self.cancel_result = None
        self.terminal = None
        self.adapter = None

    def start_thread(self, **kwargs):
        return {"thread": {"id": "executor-v3-xvfb-a01"}}

    def start_turn(self, thread_id, inputs, **kwargs):
        self.inputs.append(inputs)
        self.events.append("planner_turn_started")
        return {"turn": {"id": "planner-turn-v3-a01"}}

    def wait_turn_completed(self, thread_id, turn_id, timeout=120):
        self.events.append("fresh_typed_observation_during_pending_turn")
        self.key_down_before_observation = self.key_query()
        self.invalidation = self.monitor.observe(self.current)
        if self.invalidation is None:
            raise RuntimeError("synthetic hard health invalidation was not detected")
        self.events.append("paired_policy_invalidated")
        self.cancel_result, self.terminal = self.runtime["cancel_invalidated_cover"](
            self.adapter, self.adapter._active, self.bridge,
            self.bridge.wait_terminal, "active-cover-v3-a01")
        self.key_down_after_cancel = self.key_query()
        self.events.append("executor_terminal_before_planner_wait_return")
        return {"turn": {"status": "completed", "items": [
            {"type": "agentMessage", "text": json.dumps(ACTION)}]}}

    def interrupt_turn(self, thread_id, turn_id):
        self.events.append("planner_interrupt_transport_called")
        return {"turn": {"status": "interrupt_requested"}}

    def latest_turn_usage(self, thread_id, turn_id):
        return {"input_tokens": 0, "output_tokens": 0}


def wait_event(observer, expected_type, timeout=3):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if observer.pending_events():
            event = observer.next_event()
        else:
            ready, _, _ = select.select([observer.fileno()], [], [],
                                         max(0, deadline - time.monotonic()))
            if not ready:
                break
            event = observer.next_event()
        if event.type == expected_type:
            return {"type": int(event.type), "keycode": int(event.detail),
                    "window": int(event.window.id), "observed_ns": time.perf_counter_ns()}
    return None


def key_down(observer, keycode):
    bitmap = observer.query_keymap()
    return bool(bitmap[keycode // 8] & (1 << (keycode % 8)))


def load_events(path):
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()]
    typed = {row["sequence"]: row for row in rows
             if row.get("event") == "typed_observation" and row.get("sequence") in (2, 3)}
    if set(typed) != {2, 3}:
        raise ValueError("retained typed observations 2/3 missing")
    return typed


def load_runtime():
    sys.path.insert(0, str(HERE))
    from persistent_planner_adapter_v2 import PersistentPlannerAdapter
    from action_validity_admission_v1 import SNAPSHOT_FORMAT, evaluate_action_validity
    from doom_action_validity_contract_v1 import bindings_equal_exact, build_contract
    from final_action_admission_v2 import decide_final_admission, record_action_validity
    controller_path = HERE / "map01_overlap_controller_v39.py"
    tree = ast.parse(controller_path.read_text(encoding="utf-8"))
    top = {node.name: node for node in tree.body
           if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    names = ("guard_spec", "ammo_guard_spec", "_typed_json_equal",
             "_signal_pair_matches", "_signal_pair_content_matches",
             "DoomCoverSignalPairMonitor", "final_admission_from_planner_result",
             "begin_model_turn", "cancel_invalidated_cover")
    missing = [name for name in names if name not in top]
    if missing:
        raise ValueError("current V39 symbols missing: " + repr(missing))
    import observable_signal_guard_v2 as guards
    namespace = {
        "json": json, "time": time,
        "ObservableSignalGuard": guards.ObservableSignalGuard,
        "ObservableSignalPolicyMonitor": guards.ObservableSignalPolicyMonitor,
        "MAX_AUTHORED_HEALTH_LOSS": 20,
        "PersistentPlannerAdapter": PersistentPlannerAdapter,
        "SNAPSHOT_FORMAT": SNAPSHOT_FORMAT,
        "evaluate_action_validity": evaluate_action_validity,
        "bindings_equal_exact": bindings_equal_exact,
        "build_action_contract": build_contract,
        "decide_final_admission": decide_final_admission,
        "record_action_validity": record_action_validity,
        "win": lambda value: str(value),
    }
    exec(compile(ast.Module(body=[top[name] for name in names], type_ignores=[]),
                 str(controller_path), "exec"), namespace)
    return namespace


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--display", default=":135")
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("result leaf exists; refusing to overwrite")
    args.out.mkdir(parents=True)
    os.environ.setdefault("XAUTHORITY", "/dev/null")
    freeze = json.loads((HERE.parent / "FREEZE.json").read_text(encoding="utf-8"))
    raw = {"schema": "v39-executor-cancel-active-key-xvfb-raw-a01-v1",
           "status": "STOP", "errors": [], "display": args.display,
           "scope": "current V39 hard-signal invalidation to production Executor V3 cancel and actual Xvfb owner release; no game/model/physical input",
           "arms": {}, "cleanup": {}, "input_pair": {}}
    xvfb = observer = None
    owner = None
    executor = None
    try:
        for filename, expected in freeze["source_sha256"].items():
            if sha(HERE / filename) != expected:
                raise ValueError("source hash mismatch: " + filename)
        for filename, expected in freeze["input_sha256"].items():
            if sha(HERE.parent / "INPUTS" / filename) != expected:
                raise ValueError("input hash mismatch: " + filename)
        if sha(HERE / "candidate.py") != freeze["candidate_sha256"]:
            raise ValueError("candidate hash mismatch")
        typed = load_events(HERE.parent / "INPUTS" / "events.jsonl")
        source, current = copy.deepcopy(typed[2]), copy.deepcopy(typed[3])
        if (source["signals"]["health"]["value"] != 97
                or source["signals"]["ammo"]["value"] != 48
                or current["signals"]["health"]["value"] != 97
                or current["signals"]["ammo"]["value"] != 48):
            raise ValueError("retained source typed pair mismatch")
        current["signals"]["health"]["value"] = 80
        now = time.perf_counter_ns()
        source["capture_ns"] = now - 200_000_000
        current["capture_ns"] = now - 20_000_000
        for signal in source["signals"].values():
            signal["capture_ns"] = source["capture_ns"]
        for signal in current["signals"].values():
            signal["capture_ns"] = current["capture_ns"]
        runtime = load_runtime()
        from Xlib import X, XK, display
        from executor_v3 import Executor
        from input_transition_owner_v4 import InputOwner
        xvfb = subprocess.Popen(["Xvfb", args.display, "-screen", "0", "640x480x24",
                                 "-nolisten", "tcp", "-noreset", "-ac"],
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.PIPE)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if xvfb.poll() is not None:
                raise RuntimeError("Xvfb exited during startup")
            try:
                observer = display.Display(args.display)
                break
            except Exception:
                time.sleep(0.05)
        if observer is None:
            raise TimeoutError("Xvfb observer connection timed out")
        root = observer.screen().root
        keycode = int(observer.keysym_to_keycode(XK.string_to_keysym("a")))
        win = root.create_window(70, 70, 320, 200, 0, observer.screen().root_depth,
                                 X.InputOutput, X.CopyFromParent,
                                 event_mask=X.KeyPressMask | X.KeyReleaseMask)
        win.map()
        observer.sync()
        observer.set_input_focus(win, X.RevertToParent, X.CurrentTime)
        observer.sync()
        focused = observer.get_input_focus().focus
        if getattr(focused, "id", focused) != win.id:
            raise RuntimeError("Xvfb focus did not bind to test window")
        binding = {"focus": int(win.id), "surface": int(win.id),
                   "geometry": [0, 0, 320, 200]}
        for observation in (source, current):
            observation["pointer_binding"] = copy.deepcopy(binding)
            for signal in observation["signals"].values():
                signal["binding"] = copy.deepcopy(binding)
        while observer.pending_events():
            observer.next_event()
        lease = Lease(int(win.id), TOKEN)
        owner = InputOwner(args.display)
        backend = XvfbBackend(owner, lease)
        sink = EventSink()
        executor = Executor(backend, sink.emit)
        cover_id = "active-cover-v3-a01"
        valid_until = time.perf_counter_ns() + 15_000_000_000
        executor.submit(cover_id,
                        [{"op": "hold", "keys": ["a"], "duration_ms": 5000}],
                        expected_sequence=2, valid_until_ns=valid_until)
        accepted = sink.wait_for(lambda row: row.get("event") == "accepted", timeout=3)
        press = wait_event(observer, X.KeyPress, timeout=3)
        if (not press or press["keycode"] != keycode or press["window"] != win.id
                or accepted["accepted_ns"] >= press["observed_ns"]
                or not key_down(observer, keycode)):
            raise RuntimeError("Executor V3 acceptance/key-down order was not observed")
        raw["input_pair"] = {
            "source_sequence": 2, "current_sequence": 3,
            "source_health_ammo": [97, 48], "current_health_ammo": [80, 48],
            "binding_rebased_to_xvfb_window": binding,
            "source_png_sha256": sha(HERE.parent / "INPUTS" / "002.png"),
            "current_png_sha256": sha(HERE.parent / "INPUTS" / "003.png"),
        }
        guards = {
            "health": runtime["ObservableSignalGuard"](
                runtime["guard_spec"]({"signal_id": "health",
                    "critical_health_minimum": 45, "maximum_health_loss": 8,
                    "max_source_age_ms": 1000}, source["signals"]["health"], "executor-v3-a01"),
                source["signals"]["health"], binding),
            "ammo": runtime["ObservableSignalGuard"](
                runtime["ammo_guard_spec"](source["signals"]["ammo"], "executor-v3-a01", 1000),
                source["signals"]["ammo"], binding),
        }
        monitor = runtime["DoomCoverSignalPairMonitor"](
            guards, SignalReader("health"), SignalReader("ammo"))
        bridge = ExecutorBridge(executor, sink)
        client = FakeClient(monitor, current, lambda: key_down(observer, keycode),
                            bridge, runtime)
        planner = runtime["PersistentPlannerAdapter"](
            client, model="frozen-mock", effort="low", cwd=".",
            base_instructions="current V39 production Executor V3 cancellation integration")
        client.adapter = planner
        planner.start_session()
        with tempfile.TemporaryDirectory(prefix="v39-executor-v3-cancel-") as temp_root:
            handle = runtime["begin_model_turn"](
                planner, Path(temp_root), HERE.parent / "INPUTS" / "002.png", [],
                source["signals"]["health"]["value"],
                source["signals"]["ammo"]["value"], {}, SCHEMA)
            planner_result = planner.await_turn(handle)
        terminal_ns = time.perf_counter_ns()
        final = runtime["final_admission_from_planner_result"](
            planner_result, terminal_ns, client.invalidation, terminal_ns + 1)
        release_event = wait_event(observer, X.KeyRelease, timeout=2)
        key_is_up = not key_down(observer, keycode)
        deadline = time.monotonic() + 1
        while executor.active is not None and time.monotonic() < deadline:
            time.sleep(0.005)
        inner = owner._inner
        close_record = None
        owner.close()
        owner = None
        close_record = next((row for row in reversed(inner.records)
                             if row.get("event") == "owner_release"), None)
        raw["arms"]["active_hard_health_invalidation"] = {
            "executor_acceptance": accepted,
            "executor_events": list(sink.events),
            "executor_cancel_matched": bridge.cancel_match,
            "executor_terminal": client.terminal,
            "backend_release_transitions": backend.released,
            "keycode": keycode,
            "client_window": int(win.id),
            "key_press_event": press,
            "key_down_when_observation_arrived": client.key_down_before_observation,
            "monitor_invalidation": client.invalidation,
            "key_down_after_cancel_terminal": client.key_down_after_cancel,
            "key_release_event": release_event,
            "xvfb_key_up_after_terminal": key_is_up,
            "planner_events": client.events,
            "planner_answer_eligible": planner_result.answer_eligible,
            "planner_cancellation_requested": planner_result.cancellation_requested,
            "planner_interrupt_result": client.cancel_result,
            "final_admission": final,
            "executor_active_after_terminal": executor.active is not None,
            "owner_close_record": close_record,
            "owner_closed": inner.closed,
            "owner_stopped": inner.stopped.is_set(),
            "owner_thread_alive": inner.thread.is_alive(),
        }
        if (accepted["accepted_ns"] >= press["observed_ns"]
                or client.key_down_before_observation is not True
                or client.cancel_result is None
                or bridge.cancel_match is not True
                or client.terminal.get("status") != "cancelled"
                or client.terminal.get("release", {}).get("verified") is not True
                or client.key_down_after_cancel is not False
                or release_event is None or not key_is_up
                or planner_result.answer_eligible
                or not planner_result.cancellation_requested
                or final["status"] != "REJECTED_POLICY_INVALIDATED"
                or final["executor_admission"] is not None
                or executor.active is not None or inner.thread.is_alive()):
            raise RuntimeError("production Executor V3 cancellation/release integration assertion failed")
        raw["status"] = "CANDIDATE_COMPLETE"
    except BaseException as exc:
        raw["errors"].append(f"{type(exc).__name__}: {exc}")
    finally:
        if owner is not None:
            try:
                owner.close()
            except BaseException as exc:
                raw["cleanup"]["owner_close_error"] = f"{type(exc).__name__}: {exc}"
        if executor is not None and executor.active is not None:
            try:
                executor.close()
            except BaseException as exc:
                raw["cleanup"]["executor_close_error"] = f"{type(exc).__name__}: {exc}"
        if observer is not None:
            try:
                observer.close()
            except BaseException as exc:
                raw["cleanup"]["observer_close_error"] = f"{type(exc).__name__}: {exc}"
        if xvfb is not None:
            try:
                xvfb.terminate()
                xvfb.wait(timeout=5)
                raw["cleanup"]["xvfb_exit"] = xvfb.returncode
            except BaseException as exc:
                raw["cleanup"]["xvfb_error"] = f"{type(exc).__name__}: {exc}"
                xvfb.kill()
                xvfb.wait(timeout=5)
                raw["cleanup"]["xvfb_exit"] = xvfb.returncode
        if (raw["errors"] or any(key.endswith("_error") for key in raw["cleanup"])
                or raw["cleanup"].get("xvfb_exit") != 0
                or "active_hard_health_invalidation" not in raw["arms"]):
            raw["status"] = "STOP"
        (args.out / "RAW.json").write_text(
            json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": raw["status"], "errors": raw["errors"],
                      "arms": list(raw["arms"]), "cleanup": raw["cleanup"]},
                     sort_keys=True))
    if raw["status"] != "CANDIDATE_COMPLETE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
