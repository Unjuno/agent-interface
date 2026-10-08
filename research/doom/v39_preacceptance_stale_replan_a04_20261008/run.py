"""Execute the exact producer-to-Executor stale-replan composition with inert edges."""
import ast
import copy
import hashlib
import importlib.util
import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MAIN = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))["main_commit"]
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
CONTROLLER = REPO / "research/doom/map01_overlap_controller_v39.py"
BACKEND = REPO / "research/doom/doom_typed_coast_backend_v1.py"
TYPED = REPO / "research/doom/doom_typed_observation_v1.py"
ADAPTER = REPO / "research/live_control/persistent_planner_adapter_v2.py"
EXECUTOR = REPO / "research/live_control/executor_v12.py"
PROGRAM = REPO / "research/live_control/executor_v11.py"
sys.path.insert(0, str(REPO / "research/live_control"))


def pinned_blob(path):
    rel = path.relative_to(REPO).as_posix()
    return subprocess.check_output(["git", "-C", str(REPO), "rev-parse", f"{MAIN}:{rel}"], text=True).strip()


def extract_function(path, name, scope):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    node = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == name)
    env = dict(scope)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(path), "exec"), env)
    return env[name]


def extract_submit(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    cls = next(item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == "Executor")
    method = next(item for item in cls.body if isinstance(item, ast.FunctionDef) and item.name == "submit")
    program_hash = extract_function(PROGRAM, "program_sha256", {"json": json, "hashlib": hashlib})
    class InertThread:
        all_threads = []
        def __init__(self, target, args, daemon):
            self.target, self.args, self.daemon, self.started = target, args, daemon, False
            self.all_threads.append(self)
        def start(self):
            self.started = True  # Exact Executor reaches start; worker/input body is not invoked.
    threading_stub = type("ThreadingStub", (), {"Thread": InertThread})
    module = ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(
        name="Harness", bases=[], keywords=[], body=[method], decorator_list=[])], type_ignores=[]))
    scope = {"copy": copy, "threading": threading_stub, "time": time,
             "Lease": FakeLease, "program_sha256": program_hash}
    exec(compile(module, str(path), "exec"), scope)
    return scope["Harness"], InertThread


def extract_wait(initial, incoming):
    tree = ast.parse(CONTROLLER.read_text(encoding="utf-8"))
    main = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == "main")
    wait_node = next(item for item in ast.walk(main)
                     if isinstance(item, ast.FunctionDef) and item.name == "wait")
    factory = ast.FunctionDef(
        name="factory",
        args=ast.arguments(posonlyargs=[], args=[ast.arg(arg="process"), ast.arg(arg="incoming"),
                                                   ast.arg(arg="initial")], kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=[ast.Assign(targets=[ast.Name(id="latest", ctx=ast.Store())], value=ast.Name(id="initial", ctx=ast.Load())),
              wait_node,
              ast.Return(value=ast.Tuple(elts=[ast.Name(id="wait", ctx=ast.Load()),
                  ast.Lambda(args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
                             body=ast.Name(id="latest", ctx=ast.Load()))], ctx=ast.Load()))], decorator_list=[])
    env = {"queue": queue, "time": time, "RuntimeError": RuntimeError}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[])), str(CONTROLLER), "exec"), env)
    class Process:
        @staticmethod
        def poll(): return None
    return env["factory"](Process(), incoming, initial)


def extract_begin_and_compile():
    return (extract_function(CONTROLLER, "begin_model_turn", {"json": json, "win": lambda path: str(path)}),
            extract_function(CONTROLLER, "compile_commands", {}))


