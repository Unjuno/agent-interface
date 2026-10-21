"""Deterministically probe the exact current-main V39 final-empty race."""
import ast
import hashlib
import json
import queue
import subprocess
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))


def pinned_source(path):
    commit = FREEZE["base_commit"]
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", f"{commit}:{path}"], text=True
    ).strip()
    identity = FREEZE["sources"][path]
    if blob != identity["blob"]:
        raise ValueError(f"source blob mismatch: {path}")
    data = subprocess.check_output(
        ["git", "-C", str(REPO), "cat-file", "blob", blob]
    )
    if hashlib.sha256(data).hexdigest() != identity["sha256"]:
        raise ValueError(f"source hash mismatch: {path}")
    return data.decode("utf-8")


def module_function(source, name, filename, namespace):
    tree = ast.parse(source)
    node = next(n for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name == name)
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    exec(compile(module, filename, "exec"), namespace)
    return namespace[name]


class LateArrivalQueue(queue.Queue):
    """Insert sequence 12 just after the final empty() observation returns."""

    def __init__(self):
        super().__init__()
        self.inject_after_empty = True
        super().put({"event": "observation", "sequence": 11, "id": "before-empty"})

    def empty(self):
        observed_empty = super().empty()
        if observed_empty and self.inject_after_empty:
            self.inject_after_empty = False
            super().put({"event": "observation", "sequence": 12,
                         "id": "arrived-after-empty"})
        return observed_empty


def execute_segment(source, latest_sequence, rejection):
    tree = ast.parse(source)
    main = next(n for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name == "main")
    segment = next(n for n in ast.walk(main)
                   if isinstance(n, ast.FunctionDef) and n.name == "execute_segment")
    outer = ast.FunctionDef(
        name="make_segment",
        args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=[
            ast.Assign(targets=[ast.Name(id="program_admissions", ctx=ast.Store())],
                       value=ast.Constant(0)),
            ast.Assign(targets=[ast.Name(id="first_accepted", ctx=ast.Store())],
                       value=ast.Constant(None)),
            ast.Assign(targets=[ast.Name(id="final_action_admission", ctx=ast.Store())],
                       value=ast.Dict(keys=[], values=[])),
            segment,
            ast.Return(value=ast.Name(id="execute_segment", ctx=ast.Load())),
        ], decorator_list=[])
    namespace = {"json": json, "time": time}
    module = ast.fix_missing_locations(ast.Module(body=[outer], type_ignores=[]))
    exec(compile(module, "current-main-map01-overlap-controller-v39.py", "exec"), namespace)

    class Stdin:
        def __init__(self):
            self.data = ""

        def write(self, value):
            self.data += value

        def flush(self):
            pass

    class Process:
        pass

    process = Process()
    process.stdin = Stdin()
    namespace.update({
        "latest": {"sequence": latest_sequence},
        "all_events": [],
        "process": process,
        "compile_commands": lambda _commands: [{"op": "observe"}],
        "wait": lambda _predicate, **_kwargs: rejection,
    })
    try:
        namespace["make_segment"]()(
            "late-plan", [{"action": "observe"}], "primary", [0]
        )
    except RuntimeError as error:
        propagated = str(error)
    else:
        raise AssertionError("controller failed to propagate stale-sequence rejection")
    submitted = json.loads(process.stdin.data.strip())
    return {
        "rejection_propagates_as_runtime_error": True,
        "submitted_expected_sequence": submitted["expected_sequence"],
        "submit_attempts": 1,
        "retry_or_accept_event_count": 0,
        "disposition": "segment aborts into controller failure cleanup",
        "error": propagated,
    }


