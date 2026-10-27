import ast
import copy
import hashlib
import importlib.util
import json
import queue
import sys
import tempfile
import time
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CONTROLLER = REPO / "research/doom/map01_overlap_controller_v39.py"
ADAPTER = REPO / "research/live_control/persistent_planner_adapter_v2.py"
TYPED_OBSERVATION = REPO / "research/doom/doom_typed_observation_v1.py"
TYPED_BACKEND = REPO / "research/doom/doom_typed_coast_backend_v1.py"
FREEZE = json.loads((HERE / "FREEZE.json").read_text())
sys.path.insert(0, str(REPO / "research/live_control"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path):
    import subprocess
    rel = path.relative_to(REPO).as_posix()
    return subprocess.check_output(["git", "-C", str(REPO), "rev-parse", f"HEAD:{rel}"], text=True).strip()


def extract_wait(initial, incoming):
    tree = ast.parse(CONTROLLER.read_text())
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    wait_node = next(node for node in ast.walk(main)
                     if isinstance(node, ast.FunctionDef) and node.name == "wait")
    factory = ast.FunctionDef(
        name="factory", args=ast.arguments(posonlyargs=[], args=[ast.arg(arg="process"), ast.arg(arg="incoming"), ast.arg(arg="initial")],
            kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=[ast.Assign(targets=[ast.Name(id="latest", ctx=ast.Store())],
                         value=ast.Name(id="initial", ctx=ast.Load())),
              wait_node,
              ast.Return(value=ast.Tuple(elts=[ast.Name(id="wait", ctx=ast.Load()),
                  ast.Lambda(args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
                             body=ast.Name(id="latest", ctx=ast.Load()))], ctx=ast.Load()))],
        decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[]))
    scope = {"queue": queue, "time": time, "RuntimeError": RuntimeError}
    exec(compile(module, str(CONTROLLER), "exec"), scope)
    class Process:
        @staticmethod
        def poll(): return None
    return scope["factory"](Process(), incoming, initial)


def extract_begin_model_turn():
    tree = ast.parse(CONTROLLER.read_text())
    node = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == "begin_model_turn")
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    scope = {"json": json, "win": lambda path: str(path)}
    exec(compile(module, str(CONTROLLER), "exec"), scope)
    return scope["begin_model_turn"]


class FakePlannerClient:
    def __init__(self):
        self.turns = []
        self.answers = [{"decision": "stale-turn-answer"}, {"decision": "fresh-turn-answer"}]
    def start_thread(self, **kwargs): return {"thread": {"id": "thread-1"}}
    def start_turn(self, thread_id, inputs, **kwargs):
        self.turns.append({"thread_id": thread_id, "inputs": inputs, "schema": kwargs["outputSchema"]})
        return {"turn": {"id": f"turn-{len(self.turns)}"}}
    def wait_turn_completed(self, thread_id, turn_id, timeout=120):
        answer = self.answers[int(turn_id.split("-")[-1]) - 1]
        return {"turn": {"status": "completed", "items": [{"type": "agentMessage", "text": json.dumps(answer)}]}}
    def latest_turn_usage(self, thread_id, turn_id): return {"input_tokens": 1, "output_tokens": 1}


class RecoveryRefused(RuntimeError):
    pass


