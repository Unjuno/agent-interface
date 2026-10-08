"""Source-bound offline construction for V39 stale-sequence recovery."""
import ast
import hashlib
import importlib.util
import io
import json
import platform
import queue
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CONTROLLER = REPO / "research/doom/map01_overlap_controller_v39.py"
ADAPTER = REPO / "research/live_control/persistent_planner_adapter_v2.py"
FREEZE = json.loads((HERE / "FREEZE.json").read_text())


class RecoveryRefused(RuntimeError):
    pass


def blob(path):
    rel = path.relative_to(REPO).as_posix()
    return subprocess.check_output(["git", "-C", str(REPO), "rev-parse", f"HEAD:{rel}"], text=True).strip()


def find_function(tree, name):
    nodes = [node for node in ast.walk(tree)
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    if len(nodes) != 1:
        raise ValueError(f"expected one {name}, found {len(nodes)}")
    return nodes[0]


def extract_wait(initial, incoming, process_exit_code=None):
    tree = ast.parse(CONTROLLER.read_text())
    main = find_function(tree, "main")
    nodes = [node for node in ast.walk(main) if isinstance(node, ast.FunctionDef) and node.name == "wait"]
    if len(nodes) != 1:
        raise ValueError("main must contain exactly one production wait")
    wait_node = nodes[0]
    factory = ast.FunctionDef(
        name="factory", args=ast.arguments(posonlyargs=[], args=[ast.arg(arg="process"), ast.arg(arg="incoming"), ast.arg(arg="initial")],
            kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=[ast.Assign(targets=[ast.Name(id="latest", ctx=ast.Store())], value=ast.Name(id="initial", ctx=ast.Load())),
              wait_node,
              ast.Return(value=ast.Tuple(elts=[ast.Name(id="wait", ctx=ast.Load()), ast.Lambda(args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]), body=ast.Name(id="latest", ctx=ast.Load()))], ctx=ast.Load()))],
        decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[]))
    class Process:
        @staticmethod
        def poll(): return process_exit_code
    scope = {"queue": queue, "time": time, "RuntimeError": RuntimeError}
    exec(compile(module, str(CONTROLLER), "exec"), scope)
    return scope["factory"](Process(), incoming, initial)


def extract_begin_model_turn():
    tree = ast.parse(CONTROLLER.read_text())
    node = find_function(tree, "begin_model_turn")
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    scope = {"json": json, "win": lambda path: str(path)}
    exec(compile(module, str(CONTROLLER), "exec"), scope)
    return scope["begin_model_turn"]


def extract_execute_segment_shape():
    tree = ast.parse(CONTROLLER.read_text())
    main = find_function(tree, "main")
    nodes = [node for node in ast.walk(main) if isinstance(node, ast.FunctionDef) and node.name == "execute_segment"]
    if len(nodes) != 1:
        raise ValueError("main must contain exactly one execute_segment")
    source = ast.get_source_segment(CONTROLLER.read_text(), nodes[0])
    return {"raises_on_nonaccepted": 'if accepted["event"]!="accepted":raise RuntimeError(accepted)' in source,
            "acceptance_wait_includes_rejections": 'r["event"] in ("accepted","rejected")' in source,
            "no_recovery_after_rejection": source.index('if accepted["event"]!="accepted"') < source.index('program_admissions+=1') and
                'recover_after_stale' not in source and 'replan_after_stale' not in source}