def execute_exact_snapshot(out):
    spec = importlib.util.spec_from_file_location("a04_typed_observation", TYPED)
    typed_module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = typed_module
    spec.loader.exec_module(typed_module)
    tree = ast.parse(BACKEND.read_text(encoding="utf-8"))
    backend_cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Backend")
    snapshot = next(node for node in backend_cls.body if isinstance(node, ast.FunctionDef) and node.name == "snapshot")
    clocks = iter([150, 200, 205, 230, 240])
    typed_clocks = iter([210, 220])
    def typed_extract(frame, metadata, readers):
        return typed_module.extract_typed_observation(frame, metadata, readers, clock=typed_clocks.__next__)
    class Clock:
        @staticmethod
        def perf_counter_ns(): return next(clocks)
    binding = {"focus": 1, "surface": 7, "geometry": [0, 0, 640, 480]}
    frame_image = Image.new("RGB", (8, 8), (10, 20, 30))
    class ImageGrabStub:
        @staticmethod
        def grab(*, xdisplay):
            if xdisplay != ":fixture": raise AssertionError("unexpected display")
            return frame_image.copy()
    class Frame:
        def __init__(self, width, height, mode, payload): self.width, self.height, self.mode, self.payload = width, height, mode, payload
        def __eq__(self, other):
            return type(other) is Frame and (self.width, self.height, self.mode, self.payload) == (other.width, other.height, other.mode, other.payload)
    class Reader:
        def __init__(self, name, value): self.name, self.value = name, value
        def read_frame(self, metadata, _frame):
            return {"format": "doom-hud-number-v1", "status": "observed", "signal_id": self.name,
                    "value": self.value, "sequence": metadata["sequence"], "capture_ns": metadata["capture_ns"],
                    "binding": dict(metadata["pointer_binding"]), "wad_sha256": "b" * 64}
    class Session:
        name = ":fixture"
        @staticmethod
        def context(): return {"window_id": 4}
    class Encoder:
        def __init__(self): self.source = None
        def encode(self, source, **_kwargs): self.source = source; return b"fixture-packet"
    class Decoder:
        def __init__(self, encoder): self.encoder = encoder
        def accept(self, _packet): return self.encoder.source
    class Images:
        def publish(self, frame):
            path = out / "sequence-2.png"
            Image.frombytes(frame.mode, (frame.width, frame.height), frame.payload).save(path)
            return {"image": str(path), "artifact_published": True}
    rows = []
    class Harness:
        def __init__(self):
            self.binding_value, self.session, self.out, self.emit = binding, Session(), out, rows.append
            self.signal_readers = {"health": Reader("health", 86), "ammo": Reader("ammo", 12)}
            self.sequence, self.encoder, self.images = 1, Encoder(), Images()
            self.decoder, self.observed_focus, self.observed_pointer = Decoder(self.encoder), None, None
        def binding(self): return dict(self.binding_value)
    env = {"time": Clock, "extract_typed_observation": typed_extract,
           "ImageGrab": ImageGrabStub, "Frame": Frame}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[snapshot], type_ignores=[])), str(BACKEND), "exec"), env)
    env["snapshot"](Harness(), "plan", 0)
    if [row.get("event") for row in rows] != ["typed_observation", "observation"]:
        raise AssertionError("exact producer event order changed")
    return rows


class TypedCapture:
    event_types = frozenset({"typed_observation"})
    def __init__(self): self.event = None
    def observe(self, row): self.event = row


class FakePlannerClient:
    def __init__(self):
        self.turns = []
        self.answers = [
            {"commands": [{"action": "advance_fire", "extent": "short"}]},
            {"commands": [{"action": "retreat_fire", "extent": "short"}]},
        ]
    def start_thread(self, **_kwargs): return {"thread": {"id": "thread-a04"}}
    def start_turn(self, thread_id, inputs, **kwargs):
        self.turns.append({"thread_id": thread_id, "inputs": inputs, "schema": kwargs["outputSchema"]})
        return {"turn": {"id": f"turn-{len(self.turns)}"}}
    def wait_turn_completed(self, _thread_id, turn_id, timeout=120):
        answer = self.answers[int(turn_id.rsplit("-", 1)[1]) - 1]
        return {"turn": {"status": "completed", "items": [
            {"type": "agentMessage", "text": json.dumps(answer)}]}}
    def latest_turn_usage(self, _thread_id, _turn_id): return {"input_tokens": 1, "output_tokens": 1}


class FakeLease:
    def __init__(self, valid_until_ns): self.valid_until_ns, self.intent_token = valid_until_ns, "a04-inert-token"
    def check(self):
        if self.valid_until_ns <= time.perf_counter_ns(): raise ValueError("fixture lease expired")


class FakeBackend:
    def __init__(self, sequence, expected_steps):
        self.sequence, self.expected_steps, self.validate_calls, self.lease = sequence, expected_steps, 0, None
    def validate(self, steps):
        self.validate_calls += 1
        if steps != self.expected_steps: raise AssertionError("unexpected steps reached backend validation")


def make_executor(submit_class, sequence, expected_steps):
    executor = submit_class()
    executor.lock, executor.closed, executor.active = threading.RLock(), False, None
    executor.backend = FakeBackend(sequence, expected_steps)
    executor.used_ids, executor.admission_callback_ids = set(), set()
    executor.terminal_publication_errors, executor.admission_publication_errors = {}, {}
    executor.emit_events, executor.emit = [], None
    executor.emit = executor.emit_events.append
    executor._run = lambda *_args: None
    return executor