def recover_after_stale_rejection(rejection, submitted_sequence, previous, wait, typed_capture):
    # Candidate policy only: refresh from the event stream, never resubmit the old action.
    if (rejection.get("event") != "rejected" or
            rejection.get("reason") != "latest observation sequence required before input"):
        raise RecoveryRefused("rejection is not the exact stale-sequence refusal")
    fresh = wait(lambda row: row.get("event") == "observation" and
                 type(row.get("sequence")) is int and row["sequence"] > submitted_sequence,
                 timeout=1, observation_monitor=typed_capture)
    typed = typed_capture.event
    signals = typed.get("signals", {}) if type(typed) is dict else {}
    if (type(fresh.get("capture_ns")) is not int or fresh["capture_ns"] <= previous["capture_ns"] or
            fresh.get("pointer_binding") != previous.get("pointer_binding") or
            type(fresh.get("image")) is not str or not fresh["image"] or
            type(typed) is not dict or typed.get("event") != "typed_observation" or
            typed.get("schema") != "doom-typed-observation-v1" or
            typed.get("sequence") != fresh.get("sequence") or
            typed.get("capture_ns") != fresh.get("capture_ns") or
            typed.get("id") != fresh.get("id") or typed.get("step") != fresh.get("step") or
            typed.get("pointer_binding") != fresh.get("pointer_binding") or
            typed.get("frame_rgb_sha256") != fresh.get("frame_rgb_sha256") or
            typed.get("artifact_published") is not False or
            typed.get("grants_input_authority") is not False or
            set(signals) != {"health", "ammo"}):
        raise RecoveryRefused("new typed/full observation pair does not qualify for a fresh planner turn")
    for name, minimum in (("health", 1), ("ammo", 0)):
        signal = signals[name]
        if (signal.get("status") != "observed" or type(signal.get("value")) is not int or
                signal["value"] < minimum or signal.get("sequence") != fresh["sequence"] or
                signal.get("capture_ns") != fresh["capture_ns"] or
                signal.get("binding") != fresh["pointer_binding"]):
            raise RecoveryRefused("typed health/ammo did not bind to the full fresh observation")
    return {"observation": fresh, "typed": typed,
            "health": signals["health"]["value"], "ammo": signals["ammo"]["value"]}


def make_observation(sequence, image, health, ammo, binding):
    return {"event": "observation", "id": "plan", "step": 0,
            "sequence": sequence, "capture_ns": sequence * 100,
            "image": str(image), "frame_rgb_sha256": "a" * 64,
            "pointer_binding": binding}


class TypedCapture:
    event_types = frozenset({"typed_observation"})
    def __init__(self): self.event = None
    def observe(self, row):
        self.event = row
        return None


