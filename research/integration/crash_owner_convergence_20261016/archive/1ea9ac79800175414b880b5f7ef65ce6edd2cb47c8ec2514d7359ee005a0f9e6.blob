"""One-shot active-key visual-context boundary on V39 and isolated Xvfb."""
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
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOKEN = "v39-visual-active-hold-a01"
ACTION = {"commands": [{"action": "fire", "extent": "short"}]}
AUTHORED = {"critical_health_minimum": 45, "maximum_health_loss": 8,
            "minimum_ammo": 1, "max_current_age_ms": 700}
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
        if self.cancel.is_set(): raise RuntimeError("cancelled")
        if time.perf_counter_ns() >= self.deadline: raise RuntimeError("expired")
    def record_interruption(self, row): self.interruption = row

class SignalReader:
    def __init__(self, signal_id): self.signal_id = signal_id
    def read(self, observation):
        if observation.get("event") == "typed_observation":
            return observation["signals"][self.signal_id]
        value = observation[self.signal_id]
        return {"format": "observable-signal-v1", "status": "observed",
                "signal_id": self.signal_id, "value": value,
                "sequence": observation["sequence"],
                "capture_ns": observation["capture_ns"],
                "binding": observation["pointer_binding"]}

class FakeClient:
    def __init__(self, monitor, current, key_query):
        self.monitor = monitor
        self.current = current
        self.key_query = key_query
        self.events = []
        self.inputs = []
        self.invalidation = None
        self.key_down_during_pending = None
    def start_thread(self, **kwargs): return {"thread": {"id": "active-hold-a01"}}
    def start_turn(self, thread_id, inputs, **kwargs):
        self.inputs.append(inputs)
        self.events.append("planner_turn_started")
        return {"turn": {"id": "active-hold-turn"}}
    def wait_turn_completed(self, thread_id, turn_id, timeout=120):
        self.events.append("new_frame_signal_delivered_while_turn_pending")
        self.invalidation = self.monitor.observe(self.current)
        self.key_down_during_pending = self.key_query()
        if self.invalidation is None:
            self.events.append("monitor_preserved_existing_policy")
        else:
            self.events.append("monitor_requested_new_decision")
        return {"turn": {"status": "completed", "items": [
            {"type": "agentMessage", "text": json.dumps(ACTION)}]}}
    def latest_turn_usage(self, thread_id, turn_id):
        return {"input_tokens": 0, "output_tokens": 0}

def load_events(path):
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    typed = {row["sequence"]: row for row in rows
             if row.get("event") == "typed_observation" and row.get("sequence") in (2, 3)}
    if set(typed) != {2, 3}: raise ValueError("retained typed observations 2/3 missing")
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
             "final_admission_from_planner_result", "prepare_action_admission")
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
    missing = [name for name in names if name not in top]
    if missing: raise ValueError("current V39 source symbols missing: " + repr(missing))
    exec(compile(ast.Module(body=[top[name] for name in names], type_ignores=[]),
                 str(controller_path), "exec"), namespace)
    return namespace

def wait_event(observer, expected_type, deadline_seconds=2.0):
    deadline = time.monotonic() + deadline_seconds
    while time.monotonic() < deadline:
        if observer.pending_events(): event = observer.next_event()
        else:
            ready, _, _ = select.select([observer.fileno()], [], [],
                                         max(0, deadline - time.monotonic()))
            if not ready: break
            event = observer.next_event()
        if event.type == expected_type:
            return {"type": int(event.type), "keycode": int(event.detail),
                    "window": int(event.window.id), "observed_ns": time.perf_counter_ns()}
    return None

