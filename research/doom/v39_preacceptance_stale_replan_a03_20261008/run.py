"""Compose a fresh planner answer through current-main Executor admission only."""
import ast
import copy
import hashlib
import importlib.util
import json
import tempfile
import sys
import threading
import time
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def git_blob(path):
    import subprocess
    relative = path.relative_to(REPO).as_posix()
    return subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", f"HEAD:{relative}"], text=True).strip()


def extract_class_method(path, class_name, method_name, namespace):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    cls = next(node for node in tree.body
               if isinstance(node, ast.ClassDef) and node.name == class_name)
    method = next(node for node in cls.body
                  if isinstance(node, ast.FunctionDef) and node.name == method_name)
    module = ast.fix_missing_locations(ast.Module(body=[
        ast.ClassDef(name="Harness", bases=[], keywords=[], body=[method], decorator_list=[])
    ], type_ignores=[]))
    scope = dict(namespace)
    exec(compile(module, str(path), "exec"), scope)
    return scope["Harness"]


def extract_function(path, function_name, namespace):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    function = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == function_name)
    scope = dict(namespace)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])),
                 str(path), "exec"), scope)
    return scope[function_name]


def matched_pair(old, binding, image_path):
    with Image.open(image_path) as opened:
        rgb = opened.convert("RGB")
        digest = hashlib.sha256(rgb.tobytes()).hexdigest()
    seq, capture_ns = 2, 200
    signals = {}
    for name, value in (("health", 86), ("ammo", 12)):
        signals[name] = {"format": "observable-signal-v1", "status": "observed",
                         "signal_id": name, "value": value, "sequence": seq,
                         "capture_ns": capture_ns, "binding": binding,
                         "wad_sha256": "b" * 64}
    typed = {"event": "typed_observation", "schema": "doom-typed-observation-v1",
             "id": "plan", "step": 0, "sequence": seq, "capture_ns": capture_ns,
             "pointer_binding": binding, "signals": signals,
             "frame_rgb_sha256": digest, "artifact_published": False,
             "grants_input_authority": False}
    full = {"event": "observation", "id": "plan", "step": 0,
            "sequence": seq, "capture_ns": capture_ns, "pointer_binding": binding,
            "image": str(image_path), "frame_rgb_sha256": digest, "exact": True}
    rejection = {"event": "rejected",
                 "reason": "latest observation sequence required before input"}
    if (rejection["reason"] != "latest observation sequence required before input" or
            type(full["sequence"]) is not int or full["sequence"] <= old["sequence"] or
            full["capture_ns"] <= old["capture_ns"] or
            full["pointer_binding"] != old["pointer_binding"] or
            typed["event"] != "typed_observation" or
            typed["schema"] != "doom-typed-observation-v1" or
            any(typed.get(key) != full.get(key)
                for key in ("id", "step", "sequence", "capture_ns",
                            "pointer_binding", "frame_rgb_sha256")) or
            set(signals) != {"health", "ammo"}):
        raise ValueError("fresh typed/full pair failed exact-epoch checks")
    for name, minimum in (("health", 1), ("ammo", 0)):
        row = signals[name]
        if (row["status"] != "observed" or type(row["value"]) is not int or
                row["value"] < minimum or row["sequence"] != full["sequence"] or
                row["capture_ns"] != full["capture_ns"] or
                row["binding"] != full["pointer_binding"]):
            raise ValueError(f"invalid exact typed {name}")
    return full, typed, signals


class FakePlannerClient:
    def __init__(self):
        self.turns = []
        self.answers = [
            {"commands": [{"action": "advance_fire", "extent": "short"}]},
            {"commands": [{"action": "retreat_fire", "extent": "short"}]},
        ]

    def start_thread(self, **_kwargs):
        return {"thread": {"id": "thread-a03"}}

    def start_turn(self, thread_id, inputs, **kwargs):
        self.turns.append({"thread_id": thread_id, "inputs": inputs,
                           "schema": kwargs["outputSchema"]})
        return {"turn": {"id": f"turn-{len(self.turns)}"}}

    def wait_turn_completed(self, _thread_id, turn_id, timeout=120):
        answer = self.answers[int(turn_id.rsplit("-", 1)[1]) - 1]
        return {"turn": {"status": "completed", "items": [
            {"type": "agentMessage", "text": json.dumps(answer)}]}}

    def latest_turn_usage(self, _thread_id, _turn_id):
        return {"input_tokens": 1, "output_tokens": 1}


class FakeBackend:
    def __init__(self, sequence, expected_steps):
        self.sequence = sequence
        self.expected_steps = expected_steps
        self.validate_calls = 0
        self.lease = None

    def validate(self, steps):
        self.validate_calls += 1
        if steps != self.expected_steps:
            raise AssertionError("backend received steps other than the exact fresh compilation")