def load_typed_observation_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("current_typed_observation", TYPED_OBSERVATION)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def execute_producer_snapshot(out):
    typed_module = load_typed_observation_module()
    backend_tree = ast.parse(TYPED_BACKEND.read_text())
    backend_class = next(node for node in backend_tree.body
                         if isinstance(node, ast.ClassDef) and node.name == "Backend")
    snapshot_node = next(node for node in backend_class.body
                         if isinstance(node, ast.FunctionDef) and node.name == "snapshot")
    snapshot_node.name = "snapshot"
    producer_clock = iter([150, 200, 205, 230, 240])
    typed_clock = iter([210, 220])
    def extract_typed(frame, metadata, readers):
        return typed_module.extract_typed_observation(
            frame, metadata, readers, clock=typed_clock.__next__)
    class FakeTime:
        @staticmethod
        def perf_counter_ns(): return next(producer_clock)
    namespace = {"time": FakeTime, "extract_typed_observation": extract_typed}
    binding = {"focus": 1, "surface": 7, "geometry": [0, 0, 640, 480]}
    frame_image = Image.new("RGB", (8, 8), (10, 20, 30))
    class ImageGrabStub:
        @staticmethod
        def grab(*, xdisplay):
            if xdisplay != ":fixture": raise AssertionError("unexpected display binding")
            return frame_image.copy()
    class Frame:
        def __init__(self, width, height, mode, payload): self.width, self.height, self.mode, self.payload = width, height, mode, payload
        def __eq__(self, other):
            return type(other) is Frame and (self.width, self.height, self.mode, self.payload) == (other.width, other.height, other.mode, other.payload)
    namespace.update({"ImageGrab": ImageGrabStub, "Frame": Frame})
    module_ast = ast.fix_missing_locations(ast.Module(body=[snapshot_node], type_ignores=[]))
    exec(compile(module_ast, str(TYPED_BACKEND), "exec"), namespace)
    class Reader:
        def __init__(self, name, value): self.name, self.value = name, value
        def read_frame(self, metadata, _frame):
            return {"format": "doom-hud-number-v1", "status": "observed",
                    "signal_id": self.name, "value": self.value,
                    "sequence": metadata["sequence"], "capture_ns": metadata["capture_ns"],
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
    emitted = []
    class Harness:
        def __init__(self):
            self.binding_value = binding
            self.session, self.out, self.emit = Session(), out, emitted.append
            self.signal_readers = {"health": Reader("health", 86), "ammo": Reader("ammo", 12)}
            self.sequence, self.encoder, self.images = 1, Encoder(), Images()
            self.decoder, self.observed_focus, self.observed_pointer = Decoder(self.encoder), None, None
        def binding(self): return dict(self.binding_value)
    namespace["snapshot"](Harness(), "plan", 0)
    if len(emitted) != 2 or [row.get("event") for row in emitted] != ["typed_observation", "observation"]:
        raise AssertionError("exact backend snapshot did not emit typed then full observation")
    return emitted


def run_case():
    pin = FREEZE["sources"]
    sources = {"controller": CONTROLLER, "adapter": ADAPTER,
               "source_refresh": REPO / "research/doom/doom_source_refresh_v1.py",
               "typed_backend": TYPED_BACKEND, "typed_observation": TYPED_OBSERVATION}
    for label, path in sources.items():
        paths = {"controller": "research/doom/map01_overlap_controller_v39.py",
                 "adapter": "research/live_control/persistent_planner_adapter_v2.py",
                 "source_refresh": "research/doom/doom_source_refresh_v1.py",
                 "typed_backend": "research/doom/doom_typed_coast_backend_v1.py",
                 "typed_observation": "research/doom/doom_typed_observation_v1.py"}
        expected = pin[paths[label]]
        actual = git_blob(path)
        if expected and actual != expected:
            raise AssertionError(f"{label} source blob mismatch: {actual}")

    with tempfile.TemporaryDirectory(prefix="v39-stale-replan-") as temp:
        root = Path(temp)
        old_image = Path("fixture/sequence-1.png")
        binding = {"focus": 1, "surface": 7, "geometry": [0, 0, 640, 480]}
        old = make_observation(1, old_image, 88, 12, binding)
        producer_events = execute_producer_snapshot(root)
        typed, fresh = producer_events
        fresh_image = Path(fresh["image"])
        if typed["frame_rgb_sha256"] != fresh["frame_rgb_sha256"]:
            raise AssertionError("exact producer's typed/full frame hashes differ")
        refresh_spec = importlib.util.spec_from_file_location(
            "current_source_refresh", REPO / "research/doom/doom_source_refresh_v1.py")
        refresh_module = importlib.util.module_from_spec(refresh_spec)
        sys.modules[refresh_spec.name] = refresh_module
        refresh_spec.loader.exec_module(refresh_module)
        class Reader:
            def __init__(self, name): self.name = name
            def read(self, row):
                value = {"health": 88, "ammo": 12}[self.name] if row["sequence"] == 1 else {
                    "health": 86, "ammo": 12}[self.name]
                return {"status": "observed", "value": value}
        source_refresh_commands = []
        unchanged, source_refresh_receipt = refresh_module.refresh_source(
            old, Reader("health"), Reader("ammo"), source_refresh_commands.append,
            lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("wait must not run")),
            "stale-reject")
        if unchanged != old or source_refresh_receipt["status"] != "already_observed" or source_refresh_commands:
            raise AssertionError("existing signal-unknown refresh unexpectedly refreshed a valid stale sequence")
        adapter_spec = importlib.util.spec_from_file_location("current_planner_adapter", ADAPTER)
        adapter_module = importlib.util.module_from_spec(adapter_spec)
        sys.modules[adapter_spec.name] = adapter_module
        adapter_spec.loader.exec_module(adapter_module)
        client = FakePlannerClient()
        planner = adapter_module.PersistentPlannerAdapter(
            client, model="fixture-model", effort="low", cwd=str(REPO), base_instructions="fixture")
        planner.start_session()
        begin_model_turn = extract_begin_model_turn()
        schema = {"type": "object"}
        first_root = root / "turn-1"; first_root.mkdir()
        first_handle = begin_model_turn(planner, first_root, old_image, [], 88, 12, {}, schema)
        old_result = planner.await_turn(first_handle)
        if not old_result.answer_eligible or old_result.answer != {"decision": "stale-turn-answer"}:
            raise AssertionError("first fixture planner answer was not produced")
        incoming = queue.Queue()
        incoming.put({"event": "rejected", "reason": "latest observation sequence required before input"})
        incoming.put(typed)
        incoming.put(fresh)
        wait, get_latest = extract_wait(old, incoming)
        rejection = incoming.get_nowait()
        typed_capture = TypedCapture()
        recovered = recover_after_stale_rejection(rejection, old["sequence"], old, wait, typed_capture)
        if get_latest() != recovered["observation"]:
            raise AssertionError("exact controller wait did not advance latest observation")
        second_root = root / "turn-2"; second_root.mkdir()
        second_handle = begin_model_turn(planner, second_root, Path(recovered["observation"]["image"]), [],
                                         recovered["health"], recovered["ammo"], {}, schema)
        fresh_result = planner.await_turn(second_handle)
        inputs = client.turns[1]["inputs"]
        prompt = inputs[0]["text"]
        image_input = inputs[1]
        if (fresh_result.answer != {"decision": "fresh-turn-answer"} or
                "Current locally verified health: 86." not in prompt or
                "Current locally verified ammo: 12." not in prompt or
                image_input.get("path") != str(fresh_image)):
            raise AssertionError("fresh planner turn did not use the paired sequence-2 evidence")

        controls = {}
        stale_rejection = {"event": "rejected", "reason": "latest observation sequence required before input"}
        scenarios = {}
        scenarios["non_stale_rejection"] = ({"event": "rejected", "reason": "program expired"}, [])
        scenarios["no_fresh_observation"] = (stale_rejection, [])
        bad_binding_typed = copy.deepcopy(typed)
        bad_binding_full = copy.deepcopy(fresh)
        bad_binding_full["pointer_binding"]["surface"] = 8
        scenarios["binding_change"] = (stale_rejection, [bad_binding_typed, bad_binding_full])
        bad_hash_typed = copy.deepcopy(typed)
        bad_hash_full = copy.deepcopy(fresh)
        bad_hash_full["frame_rgb_sha256"] = "0" * 64
        scenarios["typed_full_hash_mismatch"] = (stale_rejection, [bad_hash_typed, bad_hash_full])
        scenarios["missing_typed_event"] = (stale_rejection, [copy.deepcopy(fresh)])
        for label, (bad_rejection, events) in scenarios.items():
            q = queue.Queue()
            for event in events: q.put(event)
            w, _ = extract_wait(old, q)
            try:
                recover_after_stale_rejection(bad_rejection, old["sequence"], old, w, TypedCapture())
            except (RecoveryRefused, TimeoutError):
                controls[label] = "refused"
            else:
                raise AssertionError(f"unsafe recovery control admitted: {label}")
        if set(controls.values()) != {"refused"}:
            raise AssertionError("negative controls did not fail closed")

    return {"format": "v39-preacceptance-stale-replan-a02", "disposition": "PASS_CANDIDATE_COMPOSITION",
            "main_sha": FREEZE["main_sha"], "source_blobs": {label: git_blob(path) for label, path in sources.items()},
            "trigger": {"submitted_sequence": 1, "producer_sequence_at_rejection": 2,
                        "rejection_before_typed_observation": True,
                        "typed_observation_before_full_artifact": True,
                        "exact_producer_snapshot_executed": True,
                        "typed_and_full_sequence": 2,
                        "typed_and_full_frame_hash_match": True},
            "first_turn": {"answer": "stale-turn-answer", "used_after_rejection": False},
            "recovery": {"fresh_sequence": 2, "fresh_capture_ns": fresh["capture_ns"],
                         "planner_turn_count": len(client.turns), "fresh_image_used": "fixture/sequence-2.png",
                         "fresh_hud_in_prompt": {"health": recovered["health"], "ammo": recovered["ammo"]},
                         "typed_capture_matches_full_frame": True,
                         "action_resubmissions_after_rejection": 0,
                         "controller_wait_advanced_latest": True},
            "existing_source_refresh": {"status": source_refresh_receipt["status"],
                                        "submit_count": len(source_refresh_commands),
                                        "returned_sequence": unchanged["sequence"]},
            "controls": controls,
            "scope": "source-bound synthetic construction; candidate recovery policy, not current runtime behavior"}


if __name__ == "__main__":
    result = run_case()
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