def recover(rejection, previous, wait, capture, timeout=0.5):
    if (rejection.get("event") != "rejected" or
            rejection.get("reason") != "latest observation sequence required before input"):
        raise ValueError("not the exact stale-sequence rejection")
    fresh = wait(lambda row: row.get("event") == "observation" and
                 type(row.get("sequence")) is int and row["sequence"] > previous["sequence"],
                 timeout=timeout, observation_monitor=capture)
    typed, signals = capture.event, capture.event.get("signals", {}) if capture.event else {}
    keys = ("id", "step", "sequence", "capture_ns", "pointer_binding", "frame_rgb_sha256")
    if (not typed or typed.get("schema") != "doom-typed-observation-v1" or
            typed.get("event") != "typed_observation" or
            any(typed.get(k) != fresh.get(k) for k in keys) or
            fresh["capture_ns"] <= previous["capture_ns"] or
            fresh["pointer_binding"] != previous["pointer_binding"] or
            typed.get("artifact_published") is not False or
            typed.get("grants_input_authority") is not False or set(signals) != {"health", "ammo"}):
        raise ValueError("typed/full pair mismatch")
    for name, minimum in (("health", 1), ("ammo", 0)):
        row = signals[name]
        if (row.get("status") != "observed" or type(row.get("value")) is not int or row["value"] < minimum or
                row.get("sequence") != fresh["sequence"] or row.get("capture_ns") != fresh["capture_ns"] or
                row.get("binding") != fresh["pointer_binding"]):
            raise ValueError(f"invalid {name} signal")
    return fresh, typed, signals