class FakeLease:
    def __init__(self, valid_until_ns):
        self.valid_until_ns = valid_until_ns
        self.intent_token = "inert-fixture-token"

    def check(self):
        if self.valid_until_ns <= time.perf_counter_ns():
            raise ValueError("fixture lease expired")


class InertThread:
    all_threads = []

    def __init__(self, target, args, daemon):
        self.target, self.args, self.daemon = target, args, daemon
        self.started = False
        self.all_threads.append(self)

    def start(self):
        self.started = True  # Deliberately do not invoke target or any input.


def make_executor(submit_class, sequence, expected_steps):
    executor = submit_class()
    executor.lock = threading.RLock()
    executor.closed = False
    executor.active = None
    executor.backend = FakeBackend(sequence, expected_steps)
    executor.used_ids = set()
    executor.admission_callback_ids = set()
    executor.terminal_publication_errors = {}
    executor.admission_publication_errors = {}
    executor.emit_events = []
    executor.emit = executor.emit_events.append
    executor._run = lambda *_args: None
    return executor


def run():
    paths = {
        "research/doom/map01_overlap_controller_v39.py": REPO / "research/doom/map01_overlap_controller_v39.py",
        "research/live_control/executor_v12.py": REPO / "research/live_control/executor_v12.py",
        "research/live_control/executor_v11.py": REPO / "research/live_control/executor_v11.py",
        "research/live_control/persistent_planner_adapter_v2.py": REPO / "research/live_control/persistent_planner_adapter_v2.py",
    }
    for relative, path in paths.items():
        wanted = FREEZE["sources"][relative]
        actual = git_blob(path)
        if actual != wanted:
            raise AssertionError(f"source drift: {relative}: {actual} != {wanted}")

    controller_path = paths["research/doom/map01_overlap_controller_v39.py"]
    executor_path = paths["research/live_control/executor_v12.py"]
    program_path = paths["research/live_control/executor_v11.py"]
    compile_commands = extract_function(controller_path, "compile_commands", {})
    begin_model_turn = extract_function(
        controller_path, "begin_model_turn", {"json": json, "win": lambda path: str(path)})
    adapter_path = paths["research/live_control/persistent_planner_adapter_v2.py"]
    spec = importlib.util.spec_from_file_location("adapter_a03", adapter_path)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    submit_class = extract_class_method(
        executor_path, "Executor", "submit",
        {"copy": copy, "threading": type("ThreadingStub", (), {"Thread": InertThread}),
         "time": time, "Lease": FakeLease,
         "program_sha256": extract_function(program_path, "program_sha256", {"json": json,
             "hashlib": hashlib})})

    with tempfile.TemporaryDirectory(prefix="v39-a03-", dir=str(HERE)) as temp_name:
        temp = Path(temp_name)
        old_image = temp / "sequence-1.png"
        fresh_image = temp / "sequence-2.png"
        Image.new("RGB", (8, 8), (1, 2, 3)).save(old_image)
        Image.new("RGB", (8, 8), (4, 5, 6)).save(fresh_image)
        binding = {"focus": 1, "surface": 7, "geometry": [0, 0, 640, 480]}
        old = {"sequence": 1, "capture_ns": 100, "image": str(old_image),
               "pointer_binding": binding}
        client = FakePlannerClient()
        planner = adapter.PersistentPlannerAdapter(
            client, model="fixture-model", effort="low", cwd=str(REPO),
            base_instructions="A03 inert fixture")
        planner.start_session()
        (temp / "turn-old").mkdir()
        old_handle = begin_model_turn(planner, temp / "turn-old", old_image, [],
                                      88, 12, {}, {"type": "object"})
        old_result = planner.await_turn(old_handle)
        if not old_result.answer_eligible:
            raise AssertionError("fixture old turn did not complete")

        old_steps = compile_commands(old_result.answer["commands"])
        old_executor = make_executor(submit_class, sequence=2,
                                     expected_steps=old_steps)
        InertThread.all_threads.clear()
        try:
            old_executor.submit("stale-seq-1", old_steps, 1,
                                time.perf_counter_ns() + 10_000_000_000)
        except ValueError as error:
            stale_reason = str(error)
        else:
            raise AssertionError("stale sequence unexpectedly admitted")
        if (stale_reason != "latest observation sequence required before input" or
                old_executor.emit_events or old_executor.backend.validate_calls or
                any(thread.started for thread in InertThread.all_threads)):
            raise AssertionError("stale refusal crossed the admission/worker boundary")

        full, typed, signals = matched_pair(old, binding, fresh_image)
        fresh = {"observation": full, "typed": typed, "health": signals["health"]["value"],
                 "ammo": signals["ammo"]["value"]}
        (temp / "turn-fresh").mkdir()
        fresh_handle = begin_model_turn(planner, temp / "turn-fresh", fresh_image, [],
                                       fresh["health"], fresh["ammo"], {},
                                       {"type": "object"})
        fresh_result = planner.await_turn(fresh_handle)
        client_turn = client.turns[1]
        prompt = client_turn["inputs"][0]["text"]
        if (not fresh_result.answer_eligible or len(client.turns) != 2 or
                "Current locally verified health: 86." not in prompt or
                "Current locally verified ammo: 12." not in prompt or
                client_turn["inputs"][1]["path"] != str(fresh_image)):
            raise AssertionError("fresh planner turn did not consume the matched sequence-2 frame/HUD")

        fresh_steps = compile_commands(fresh_result.answer["commands"])
        expected_steps = [{"op": "hold", "keys": ["Down", "space"],
                           "duration_ms": 300}]
        if fresh_steps != expected_steps or fresh_steps == old_steps:
            raise AssertionError("only the fresh planner answer must reach the current compiler")
        InertThread.all_threads.clear()
        stable_executor = make_executor(submit_class, sequence=2,
                                       expected_steps=fresh_steps)
        stable_executor.submit("fresh-seq-2", fresh_steps, 2,
                               time.perf_counter_ns() + 10_000_000_000)
        if (len(stable_executor.emit_events) != 1 or
                stable_executor.emit_events[0].get("event") != "accepted" or
                stable_executor.backend.validate_calls != 1 or
                len(InertThread.all_threads) != 1 or
                not InertThread.all_threads[0].started):
            raise AssertionError("fresh sequence-2 action did not reach exactly one admission")

        InertThread.all_threads.clear()
        drift_executor = make_executor(submit_class, sequence=3,
                                       expected_steps=fresh_steps)
        try:
            drift_executor.submit("second-drift-seq-2", fresh_steps, 2,
                                  time.perf_counter_ns() + 10_000_000_000)
        except ValueError as error:
            drift_reason = str(error)
        else:
            raise AssertionError("second sequence advance was not rejected")
        if (drift_reason != "latest observation sequence required before input" or
                drift_executor.emit_events or drift_executor.backend.validate_calls or
                any(thread.started for thread in InertThread.all_threads)):
            raise AssertionError("second drift crossed admission/worker boundary")

        accepted_projection = {key: stable_executor.emit_events[0][key]
                               for key in ("event", "id", "steps", "program_sha256",
                                           "intent_token")}
        result = {
            "experiment_id": FREEZE["experiment_id"],
            "disposition": "PASS_SYNTHETIC_FRESH_ANSWER_ADMISSION_BOUNDARY",
            "main_commit": FREEZE["main_commit"],
            "source_blobs": FREEZE["sources"],
            "stale_sequence_1": {"reason": stale_reason, "submit_attempts": 1,
                                 "compiled_steps": old_steps,
                                 "accepted_events": len(old_executor.emit_events),
                                 "backend_validation_calls": old_executor.backend.validate_calls,
                                 "worker_starts": 0,
                                 "old_plan_retried_after_rejection": False},
            "fresh_sequence_2": {"health": fresh["health"], "ammo": fresh["ammo"],
                                 "image_rgb_sha256": typed["frame_rgb_sha256"],
                                 "turn_count": len(client.turns), "compiled_steps": fresh_steps,
                                 "accepted_events": [accepted_projection],
                                 "backend_validation_calls": stable_executor.backend.validate_calls,
                                 "worker_started_inertly": True, "physical_input": False},
            "second_drift_sequence_3": {"expected_sequence": 2, "backend_sequence": 3,
                                         "reason": drift_reason, "accepted_events": len(drift_executor.emit_events),
                                         "backend_validation_calls": drift_executor.backend.validate_calls,
                                         "worker_starts": 0},
            "controls": {"stale_pre_acceptance_refused": True,
                         "fresh_exact_sequence_admitted_once": True,
                         "subsequent_sequence_advance_refused": True,
                         "old_action_not_retried_after_refusal": True},
            "scope": "method-level synthetic composition only; exact submit method, inert Lease/backend/thread boundaries",
        }
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": result["disposition"],
                      "stale_accepted": result["stale_sequence_1"]["accepted_events"],
                      "fresh_accepted": len(result["fresh_sequence_2"]["accepted_events"]),
                      "second_drift_accepted": result["second_drift_sequence_3"]["accepted_events"],
                      "worker_started_inertly": result["fresh_sequence_2"]["worker_started_inertly"]},
                     sort_keys=True))


if __name__ == "__main__":
    run()