def run():
    controller = pinned_source("research/doom/map01_overlap_controller_v39.py")
    executor = pinned_source("research/live_control/executor_v12.py")
    for path in (
        "research/doom/session_map01_v12.py",
        "research/doom/doom_typed_coast_backend_v1.py",
    ):
        pinned_source(path)

    controller_ns = {"queue": queue}
    controller_tree = ast.parse(controller)
    constants = [n for n in controller_tree.body
                 if isinstance(n, ast.Assign) and any(
                     isinstance(target, ast.Name) and target.id in {
                         "MAX_PENDING_OBSERVATION_EVENTS",
                         "MAX_PENDING_OBSERVATION_RECOVERY_BATCHES",
                     } for target in n.targets)]
    drain = next(n for n in controller_tree.body
                 if isinstance(n, ast.FunctionDef)
                 and n.name == "drain_pending_observation_events")
    selected = ast.fix_missing_locations(
        ast.Module(body=constants + [drain], type_ignores=[])
    )
    exec(compile(selected, "current-main-map01-overlap-controller-v39.py", "exec"),
         controller_ns)

    incoming = LateArrivalQueue()
    drained = controller_ns["drain_pending_observation_events"](
        incoming, None, "terminal"
    )
    if (drained["latest"]["sequence"] != 11 or drained["pending_events"]
            or incoming.qsize() != 1):
        raise AssertionError("fixture did not land in the final-empty race window")
    late = incoming.get_nowait()
    if late["sequence"] != 12:
        raise AssertionError("late row identity changed")

    executor_tree = ast.parse(executor)
    executor_class = next(n for n in executor_tree.body
                          if isinstance(n, ast.ClassDef) and n.name == "Executor")
    submit = next(n for n in executor_class.body
                  if isinstance(n, ast.FunctionDef) and n.name == "submit")
    harness_class = ast.ClassDef(name="HarnessExecutor", bases=[], keywords=[],
                                 body=[submit], decorator_list=[])
    executor_ns = {}
    exec(compile(ast.fix_missing_locations(ast.Module(
        body=[harness_class], type_ignores=[])),
        "current-main-executor-v12.py", "exec"), executor_ns)

    class Lock:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class Backend:
        sequence = late["sequence"]

        def validate(self, _steps):
            raise AssertionError("stale sequence passed validation")

    events = []
    executor_harness = executor_ns["HarnessExecutor"]()
    executor_harness.lock = Lock()
    executor_harness.closed = False
    executor_harness.active = None
    executor_harness.backend = Backend()
    executor_harness.used_ids = set()
    executor_harness.emit = events.append
    try:
        executor_harness.submit(
            "late-observation", [{"op": "observe"}],
            drained["latest"]["sequence"], 10**30,
        )
    except ValueError as error:
        rejection_reason = str(error)
    else:
        raise AssertionError("stale observation was admitted")
    if rejection_reason != "latest observation sequence required before input" or events:
        raise AssertionError("executor did not fail closed before admission/input")

    controller_result = execute_segment(controller, 11, {
        "event": "rejected", "reason": rejection_reason,
    })
    result = {
        "schema": "current-main-final-empty-check-race-construction-v1",
        "main_commit": FREEZE["base_commit"],
        "source_identities": FREEZE["sources"],
        "scenario": {
            "queue_observation_before_final_empty": 11,
            "observation_enqueued_after_empty_return": 12,
            "drain_latest_sequence": drained["latest"]["sequence"],
            "drain_pending_events": drained["pending_events"],
            "queued_after_return": 1,
            "executor_backend_sequence": late["sequence"],
            "executor_expected_sequence": drained["latest"]["sequence"],
        },
        "executor": {
            "rejected": True,
            "reason": rejection_reason,
            "admission_or_input_events": len(events),
        },
        "controller": controller_result,
        "decision": "PASS_FAIL_CLOSED_BUT_DRAIN_MISSED_LATE_EVENT; SESSION_CONTINUITY_NOT_ESTABLISHED",
        "scope": "Deterministic synthetic interleaving; exact pinned current-main drain, Executor.submit and execute_segment ASTs. No full controller worker, backend session, GUI, model, game, OS input, live recovery, or task effect.",
    }
    return result


if __name__ == "__main__":
    result = run()
    (ROOT / "RESULT.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