def execute_production_rejection_branch():
    """Execute the exact nested production function until its rejection branch."""
    tree = ast.parse(CONTROLLER.read_text())
    main = find_function(tree, "main")
    wait_nodes = [item for item in ast.walk(main) if isinstance(item, ast.FunctionDef) and item.name == "wait"]
    node = [item for item in ast.walk(main)
            if isinstance(item, ast.FunctionDef) and item.name == "execute_segment"]
    if len(node) != 1 or len(wait_nodes) != 1: raise ValueError("expected one production wait and execute_segment")
    fn = node[0]
    wait_node = wait_nodes[0]
    factory = ast.FunctionDef(
        name="factory", args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=[
            ast.Assign(targets=[ast.Name(id="program_admissions", ctx=ast.Store())], value=ast.Constant(0)),
            ast.Assign(targets=[ast.Name(id="first_accepted", ctx=ast.Store())], value=ast.Constant(None)),
            ast.Assign(targets=[ast.Name(id="final_action_admission", ctx=ast.Store())], value=ast.Dict(keys=[], values=[])),
            ast.Assign(targets=[ast.Name(id="latest", ctx=ast.Store())], value=ast.Name(id="initial", ctx=ast.Load())),
            ast.Assign(targets=[ast.Name(id="all_events", ctx=ast.Store())], value=ast.List(elts=[], ctx=ast.Load())),
            ast.Assign(targets=[ast.Name(id="process", ctx=ast.Store())], value=ast.Call(func=ast.Name(id="FakeProcess", ctx=ast.Load()), args=[], keywords=[])),
            wait_node,
            ast.Assign(targets=[ast.Name(id="compile_commands", ctx=ast.Store())], value=ast.Name(id="fake_compile", ctx=ast.Load())),
            fn,
            ast.Return(value=ast.Tuple(elts=[ast.Name(id="execute_segment", ctx=ast.Load()),
                ast.Name(id="process", ctx=ast.Load()), ast.Name(id="wait", ctx=ast.Load()),
                ast.Lambda(args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]), body=ast.Name(id="latest", ctx=ast.Load())),
                ast.Lambda(args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
                    body=ast.Tuple(elts=[ast.Name(id="program_admissions", ctx=ast.Load()), ast.Name(id="first_accepted", ctx=ast.Load())], ctx=ast.Load()))], ctx=ast.Load()))],
        decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[]))
    class FakeProcess:
        def __init__(self): self.stdin = io.StringIO()
        @staticmethod
        def poll(): return None
    binding = {"focus": 1, "surface": 7, "geometry": [0, 0, 640, 480]}
    previous = observation(1, "fixture/sequence-1.png", 88, 12, binding)
    fresh = observation(2, "fixture/sequence-2.png", 86, 11, binding)
    incoming = queue.Queue()
    incoming.put({"event": "typed_observation", "sequence": 2, "capture_ns": 200})
    incoming.put(fresh)
    incoming.put({"event": "rejected", "reason": "latest observation sequence required before input"})
    def fake_compile(commands): return [{"op": "observe"}]
    scope = {"FakeProcess": FakeProcess, "fake_compile": fake_compile,
             "time": time, "json": json, "queue": queue, "RuntimeError": RuntimeError,
             "incoming": incoming, "initial": previous}
    exec(compile(module, str(CONTROLLER), "exec"), scope)
    execute_segment, process, production_wait, latest, state = scope["factory"]()
    try:
        execute_segment("plan-0-primary-0-0", [{"action": "observe", "extent": "one"}], "primary", [0])
    except RuntimeError as error:
        message = str(error)
        if "latest observation sequence required before input" not in message:
            raise
        lines = [line for line in process.stdin.getvalue().splitlines() if line]
        command = json.loads(lines[0]) if len(lines) == 1 else None
        evidence = {"result": "raises_on_rejection", "message": message,
                "submit_count": len(lines), "submitted_expected_sequence": None if command is None else command.get("expected_sequence"),
                "state_before_any_admission": state(), "latest_after_production_wait": latest()}
        return evidence, production_wait, latest, {"event": "rejected", "reason": "latest observation sequence required before input"}
    raise AssertionError("production rejection branch did not fail closed")