def run_case():
    source_hashes = {}
    for path, expected in FREEZE["sources"].items():
        actual = pinned_blob(REPO / path)
        if actual != expected: raise AssertionError(f"source drift {path}: {actual} != {expected}")
        source_hashes[path] = actual
    begin_turn, compile_commands = extract_begin_and_compile()
    submit_class, inert_thread = extract_submit(EXECUTOR)
    spec = importlib.util.spec_from_file_location("a04_planner_adapter", ADAPTER)
    adapter = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = adapter
    spec.loader.exec_module(adapter)

    with __import__("tempfile").TemporaryDirectory(prefix="v39-a04-", dir=str(HERE)) as raw:
        temp = Path(raw)
        old_image = temp / "sequence-1.png"
        Image.new("RGB", (8, 8), (1, 2, 3)).save(old_image)
        binding = {"focus": 1, "surface": 7, "geometry": [0, 0, 640, 480]}
        previous = {"event": "observation", "id": "plan", "step": 0, "sequence": 1,
                    "capture_ns": 100, "image": str(old_image), "frame_rgb_sha256": "a" * 64,
                    "pointer_binding": binding}
        produced = execute_exact_snapshot(temp)
        typed, full = produced
        if (typed["sequence"] != 2 or full["sequence"] != 2 or
                typed["capture_ns"] != full["capture_ns"] or typed["pointer_binding"] != full["pointer_binding"] or
                typed["frame_rgb_sha256"] != full["frame_rgb_sha256"]):
            raise AssertionError("producer sequence-2 pair mismatch")

        client = FakePlannerClient()
        planner = adapter.PersistentPlannerAdapter(client, model="fixture-model", effort="low",
                                                   cwd=str(REPO), base_instructions="A04 inert fixture")
        planner.start_session()
        schema = {"type": "object"}
        turn1_dir = temp / "turn-1"; turn1_dir.mkdir()
        old_handle = begin_turn(planner, turn1_dir, old_image, [], 88, 12, {}, schema)
        old_result = planner.await_turn(old_handle)
        if not old_result.answer_eligible: raise AssertionError("first planner answer unavailable")
        old_steps = compile_commands(old_result.answer["commands"])

        inert_thread.all_threads.clear()
        stale = make_executor(submit_class, 2, old_steps)
        try:
            stale.submit("stale-seq-1", old_steps, 1, time.perf_counter_ns() + 10_000_000_000)
        except ValueError as exc:
            stale_reason = str(exc)
        else: raise AssertionError("sequence-1 action unexpectedly admitted")
        if (stale_reason != "latest observation sequence required before input" or stale.emit_events or
                stale.backend.validate_calls or any(t.started for t in inert_thread.all_threads)):
            raise AssertionError("stale answer crossed Executor admission boundary")

        incoming = queue.Queue()
        incoming.put({"event": "rejected", "reason": stale_reason})
        incoming.put(typed); incoming.put(full)
        wait, latest = extract_wait(previous, incoming)
        rejection = incoming.get_nowait()
        capture = TypedCapture()
        fresh, fresh_typed, signals = recover(rejection, previous, wait, capture)
        if latest() != fresh: raise AssertionError("controller wait did not advance to full observation")
        turn2_dir = temp / "turn-2"; turn2_dir.mkdir()
        new_handle = begin_turn(planner, turn2_dir, Path(fresh["image"]), [],
                                signals["health"]["value"], signals["ammo"]["value"], {}, schema)
        new_result = planner.await_turn(new_handle)
        prompt = client.turns[1]["inputs"][0]["text"]
        if (not new_result.answer_eligible or len(client.turns) != 2 or
                "Current locally verified health: 86." not in prompt or
                "Current locally verified ammo: 12." not in prompt or
                client.turns[1]["inputs"][1]["path"] != fresh["image"]):
            raise AssertionError("fresh turn did not use exact paired producer image/HUD")
        fresh_steps = compile_commands(new_result.answer["commands"])
        if fresh_steps == old_steps: raise AssertionError("fresh answer did not compile distinctly")

        inert_thread.all_threads.clear()
        stable = make_executor(submit_class, 2, fresh_steps)
        stable.submit("fresh-seq-2", fresh_steps, 2, time.perf_counter_ns() + 10_000_000_000)
        if (len(stable.emit_events) != 1 or stable.emit_events[0].get("event") != "accepted" or
                stable.backend.validate_calls != 1 or len(inert_thread.all_threads) != 1 or
                not inert_thread.all_threads[0].started):
            raise AssertionError("fresh turn did not reach exactly one admission")
        fresh_worker_started = inert_thread.all_threads[0].started

        inert_thread.all_threads.clear()
        drift = make_executor(submit_class, 3, fresh_steps)
        try: drift.submit("second-drift-seq-2", fresh_steps, 2, time.perf_counter_ns() + 10_000_000_000)
        except ValueError as exc: drift_reason = str(exc)
        else: raise AssertionError("second sequence drift unexpectedly admitted")
        if (drift_reason != "latest observation sequence required before input" or drift.emit_events or
                drift.backend.validate_calls or any(t.started for t in inert_thread.all_threads)):
            raise AssertionError("second drift crossed admission boundary")

        controls = {}
        for label, rejection_row, events in (
            ("non_stale_rejection", {"event": "rejected", "reason": "program expired"}, []),
            ("no_fresh_observation", {"event": "rejected", "reason": "latest observation sequence required before input"}, []),
            ("missing_typed_event", {"event": "rejected", "reason": "latest observation sequence required before input"}, [copy.deepcopy(full)]),
        ):
            q = queue.Queue()
            for row in events: q.put(row)
            w, _ = extract_wait(previous, q)
            try: recover(rejection_row, previous, w, TypedCapture(), timeout=0.002)
            except Exception: controls[label] = "refused"
            else: raise AssertionError(f"unsafe recovery accepted {label}")
        for label, bad_typed, bad_full in (
            ("binding_mismatch", copy.deepcopy(typed), copy.deepcopy(full)),
            ("frame_hash_mismatch", copy.deepcopy(typed), copy.deepcopy(full)),
        ):
            if label == "binding_mismatch": bad_full["pointer_binding"]["surface"] = 8
            else: bad_full["frame_rgb_sha256"] = "0" * 64
            q = queue.Queue(); q.put(bad_typed); q.put(bad_full)
            w, _ = extract_wait(previous, q)
            try: recover({"event": "rejected", "reason": "latest observation sequence required before input"}, previous, w, TypedCapture())
            except Exception: controls[label] = "refused"
            else: raise AssertionError(f"unsafe recovery accepted {label}")

    return {
        "schema": "v39-preacceptance-stale-replan-a04-result-v1",
        "main_commit": MAIN,
        "disposition": "PASS_EXACT_PRODUCER_TO_EXECUTOR_RECOVERY_COMPOSITION",
        "source_blobs": source_hashes,
        "producer_pair": {"sequence": 2, "typed_before_full": True,
                          "capture_binding_hash_match": True, "health": 86, "ammo": 12},
        "stale_sequence_1": {"reason": stale_reason, "compiled_once": True, "accepted_events": 0,
                              "backend_validation_calls": 0, "worker_starts": 0,
                              "retried_after_rejection": False},
        "fresh_sequence_2": {"planner_turn_count": len(client.turns), "used_exact_producer_image": True,
                              "used_paired_typed_hud": True, "compiled_steps": fresh_steps,
                              "accepted_events": len(stable.emit_events),
                              "backend_validation_calls": stable.backend.validate_calls,
                              "worker_started_inertly": fresh_worker_started,
                              "physical_input": False},
        "second_drift_sequence_3": {"reason": drift_reason, "accepted_events": len(drift.emit_events),
                                    "backend_validation_calls": drift.backend.validate_calls,
                                    "worker_starts": sum(t.started for t in inert_thread.all_threads)},
        "controls": controls,
        "scope": "synthetic source-bound method composition; worker body/instrumental input not run",
    }


if __name__ == "__main__":
    result = run_case()
    print(json.dumps(result, sort_keys=True))
