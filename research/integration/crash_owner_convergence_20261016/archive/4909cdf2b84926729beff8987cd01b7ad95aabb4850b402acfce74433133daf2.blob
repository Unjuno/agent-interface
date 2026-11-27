"""One-shot current-main policy-invalidation to Xvfb key-release integration."""
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
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOKEN = "v39-active-invalidation-key-release-a01"
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
        if observation.get("event") == "typed_observation":
            return observation["signals"][self.signal_id]
        value = observation[self.signal_id]
        return {"format": "observable-signal-v1", "status": "observed",
                "signal_id": self.signal_id, "value": value,
                "sequence": observation["sequence"],
                "capture_ns": observation["capture_ns"],
                "binding": observation["pointer_binding"]}


def wait_event(observer, expected_type, deadline_seconds=2.0):
    deadline = time.monotonic() + deadline_seconds
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


class FakeProcess:
    """Minimal executor protocol peer; cancel crosses the production helper boundary."""
    def __init__(self, owner, lease, observer, keycode):
        self.owner = owner
        self.lease = lease
        self.observer = observer
        self.keycode = keycode
        self.events = []
        self.release_transitions = None
        self.key_release_event = None
        self.terminal = None
        self.stdin = self
        self._line = ""

    def write(self, value):
        self._line += value
        self.events.append("cancel_write")

    def flush(self):
        request = json.loads(self._line)
        self._line = ""
        if request != {"op": "cancel", "id": "active-cover-a01"}:
            raise RuntimeError("unexpected executor command")
        self.events.append("cancel_flushed")
        self.release_transitions = self.owner.call("up_batch", self.lease, ["a"])
        self.key_release_event = wait_event(self.observer, 3)
        verified = (type(self.release_transitions) is list
                    and len(self.release_transitions) == 1
                    and self.release_transitions[0].get("owner_thread_keyup_verified") is True
                    and not key_down(self.observer, self.keycode))
        self.terminal = {
            "event": "terminal", "id": request["id"], "status": "cancelled",
            "release": {"verified": verified, "keys_down": [],
                        "buttons_down": [],
                        "owner_transitions": self.release_transitions}}
        self.events.append("owner_keyup_verified_before_terminal")

    def wait_terminal(self, predicate):
        if self.terminal is None or not predicate(self.terminal):
            raise RuntimeError("executor terminal did not satisfy production wait predicate")
        self.events.append("terminal_observed")
        return self.terminal