def key_down(observer, keycode):
    bitmap = observer.query_keymap()
    return bool(bitmap[keycode // 8] & (1 << (keycode % 8)))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--display", default=":132")
    args = parser.parse_args()
    if args.out.exists(): raise SystemExit("result leaf exists; refusing to overwrite")
    args.out.mkdir(parents=True)
    os.environ.setdefault("XAUTHORITY", "/dev/null")
    freeze = json.loads((HERE.parent / "FREEZE.json").read_text(encoding="utf-8"))
    raw = {"schema": "v39-visual-active-hold-xvfb-raw-a01-v1",
           "status": "STOP", "errors": [], "display": args.display,
           "scope": "two monitor/admission boundary cases with one actual Xvfb-held key each; no game/model/physical input",
           "input_pair": {}, "arms": {}, "cleanup": {}}
    xvfb = observer = None
    owners = []
    try:
        for filename, expected in freeze["source_sha256"].items():
            if sha(HERE / filename) != expected: raise ValueError("source hash mismatch: " + filename)
        for filename, expected in freeze["input_sha256"].items():
            if sha(HERE.parent / "INPUTS" / filename) != expected: raise ValueError("input hash mismatch: " + filename)
        if sha(HERE / "candidate.py") != freeze["candidate_sha256"]:
            raise ValueError("candidate hash mismatch")
        typed = load_events(HERE.parent / "INPUTS" / "events.jsonl")
        source = typed[2]
        actual_current = typed[3]
        if (source["signals"]["health"]["value"] != 97 or
                source["signals"]["ammo"]["value"] != 48 or
                actual_current["signals"]["health"]["value"] != 97 or
                actual_current["signals"]["ammo"]["value"] != 48 or
                source["pointer_binding"] != actual_current["pointer_binding"] or
                source["frame_rgb_sha256"] == actual_current["frame_rgb_sha256"]):
            raise ValueError("retained 2→3 frame/signal boundary does not match freeze")
        raw["input_pair"] = {
            "source_sequence": 2, "current_sequence": 3,
            "source_health_ammo": [97, 48], "current_health_ammo": [97, 48],
            "pointer_binding_equal": True,
            "source_frame_rgb_sha256": source["frame_rgb_sha256"],
            "current_frame_rgb_sha256": actual_current["frame_rgb_sha256"],
            "source_png_sha256": sha(HERE.parent / "INPUTS" / "002.png"),
            "current_png_sha256": sha(HERE.parent / "INPUTS" / "003.png"),
        }
        runtime = load_runtime()
        from Xlib import X, XK, display
        import sys as _sys, types as _types
        executor = _types.ModuleType("executor_v3")
        executor.Cancelled = type("Cancelled", (Exception,), {})
        executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
        _sys.modules["executor_v3"] = executor
        from input_transition_owner_v4 import InputOwner
        xvfb = subprocess.Popen(["Xvfb", args.display, "-screen", "0", "640x480x24",
                                 "-nolisten", "tcp", "-noreset", "-ac"],
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.PIPE)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if xvfb.poll() is not None: raise RuntimeError("Xvfb exited during startup")
            try:
                observer = display.Display(args.display)
                break
            except Exception:
                time.sleep(0.05)
        if observer is None: raise TimeoutError("Xvfb observer connection timed out")
        root = observer.screen().root
        keycode = int(observer.keysym_to_keycode(XK.string_to_keysym("a")))
        if not keycode: raise RuntimeError("X keycode for a unavailable")
        health_reader = SignalReader("health")
        ammo_reader = SignalReader("ammo")
        validity = {"signal_id": "health", "critical_health_minimum": 45,
                    "maximum_health_loss": 8, "max_source_age_ms": 1000}
        source_health = source["signals"]["health"]
        source_ammo = source["signals"]["ammo"]
        health_guard = runtime["ObservableSignalGuard"](
            runtime["guard_spec"](validity, source_health, "active-hold-a01"),
            source_health, source["pointer_binding"])
        ammo_guard = runtime["ObservableSignalGuard"](
            runtime["ammo_guard_spec"](source_ammo, "active-hold-a01", 1000),
            source_ammo, source["pointer_binding"])
        arms = (("visual_changed", actual_current, True),
                ("same_frame_control", copy.deepcopy(actual_current), False))
        for index, (label, current, changed_arm) in enumerate(arms, 1):
            current = copy.deepcopy(current)
            if not changed_arm:
                current["frame_rgb_sha256"] = source["frame_rgb_sha256"]
            pair_monitor = runtime["DoomCoverSignalPairMonitor"](
                {"health": health_guard, "ammo": ammo_guard}, health_reader, ammo_reader)
            win = root.create_window(20 + index * 10, 20 + index * 10, 320, 200,
                                     0, observer.screen().root_depth, X.InputOutput,
                                     X.CopyFromParent,
                                     event_mask=X.KeyPressMask | X.KeyReleaseMask)
            win.map(); observer.sync(); observer.set_input_focus(win, X.RevertToParent, X.CurrentTime); observer.sync()
            focus_deadline = time.monotonic() + 1
            while time.monotonic() < focus_deadline:
                focused = observer.get_input_focus().focus
                if getattr(focused, "id", focused) == win.id: break
                time.sleep(0.01)
            else: raise RuntimeError("Xvfb test-client focus was not established")
            while observer.pending_events(): observer.next_event()
            lease = Lease(int(win.id), TOKEN + ":" + label)
            owner = InputOwner(args.display)
            owners.append(owner)
            admission = owner.call("down", lease, "a")
            press = wait_event(observer, X.KeyPress)
            if (not press or press["keycode"] != keycode or press["window"] != win.id):
                raise RuntimeError("actual Xvfb keydown did not reach focused client")
            down_before = key_down(observer, keycode)
            client = FakeClient(pair_monitor, current,
                                lambda: key_down(observer, keycode))
            planner = runtime["PersistentPlannerAdapter"](
                client, model="frozen-mock", effort="low", cwd=".",
                base_instructions="visual active hold boundary fixture")
            planner.start_session()
            with tempfile.TemporaryDirectory(prefix="v39-visual-active-hold-") as temp_root:
                handle = runtime["begin_model_turn"](
                    planner, Path(temp_root), HERE.parent / "INPUTS" / "002.png", [],
                    source_health["value"], source_ammo["value"], {}, SCHEMA)
                planner_result = planner.await_turn(handle)
            key_while_pending = client.key_down_during_pending
            terminal_ns = current["capture_ns"] + 50_000_000
            receipt = runtime["final_admission_from_planner_result"](
                planner_result, terminal_ns, None, terminal_ns + 1)
            prepared = runtime["prepare_action_admission"](
                receipt, planner_result.answer, AUTHORED,
                health_reader.read(source), ammo_reader.read(source),
                health_reader.read(current), ammo_reader.read(current), terminal_ns + 2)
            down_after_answer = key_down(observer, keycode)
            owner.close()
            owners.remove(owner)
            release = wait_event(observer, X.KeyRelease)
            up_after_close = not key_down(observer, keycode)
            inner = owner._inner
            records = list(inner.records)
            close_record = next((row for row in reversed(records)
                                 if row.get("event") == "owner_release"), None)
            raw["arms"][label] = {
                "current_frame_rgb_sha256": current["frame_rgb_sha256"],
                "monitor_invalidation": client.invalidation,
                "monitor_soft_event_count": pair_monitor.soft_event_count,
                "health_guard_outcome": health_guard.evaluate(current["signals"]["health"]),
                "ammo_guard_outcome": ammo_guard.evaluate(current["signals"]["ammo"]),
                "planner_events": client.events,
                "answer_eligible": planner_result.answer_eligible,
                "final_status": prepared["status"],
                "final_reason": prepared["action_validity"]["reason"],
                "executor_admission": prepared["executor_admission"],
                "input_authority_admitted": prepared["input_authority_admitted"],
                "admission": admission,
                "keycode": keycode,
                "client_window": int(win.id),
                "key_press_event": press,
                "key_down_before_new_frame": down_before,
                "key_down_during_pending_turn": key_while_pending,
                "key_down_after_answer": down_after_answer,
                "owner_close_record": close_record,
                "owner_records": records,
                "key_release_event": release,
                "observer_key_up_after_close": up_after_close,
                "owner_closed": inner.closed,
                "owner_stopped": inner.stopped.is_set(),
                "owner_thread_alive": inner.thread.is_alive(),
            }
            if not down_after_answer or not up_after_close:
                raise RuntimeError("Xvfb owner/key state did not match the intended hold/close lifecycle")
        raw["status"] = "CANDIDATE_COMPLETE"
    except BaseException as exc:
        raw["errors"].append(f"{type(exc).__name__}: {exc}")
    finally:
        for owner in list(owners):
            try: owner.close()
            except BaseException as exc: raw["cleanup"]["owner_close_error"] = f"{type(exc).__name__}: {exc}"
        if observer is not None:
            try: observer.close()
            except BaseException as exc: raw["cleanup"]["observer_close_error"] = f"{type(exc).__name__}: {exc}"
        if xvfb is not None:
            try:
                xvfb.terminate(); xvfb.wait(timeout=5)
                raw["cleanup"]["xvfb_exit"] = xvfb.returncode
            except BaseException as exc:
                raw["cleanup"]["xvfb_error"] = f"{type(exc).__name__}: {exc}"
                xvfb.kill(); xvfb.wait(timeout=5)
                raw["cleanup"]["xvfb_exit"] = xvfb.returncode
        if raw["errors"] or raw["cleanup"] or len(raw["arms"]) != 2:
            raw["status"] = "STOP"
        (args.out / "RAW.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n",
                                          encoding="utf-8")
    print(json.dumps({"status": raw["status"], "errors": raw["errors"],
                      "arms": list(raw["arms"]), "cleanup": raw["cleanup"]}, sort_keys=True))
    if raw["status"] != "CANDIDATE_COMPLETE": raise SystemExit(1)

if __name__ == "__main__": main()