def extract_adapter():
    spec = importlib.util.spec_from_file_location("current_planner_adapter", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.PersistentPlannerAdapter


class FakePlannerClient:
    def __init__(self):
        self.turns = []
        self.answers = [{"decision": "fresh-turn-answer"}]
    def start_thread(self, **kwargs): return {"thread": {"id": "thread-1"}}
    def start_turn(self, thread_id, inputs, **kwargs):
        self.turns.append({"thread_id": thread_id, "inputs": inputs, "schema": kwargs["outputSchema"]})
        return {"turn": {"id": f"turn-{len(self.turns)}"}}
    def wait_turn_completed(self, thread_id, turn_id, timeout=120):
        answer = self.answers[int(turn_id.split("-")[-1]) - 1]
        return {"turn": {"status": "completed", "items": [{"type": "agentMessage", "text": json.dumps(answer)}]}}
    def latest_turn_usage(self, thread_id, turn_id): return {"input_tokens": 1, "output_tokens": 1}


def observation(sequence, image, health, ammo, binding):
    return {"event": "observation", "sequence": sequence, "capture_ns": sequence * 100,
            "image": str(image), "health": health, "ammo": ammo, "pointer_binding": binding}


def candidate_recover(rejection, submitted, previous, wait, latest_fn):
    if rejection.get("event") != "rejected":
        raise RecoveryRefused("not a rejection")
    if rejection.get("reason") != "latest observation sequence required before input":
        raise RecoveryRefused("not the exact stale-sequence refusal")
    fresh = latest_fn()
    if not (type(fresh.get("sequence")) is int and fresh["sequence"] > submitted):
        fresh = wait(lambda row: row.get("event") == "observation" and
                     type(row.get("sequence")) is int and row["sequence"] > submitted,
                     timeout=1)
    binding = fresh.get("pointer_binding")
    if (type(fresh.get("capture_ns")) is not int or fresh["capture_ns"] <= previous["capture_ns"] or
            type(binding) is not dict or binding != previous.get("pointer_binding") or
            type(fresh.get("image")) is not str or not fresh["image"] or
            type(fresh.get("health")) is not int or fresh["health"] < 1 or
            type(fresh.get("ammo")) is not int or fresh["ammo"] < 0):
        raise RecoveryRefused("new observation is incomplete, stale, or binding changed")
    return fresh


def run_case():
    expected = FREEZE["sources"]
    if blob(CONTROLLER) != expected["research/doom/map01_overlap_controller_v39.py"]:
        raise AssertionError("controller source blob differs from freeze")
    if blob(ADAPTER) != expected["research/live_control/persistent_planner_adapter_v2.py"]:
        raise AssertionError("planner adapter source blob differs from freeze")
    source_shape = extract_execute_segment_shape()
    if not all(source_shape.values()):
        raise AssertionError(f"production rejection branch changed: {source_shape}")
    production_reproduction, production_wait, production_latest, production_rejection = execute_production_rejection_branch()
    if (production_reproduction["submit_count"] != 1 or
            production_reproduction["submitted_expected_sequence"] != 1 or
            production_reproduction["state_before_any_admission"] != (0, None)):
        raise AssertionError(f"production branch did not fail before admission/input: {production_reproduction}")

    binding = {"focus": 1, "surface": 7, "geometry": [0, 0, 640, 480]}
    old = observation(1, "fixture/sequence-1.png", 88, 12, binding)
    fresh = observation(2, "fixture/sequence-2.png", 86, 11, binding)
    # Current-main ordering: typed observation, full observation, then the
    # stale rejection while production execute_segment's exact wait is active.
    recovered = candidate_recover(production_rejection, old["sequence"], old,
                                  production_wait, production_latest)
    if production_latest() != recovered: raise AssertionError("candidate did not retain production wait's latest observation")

    # Alternative ordering: rejection is delivered before the full observation.
    incoming = queue.Queue()
    incoming.put({"event": "typed_observation", "sequence": 2, "capture_ns": 200})
    incoming.put(fresh)
    wait, get_latest = extract_wait(old, incoming)
    delayed = candidate_recover(production_rejection, old["sequence"], old, wait, get_latest)
    if delayed != fresh: raise AssertionError("candidate did not wait for delayed full observation")

    with tempfile.TemporaryDirectory(prefix="v39-stale-replan-a02-") as temp:
        root = Path(temp)
        client = FakePlannerClient()
        planner_type = extract_adapter()
        planner = planner_type(client, model="fixture-model", effort="low", cwd=str(REPO), base_instructions="fixture")
        planner.start_session()
        image = root / "sequence-2.png"
        (root / "turn-2").mkdir(parents=True, exist_ok=True)
        image.write_bytes(b"synthetic-sequence-2-image")
        handle = extract_begin_model_turn()(planner, root / "turn-2", image, [],
                                            recovered["health"], recovered["ammo"], {}, {"type": "object"})
        result = planner.await_turn(handle)
        inputs = client.turns[0]["inputs"]
        prompt, image_input = inputs[0]["text"], inputs[1]
        if (result.answer != {"decision": "fresh-turn-answer"} or
                "Current locally verified health: 86." not in prompt or
                "Current locally verified ammo: 11." not in prompt or
                image_input.get("path") != str(image)):
            raise AssertionError("fresh planner turn did not use the newer complete observation")

    controls = {}
    cases = [
        ("other_rejection", {"event": "rejected", "reason": "program expired"}, fresh, "refused"),
        ("binding_changed", {"event": "rejected", "reason": "latest observation sequence required before input"}, observation(2, "fixture/new.png", 86, 11, {"focus": 1, "surface": 8, "geometry": [0, 0, 640, 480]}), "refused"),
        ("same_sequence", {"event": "rejected", "reason": "latest observation sequence required before input"}, observation(1, "fixture/old.png", 88, 12, binding), "refused"),
        ("invalid_health", {"event": "rejected", "reason": "latest observation sequence required before input"}, observation(2, "fixture/bad.png", 0, 11, binding), "refused"),
        ("invalid_ammo", {"event": "rejected", "reason": "latest observation sequence required before input"}, observation(2, "fixture/bad.png", 86, -1, binding), "refused"),
        ("missing_image", {"event": "rejected", "reason": "latest observation sequence required before input"}, observation(2, "", 86, 11, binding), "refused"),
        ("old_capture", {"event": "rejected", "reason": "latest observation sequence required before input"}, dict(observation(2, "fixture/old-time.png", 86, 11, binding), capture_ns=100), "refused"),
    ]
    for label, rejection, row, expected_outcome in cases:
        q = queue.Queue(); q.put(row)
        w, _ = extract_wait(old, q)
        try: candidate_recover(rejection, 1, old, w, lambda: old)
        except (RecoveryRefused, TimeoutError): controls[label] = "refused"
        else: raise AssertionError(f"negative control admitted: {label}")
    q = queue.Queue(); w, _ = extract_wait(old, q)
    try: candidate_recover({"event": "rejected", "reason": "latest observation sequence required before input"}, 1, old, w, lambda: old)
    except TimeoutError: controls["timeout"] = "refused"
    else: raise AssertionError("timeout admitted")
    q = queue.Queue(); w, _ = extract_wait(old, q, process_exit_code=17)
    try: candidate_recover({"event": "rejected", "reason": "latest observation sequence required before input"}, 1, old, w, lambda: old)
    except RuntimeError as error:
        if "session exited" not in str(error): raise
        controls["process_exit"] = "refused"
    else: raise AssertionError("process exit admitted")

    return {"format": "v39-preacceptance-stale-replan-a02", "disposition": "PASS_CANDIDATE_CONTROLLER_RECOVERY",
            "main_sha": FREEZE["main_sha"], "source_blobs": {name: blob(REPO / name) for name in expected},
            "runtime": {"python": sys.version, "platform": platform.platform()},
            "production_branch": source_shape,
            "production_reproduction": production_reproduction,
            "trigger": {"submitted_sequence": 1, "producer_sequence": 2,
                        "current_main_order": ["typed_observation", "observation", "rejected"],
                        "candidate_also_passed_rejection_before_full_observation": delayed == fresh},
            "recovery": {"fresh_sequence": recovered["sequence"], "health": recovered["health"], "ammo": recovered["ammo"],
                         "planner_turns": len(client.turns), "image": image_input.get("path"), "post_rejection_submits": 0},
            "negative_controls": controls,
            "scope": "offline synthetic construction; production branch observed but candidate recovery not merged or executed live"}


if __name__ == "__main__":
    result = run_case()
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