class FakeClient:
    def __init__(self, monitor, current, key_query, process, runtime, label):
        self.monitor = monitor
        self.current = current
        self.key_query = key_query
        self.process = process
        self.runtime = runtime
        self.label = label
        self.events = []
        self.inputs = []
        self.invalidation = None
        self.key_down_before_observation = None
        self.key_down_after_cancel = None
        self.cancel_result = None
        self.terminal = None
        self.adapter = None

    def start_thread(self, **kwargs):
        return {"thread": {"id": "active-invalidation-a01"}}

    def start_turn(self, thread_id, inputs, **kwargs):
        self.inputs.append(inputs)
        self.events.append("planner_turn_started")
        return {"turn": {"id": "active-turn-a01"}}

    def wait_turn_completed(self, thread_id, turn_id, timeout=120):
        self.events.append("new_typed_observation_delivered_while_turn_pending")
        self.key_down_before_observation = self.key_query()
        self.invalidation = self.monitor.observe(self.current)
        if self.invalidation is not None:
            self.events.append("paired_policy_invalidated")
            self.cancel_result, self.terminal = self.runtime["cancel_invalidated_cover"](
                self.adapter, self.adapter._active, self.process,
                self.process.wait_terminal, "active-cover-a01")
            self.key_down_after_cancel = self.key_query()
            self.events.append("planner_interrupted_after_executor_cancel")
        else:
            self.events.append("policy_preserved")
            self.key_down_after_cancel = self.key_query()
        return {"turn": {"status": "completed", "items": [
            {"type": "agentMessage", "text": json.dumps(ACTION)}]}}

    def interrupt_turn(self, thread_id, turn_id):
        self.events.append("planner_interrupt_transport_called")
        return {"turn": {"status": "interrupt_requested"}}

    def latest_turn_usage(self, thread_id, turn_id):
        return {"input_tokens": 0, "output_tokens": 0}


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
    guard_module = __import__("observable_signal_guard_v2")
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
             "DoomCoverSignalPairMonitor", "begin_model_turn",
             "final_admission_from_planner_result", "prepare_action_admission",
             "cancel_invalidated_cover")
    missing = [name for name in names if name not in top]
    if missing:
        raise ValueError("current V39 symbols missing: " + repr(missing))
    namespace = {
        "json": json, "time": time,
        "ObservableSignalGuard": guard_module.ObservableSignalGuard,
        "ObservableSignalPolicyMonitor": guard_module.ObservableSignalPolicyMonitor,
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
    parser.add_argument("--display", default=":133")
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("result leaf exists; refusing to overwrite")
    args.out.mkdir(parents=True)
    os.environ.setdefault("XAUTHORITY", "/dev/null")
    freeze = json.loads((HERE.parent / "FREEZE.json").read_text(encoding="utf-8"))
    raw = {"schema": "v39-active-invalidation-key-release-xvfb-raw-a01-v1",
           "status": "STOP", "errors": [], "display": args.display,
           "scope": "synthetic paired health guard invalidation through current V39 cancel helper to actual Xvfb keyup; no game/model/physical input",
           "input_pair": {}, "arms": {}, "cleanup": {}}
    xvfb = observer = None
    owners = []
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
        source, retained = typed[2], typed[3]
        if (source["signals"]["health"]["value"] != 97
                or source["signals"]["ammo"]["value"] != 48
                or retained["signals"]["health"]["value"] != 97
                or retained["signals"]["ammo"]["value"] != 48
                or source["pointer_binding"] != retained["pointer_binding"]):
            raise ValueError("retained observation pair differs from freeze")
        raw["input_pair"] = {
            "source_sequence": 2, "current_sequence": 3,
            "retained_health_ammo": [[97, 48], [97, 48]],
            "pointer_binding_equal": True,
            "source_frame_rgb_sha256": source["frame_rgb_sha256"],
            "current_frame_rgb_sha256": retained["frame_rgb_sha256"],
            "source_png_sha256": sha(HERE.parent / "INPUTS" / "002.png"),
            "current_png_sha256": sha(HERE.parent / "INPUTS" / "003.png"),
        }
        runtime = load_runtime()
        from Xlib import X, XK, display
        import types
        executor = types.ModuleType("executor_v3")
        executor.Cancelled = type("Cancelled", (Exception,), {})
        executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
        sys.modules["executor_v3"] = executor
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
        if not keycode:
            raise RuntimeError("X keycode unavailable")
        health_reader = SignalReader("health")
        ammo_reader = SignalReader("ammo")
        validity = {"signal_id": "health", "critical_health_minimum": 45,
                    "maximum_health_loss": 8, "max_source_age_ms": 1000}
        source_health = source["signals"]["health"]
        source_ammo = source["signals"]["ammo"]
        arms = (("health_drop_invalidates", 80),
                ("health_unchanged_control", 97))
        for index, (label, current_health) in enumerate(arms, 1):
            current = copy.deepcopy(retained)
            current["signals"]["health"]["value"] = current_health
            guards = {
                "health": runtime["ObservableSignalGuard"](
                    runtime["guard_spec"](validity, source_health, "active-cancel-a01"),
                    source_health, source["pointer_binding"]),
                "ammo": runtime["ObservableSignalGuard"](
                    runtime["ammo_guard_spec"](source_ammo, "active-cancel-a01", 1000),
                    source_ammo, source["pointer_binding"]),
            }
            monitor = runtime["DoomCoverSignalPairMonitor"](
                guards, health_reader, ammo_reader)
            win = root.create_window(30 + index * 10, 30 + index * 10, 320, 200,
                                     0, observer.screen().root_depth, X.InputOutput,
                                     X.CopyFromParent,
                                     event_mask=X.KeyPressMask | X.KeyReleaseMask)
            win.map()
            observer.sync()
            observer.set_input_focus(win, X.RevertToParent, X.CurrentTime)
            observer.sync()
            focus_deadline = time.monotonic() + 1
            while time.monotonic() < focus_deadline:
                focused = observer.get_input_focus().focus
                if getattr(focused, "id", focused) == win.id:
                    break
                time.sleep(0.01)
            else:
                raise RuntimeError("Xvfb client focus was not established")
            while observer.pending_events():
                observer.next_event()
            lease = Lease(int(win.id), TOKEN + ":" + label)
            owner = InputOwner(args.display)
            owners.append(owner)
            admission = owner.call("down", lease, "a")
            press = wait_event(observer, X.KeyPress)
            if not press or press["keycode"] != keycode or press["window"] != win.id:
                raise RuntimeError("Xvfb did not observe actual owner keydown")
            process = FakeProcess(owner, lease, observer, keycode)
            client = FakeClient(monitor, current, lambda: key_down(observer, keycode),
                                process, runtime, label)
            planner = runtime["PersistentPlannerAdapter"](
                client, model="frozen-mock", effort="low", cwd=".",
                base_instructions="active health-invalidation integration fixture")
            client.adapter = planner
            planner.start_session()
            with tempfile.TemporaryDirectory(prefix="v39-active-cancel-") as temp_root:
                handle = runtime["begin_model_turn"](
                    planner, Path(temp_root), HERE.parent / "INPUTS" / "002.png", [],
                    source_health["value"], source_ammo["value"], {}, SCHEMA)
                planner_result = planner.await_turn(handle)
            terminal_ns = time.perf_counter_ns()
            final = runtime["final_admission_from_planner_result"](
                planner_result, terminal_ns, client.invalidation, terminal_ns + 1)
            release_event = process.key_release_event
            if release_event is None:
                owner.close()
                release_event = wait_event(observer, X.KeyRelease)
            else:
                owner.close()
            owners.remove(owner)
            up_after_cleanup = not key_down(observer, keycode)
            inner = owner._inner
            close_record = next((row for row in reversed(inner.records)
                                 if row.get("event") == "owner_release"), None)
            health_outcome = (client.invalidation or {}).get("outcomes", {}).get("health")
            arm_raw = {
                "health_value": current_health,
                "monitor_invalidation": client.invalidation,
                "health_guard_outcome": health_outcome,
                "planner_events": client.events,
                "executor_protocol_events": process.events,
                "cancel_result": client.cancel_result,
                "executor_terminal": client.terminal,
                "release_transitions": process.release_transitions,
                "answer_eligible": planner_result.answer_eligible,
                "planner_cancellation_requested": planner_result.cancellation_requested,
                "final_admission": final,
                "input_admission": admission,
                "keycode": keycode,
                "client_window": int(win.id),
                "key_press_event": press,
                "key_down_before_observation": client.key_down_before_observation,
                "key_down_after_cancel": client.key_down_after_cancel,
                "key_release_event": release_event,
                "observer_key_up_after_cleanup": up_after_cleanup,
                "owner_close_record": close_record,
                "owner_closed": inner.closed,
                "owner_stopped": inner.stopped.is_set(),
                "owner_thread_alive": inner.thread.is_alive(),
            }
            raw["arms"][label] = arm_raw
            if label == "health_drop_invalidates":
                if (client.invalidation is None or client.cancel_result is None
                        or planner_result.answer_eligible
                        or not planner_result.cancellation_requested
                        or client.key_down_before_observation is not True
                        or client.key_down_after_cancel is not False
                        or release_event is None or not up_after_cleanup
                        or final["status"] != "REJECTED_POLICY_INVALIDATED"
                        or final["executor_admission"] is not None):
                    raise RuntimeError("hard health invalidation did not cancel and release before admission")
            else:
                if (client.invalidation is not None or client.cancel_result is not None
                        or not planner_result.answer_eligible
                        or client.key_down_after_cancel is not True
                        or final["status"] != "READY_FOR_FRESH_EXECUTOR_ADMISSION"
                        or not up_after_cleanup):
                    raise RuntimeError("unchanged control did not preserve policy and normal cleanup")
        raw["status"] = "CANDIDATE_COMPLETE"
    except BaseException as exc:
        raw["errors"].append(f"{type(exc).__name__}: {exc}")
    finally:
        for owner in list(owners):
            try:
                owner.close()
            except BaseException as exc:
                raw["cleanup"]["owner_close_error"] = f"{type(exc).__name__}: {exc}"
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
                or raw["cleanup"].get("xvfb_exit") != 0 or len(raw["arms"]) != 2):
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
