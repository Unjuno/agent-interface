import ast
import hashlib
import importlib.util
import json
import queue
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CONTROLLER = REPO / "research/doom/map01_overlap_controller_v39.py"
ADAPTER = REPO / "research/live_control/persistent_planner_adapter_v2.py"
FREEZE = json.loads((HERE / "FREEZE.json").read_text())


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


def recover_after_stale_rejection(rejection, submitted_sequence, previous, wait):
    # Candidate policy only: refresh from the event stream, never resubmit the old action.
    if (rejection.get("event") != "rejected" or
            rejection.get("reason") != "latest observation sequence required before input"):
        raise RecoveryRefused("rejection is not the exact stale-sequence refusal")
    fresh = wait(lambda row: row.get("event") == "observation" and
                 type(row.get("sequence")) is int and row["sequence"] > submitted_sequence,
                 timeout=1)
    if (type(fresh.get("capture_ns")) is not int or fresh["capture_ns"] <= previous["capture_ns"] or
            fresh.get("pointer_binding") != previous.get("pointer_binding") or
            type(fresh.get("image")) is not str or not fresh["image"] or
            type(fresh.get("health")) is not int or fresh["health"] < 1 or
            type(fresh.get("ammo")) is not int or fresh["ammo"] < 0):
        raise RecoveryRefused("new observation does not qualify for a fresh planner turn")
    return fresh


def make_observation(sequence, image, health, ammo, binding):
    return {"event": "observation", "sequence": sequence, "capture_ns": sequence * 100,
            "image": str(image), "health": health, "ammo": ammo, "pointer_binding": binding}


def run_case():
    pin = FREEZE["sources"]
    sources = {"controller": CONTROLLER, "adapter": ADAPTER,
               "source_refresh": REPO / "research/doom/doom_source_refresh_v1.py"}
    for label, path in sources.items():
        expected = pin["research/doom/map01_overlap_controller_v39.py"] if label == "controller" else (
            pin["research/doom/doom_source_refresh_v1.py"] if label == "source_refresh" else pin["research/live_control/persistent_planner_adapter_v2.py"])
        actual = git_blob(path)
        if expected and actual != expected:
            raise AssertionError(f"{label} source blob mismatch: {actual}")

    with tempfile.TemporaryDirectory(prefix="v39-stale-replan-") as temp:
        root = Path(temp)
        old_image, fresh_image = Path("fixture/sequence-1.png"), Path("fixture/sequence-2.png")
        binding = {"focus": 1, "surface": 7, "geometry": [0, 0, 640, 480]}
        old = make_observation(1, old_image, 88, 12, binding)
        fresh = make_observation(2, fresh_image, 86, 12, binding)
        refresh_spec = importlib.util.spec_from_file_location(
            "current_source_refresh", REPO / "research/doom/doom_source_refresh_v1.py")
        refresh_module = importlib.util.module_from_spec(refresh_spec)
        sys.modules[refresh_spec.name] = refresh_module
        refresh_spec.loader.exec_module(refresh_module)
        class Reader:
            def __init__(self, name): self.name = name
            def read(self, row): return {"status": "observed", "value": row[self.name]}
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
        incoming.put(fresh)
        wait, get_latest = extract_wait(old, incoming)
        rejection = incoming.get_nowait()
        recovered = recover_after_stale_rejection(rejection, old["sequence"], old, wait)
        if get_latest() != recovered:
            raise AssertionError("exact controller wait did not advance latest observation")
        second_root = root / "turn-2"; second_root.mkdir()
        second_handle = begin_model_turn(planner, second_root, Path(recovered["image"]), [],
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
        for label, bad_rejection, bad_observation in [
                ("non_stale_rejection", {"event": "rejected", "reason": "program expired"}, None),
                ("binding_change", {"event": "rejected", "reason": "latest observation sequence required before input"},
                 make_observation(2, fresh_image, 86, 12, {"focus": 1, "surface": 8, "geometry": [0, 0, 640, 480]}))]:
            q = queue.Queue()
            if bad_observation is not None: q.put(bad_observation)
            w, _ = extract_wait(old, q)
            try:
                recover_after_stale_rejection(bad_rejection, old["sequence"], old, w)
            except (RecoveryRefused, TimeoutError):
                controls[label] = "refused"
            else:
                raise AssertionError(f"unsafe recovery control admitted: {label}")
        q = queue.Queue()
        w, _ = extract_wait(old, q)
        try:
            recover_after_stale_rejection({"event": "rejected", "reason": "latest observation sequence required before input"},
                                          old["sequence"], old, w)
        except TimeoutError:
            controls["no_fresh_observation"] = "refused"
        else:
            raise AssertionError("missing fresh observation was not refused")
        if set(controls.values()) != {"refused"}:
            raise AssertionError("negative controls did not fail closed")

    return {"format": "v39-preacceptance-stale-replan-a01", "disposition": "PASS_CANDIDATE_COMPOSITION",
            "main_sha": FREEZE["main_sha"], "source_blobs": {label: git_blob(path) for label, path in sources.items()},
            "trigger": {"submitted_sequence": 1, "producer_sequence_at_rejection": 2,
                        "rejection_before_full_observation_delivery": True},
            "first_turn": {"answer": "stale-turn-answer", "used_after_rejection": False},
            "recovery": {"fresh_sequence": 2, "fresh_capture_ns": fresh["capture_ns"],
                         "planner_turn_count": len(client.turns), "fresh_image_used": fresh_image.as_posix(),
                         "fresh_hud_in_prompt": {"health": 86, "ammo": 12},
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
