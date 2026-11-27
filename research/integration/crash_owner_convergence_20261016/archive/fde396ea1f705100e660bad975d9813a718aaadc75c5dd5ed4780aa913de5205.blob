"""One-shot current-main action-validity to Xvfb Executor-acceptance boundary."""
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
TOKEN = "v39-action-validity-executor-a01"
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
        if self.cancel.is_set():
            raise RuntimeError("cancelled")
        if time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("expired")

    def record_interruption(self, row):
        self.interruption = row


class FakeClient:
    def __init__(self, current, label):
        self.current = current
        self.label = label
        self.events = []
        self.inputs = []

    def start_thread(self, **kwargs):
        return {"thread": {"id": "action-validity-a01"}}

    def start_turn(self, thread_id, inputs, **kwargs):
        self.inputs.append(inputs)
        self.events.append("planner_turn_started")
        return {"turn": {"id": "action-validity-turn"}}

    def wait_turn_completed(self, thread_id, turn_id, timeout=120):
        self.events.append("retained_sequence_3_observed_while_turn_pending")
        self.events.append("completed_structured_answer_returned")
        return {"turn": {"status": "completed", "items": [
            {"type": "agentMessage", "text": json.dumps(ACTION)}]}}

    def latest_turn_usage(self, thread_id, turn_id):
        return {"input_tokens": 0, "output_tokens": 0}


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
    from final_action_admission_v2 import (
        decide_final_admission, record_action_validity, record_executor_admission)
    controller_path = HERE / "map01_overlap_controller_v39.py"
    tree = ast.parse(controller_path.read_text(encoding="utf-8"))
    top = {node.name: node for node in tree.body
           if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    names = ("final_admission_from_planner_result", "prepare_action_admission",
             "bind_first_plan_acceptance", "begin_model_turn")
    missing = [name for name in names if name not in top]
    if missing:
        raise ValueError("current V39 symbols missing: " + repr(missing))
    namespace = {
        "json": json, "time": time, "Path": Path,
        "PersistentPlannerAdapter": PersistentPlannerAdapter,
        "SNAPSHOT_FORMAT": SNAPSHOT_FORMAT,
        "evaluate_action_validity": evaluate_action_validity,
        "bindings_equal_exact": bindings_equal_exact,
        "build_action_contract": build_contract,
        "decide_final_admission": decide_final_admission,
        "record_action_validity": record_action_validity,
        "record_executor_admission": record_executor_admission,
        "win": lambda value: str(value),
    }
    exec(compile(ast.Module(body=[top[name] for name in names], type_ignores=[]),
                 str(controller_path), "exec"), namespace)
    return namespace


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--display", default=":134")
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("result leaf exists; refusing to overwrite")
    args.out.mkdir(parents=True)
    os.environ.setdefault("XAUTHORITY", "/dev/null")
    freeze = json.loads((HERE.parent / "FREEZE.json").read_text(encoding="utf-8"))
    raw = {"schema": "v39-action-validity-executor-acceptance-xvfb-raw-a01-v1",
           "status": "STOP", "errors": [], "display": args.display,
           "scope": "current V39 final/action-validity/first-acceptance chain with real Xvfb owner key events; no game/model/physical input",
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
        retained_source, retained_current = typed[2], typed[3]
        if (retained_source["signals"]["health"]["value"] != 97
                or retained_source["signals"]["ammo"]["value"] != 48
                or retained_current["signals"]["health"]["value"] != 97
                or retained_current["signals"]["ammo"]["value"] != 48
                or retained_source["pointer_binding"] != retained_current["pointer_binding"]):
            raise ValueError("retained typed pair mismatch")
        raw["input_pair"] = {
            "source_sequence": 2, "current_sequence": 3,
            "source_health_ammo": [97, 48], "retained_current_health_ammo": [97, 48],
            "pointer_binding_equal": True,
            "source_frame_rgb_sha256": retained_source["frame_rgb_sha256"],
            "current_frame_rgb_sha256": retained_current["frame_rgb_sha256"],
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
        for index, (label, current_health) in enumerate(
                (("health_unchanged_acceptance", 97),
                 ("health_drop_rejected", 80)), 1):
            base_ns = time.perf_counter_ns()
            source = copy.deepcopy(retained_source)
            current = copy.deepcopy(retained_current)
            source_capture = base_ns - 200_000_000
            current_capture = base_ns - 20_000_000
            source["capture_ns"] = source_capture
            current["capture_ns"] = current_capture
            for signal in source["signals"].values():
                signal["capture_ns"] = source_capture
            for signal in current["signals"].values():
                signal["capture_ns"] = current_capture
            current["signals"]["health"]["value"] = current_health
            win = root.create_window(40 + index * 10, 40 + index * 10, 320, 200,
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
            xvfb_binding = {"focus": int(win.id), "surface": int(win.id),
                            "geometry": [0, 0, 320, 200]}
            source["pointer_binding"] = copy.deepcopy(xvfb_binding)
            current["pointer_binding"] = copy.deepcopy(xvfb_binding)
            for signal in source["signals"].values():
                signal["binding"] = copy.deepcopy(xvfb_binding)
            for signal in current["signals"].values():
                signal["binding"] = copy.deepcopy(xvfb_binding)
            while observer.pending_events():
                observer.next_event()
            lease = Lease(int(win.id), TOKEN + ":" + label)
            owner = InputOwner(args.display)
            owners.append(owner)
            client = FakeClient(current, label)
            planner = runtime["PersistentPlannerAdapter"](
                client, model="frozen-mock", effort="low", cwd=".",
                base_instructions="V39 action-validity and first acceptance boundary")
            planner.start_session()
            with tempfile.TemporaryDirectory(prefix="v39-action-validity-") as temp_root:
                handle = runtime["begin_model_turn"](
                    planner, Path(temp_root), HERE.parent / "INPUTS" / "002.png", [],
                    source["signals"]["health"]["value"],
                    source["signals"]["ammo"]["value"], {}, SCHEMA)
                planner_result = planner.await_turn(handle)
            terminal_ns = time.perf_counter_ns()
            planner_admission = runtime["final_admission_from_planner_result"](
                planner_result, terminal_ns, None, terminal_ns + 1)
            prepared = runtime["prepare_action_admission"](
                planner_admission, planner_result.answer, AUTHORED,
                source["signals"]["health"], source["signals"]["ammo"],
                current["signals"]["health"], current["signals"]["ammo"],
                time.perf_counter_ns())
            input_admission = None
            press = None
            accepted = None
            release = None
            release_event = None
            if prepared["status"] == "READY_FOR_FRESH_EXECUTOR_ADMISSION":
                input_admission = owner.call("down", lease, "a")
                press = wait_event(observer, X.KeyPress)
                if not press or press["keycode"] != keycode or press["window"] != win.id:
                    raise RuntimeError("validated action did not produce the expected Xvfb keydown")
                accepted_ns = time.perf_counter_ns()
                accepted = runtime["bind_first_plan_acceptance"](
                    prepared, {"id": "accepted-" + label,
                               "accepted_ns": accepted_ns})
                release = owner.call("up", lease, "a")
                release_event = wait_event(observer, X.KeyRelease)
                if not release or release.get("owner_thread_keyup_verified") is not True:
                    raise RuntimeError("explicit keyup did not have current-main V4 owner receipt")
            key_is_down = key_down(observer, keycode)
            inner = owner._inner
            owner.close()
            owners.remove(owner)
            up_after_close = not key_down(observer, keycode)
            close_record = next((row for row in reversed(inner.records)
                                 if row.get("event") == "owner_release"), None)
            raw["arms"][label] = {
                "health_value": current_health,
                "planner_answer_eligible": planner_result.answer_eligible,
                "planner_admission": planner_admission,
                "action_validity": prepared.get("action_validity"),
                "action_admission": prepared,
                "executor_acceptance_receipt": accepted,
                "input_admission": input_admission,
                "keycode": keycode,
                "client_window": int(win.id),
                "key_press_event": press,
                "key_release_transition": release,
                "key_release_event": release_event,
                "key_down_after_policy_chain": key_is_down,
                "observer_key_up_after_cleanup": up_after_close,
                "owner_close_record": close_record,
                "owner_closed": inner.closed,
                "owner_stopped": inner.stopped.is_set(),
                "owner_thread_alive": inner.thread.is_alive(),
            }
            if label == "health_unchanged_acceptance":
                if (planner_admission["status"] != "READY_FOR_ACTION_VALIDITY"
                        or prepared["status"] != "READY_FOR_FRESH_EXECUTOR_ADMISSION"
                        or prepared["action_validity"]["status"] != "VALID_CURRENT"
                        or accepted is None or accepted["status"] != "INPUT_ADMITTED"
                        or accepted["input_authority_admitted"] is not True
                        or press is None or not key_is_down
                        or release_event is None or not up_after_close):
                    raise RuntimeError("current action did not traverse validity, acceptance, and keyup")
            else:
                if (prepared["status"] != "REJECTED_ACTION_NOT_CURRENT"
                        or prepared["action_validity"]["action_may_proceed_to_executor_admission"] is not False
                        or accepted is not None or input_admission is not None
                        or press is not None or key_is_down
                        or not up_after_close):
                    raise RuntimeError("stale health did not fail closed before input admission")
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
