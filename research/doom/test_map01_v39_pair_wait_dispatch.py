"""Exercise the production wait dispatcher and paired monitor on full rows."""
import ast
import os
from pathlib import Path
import queue
import time
import unittest


HERE = Path(__file__).resolve().parent
CONTROLLER = Path(os.environ.get(
    "V39_CONTROLLER_SOURCE", HERE / "map01_overlap_controller_v39.py"))
BINDING = {"focus": 7, "surface": 9, "geometry": [0, 0, 640, 480]}


def signal(signal_id, value, sequence, capture_ns):
    return {"status": "observed", "signal_id": signal_id, "value": value,
            "sequence": sequence, "capture_ns": capture_ns,
            "binding": dict(BINDING)}


class Reader:
    def __init__(self, key):
        self.key = key

    def read(self, observation):
        return observation[self.key]


class Guard:
    def __init__(self, signal_id, source_value, source_sequence, source_capture_ns,
                 hard_minimum):
        self.spec = {"signal_id": signal_id, "source_value": source_value,
                     "source_sequence": source_sequence,
                     "hard_minimum": hard_minimum}
        self.source_capture_ns = source_capture_ns

    def evaluate(self, value):
        invalid = value["value"] < self.spec["hard_minimum"]
        status = "HARD_INVALIDATED" if invalid else "UNCHANGED"
        return {"status": status,
                "reason": "below_hard_minimum" if invalid else "signal_unchanged",
                "requires_new_decision": invalid,
                "grants_input_authority": False,
                "may_only_preserve_or_reduce_existing_authority": True,
                "task_success_verified": False}


class Process:
    def poll(self):
        return None


def load_controller_dispatch(source_path):
    tree = ast.parse(source_path.read_bytes(), filename=str(source_path))
    main = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "main")
    wait_node = next(node for node in ast.walk(main)
                     if isinstance(node, ast.FunctionDef) and node.name == "wait")
    monitor_nodes = [node for node in tree.body
                     if ((isinstance(node, ast.FunctionDef) and node.name in {
                             "_typed_json_equal", "_signal_pair_matches"}) or
                         (isinstance(node, ast.ClassDef) and
                          node.name == "DoomCoverSignalPairMonitor"))]
    wanted = {"_typed_json_equal", "_signal_pair_matches", "DoomCoverSignalPairMonitor"}
    found = {node.name for node in monitor_nodes}
    if found != wanted:
        raise AssertionError(f"pinned production monitor missing: {wanted - found}")

    outer = ast.FunctionDef(
        name="build_wait",
        args=ast.arguments(posonlyargs=[], args=[ast.arg(arg="incoming"),
                                                ast.arg(arg="process")],
                           kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=[ast.Assign(targets=[ast.Name(id="latest", ctx=ast.Store())],
                         value=ast.Constant(value=None)),
              wait_node,
              ast.Return(value=ast.Name(id="wait", ctx=ast.Load()))],
        decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(
        body=monitor_nodes + [outer], type_ignores=[]))
    namespace = {"queue": queue, "time": time}
    exec(compile(module, str(source_path), "exec"), namespace)
    return namespace["build_wait"], namespace["DoomCoverSignalPairMonitor"]


class PairWaitDispatchTests(unittest.TestCase):
    def test_ack_precedes_active_typed_observation_on_serialized_session_stream(self):
        root = HERE.parents[1]

        def source(relative):
            return ast.parse((root / relative).read_text(encoding="utf-8"))

        def function(tree, name, parent=None):
            scope = tree if parent is None else parent
            matches = [node for node in ast.walk(scope)
                       if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                       and node.name == name]
            self.assertEqual(len(matches), 1, name)
            return matches[0]

        def calls(node, attribute):
            return [item for item in ast.walk(node)
                    if isinstance(item, ast.Call)
                    and isinstance(item.func, ast.Attribute)
                    and item.func.attr == attribute]

        session = source("research/doom/session_map01_v12.py")
        session_main = function(session, "main")
        emit = function(session, "emit", session_main)
        lock_scope = next(node for node in ast.walk(emit)
                          if isinstance(node, ast.With)
                          and any(isinstance(item.context_expr, ast.Name)
                                  and item.context_expr.id == "lock"
                                  for item in node.items))
        self.assertTrue(any(
            isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "print"
            and any(keyword.arg == "flush"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                    for keyword in node.keywords)
            for node in ast.walk(lock_scope)))

        executor = source("research/live_control/executor_v12.py")
        executor_class = next(node for node in executor.body
                              if isinstance(node, ast.ClassDef)
                              and node.name == "Executor")
        submit = function(executor, "submit", executor_class)
        accepted_emits = [node for node in calls(submit, "emit")
                          if node.args and isinstance(node.args[0], ast.Dict)
                          and any(isinstance(key, ast.Constant)
                                  and key.value == "event"
                                  and isinstance(value, ast.Constant)
                                  and value.value == "accepted"
                                  for key, value in zip(node.args[0].keys,
                                                        node.args[0].values))]
        worker_starts = calls(submit, "start")
        self.assertEqual(len(accepted_emits), 1)
        self.assertEqual(len(worker_starts), 1)
        self.assertLess(accepted_emits[0].lineno, worker_starts[0].lineno)

        typed = source("research/doom/doom_typed_coast_backend_v1.py")
        typed_backend = next(node for node in typed.body
                             if isinstance(node, ast.ClassDef)
                             and node.name == "Backend")
        snapshot = function(typed, "snapshot", typed_backend)
        self.assertTrue(calls(snapshot, "emit"))
        coast = source("research/live_control/coast_backend_v1.py")
        coast_backend = next(node for node in coast.body
                             if isinstance(node, ast.ClassDef)
                             and node.name == "Backend")
        execute = function(coast, "execute", coast_backend)
        self.assertTrue(calls(execute, "snapshot"))

        controller = source("research/doom/map01_overlap_controller_v39.py")
        controller_main = function(controller, "main")
        reader = function(controller, "reader", controller_main)
        stdout_loop = next(node for node in ast.walk(reader)
                           if isinstance(node, ast.For)
                           and isinstance(node.iter, ast.Attribute)
                           and isinstance(node.iter.value, ast.Name)
                           and node.iter.value.id == "process"
                           and node.iter.attr == "stdout")
        decodes = calls(stdout_loop, "loads")
        enqueues = calls(stdout_loop, "put")
        self.assertEqual(len(decodes), 1)
        self.assertEqual(len(enqueues), 1)
        self.assertEqual(decodes[0].lineno, enqueues[0].lineno)

    def test_full_observation_dispatches_zero_ammo_invalidation(self):
        build_wait, monitor_type = load_controller_dispatch(CONTROLLER)
        monitor = monitor_type(
            {"health": Guard("health", 100, 10, 1_000_000_000, 35),
             "ammo": Guard("ammo", 4, 10, 1_000_000_000, 1)},
            Reader("health"), Reader("ammo"))
        observation = {
            "event": "observation", "sequence": 11,
            "capture_ns": 1_100_000_000, "pointer_binding": dict(BINDING),
            "image": "fixture.png", "frame_rgb_sha256": "a" * 64,
            "health": signal("health", 100, 11, 1_100_000_000),
            "ammo": signal("ammo", 0, 11, 1_100_000_000),
        }
        incoming = queue.Queue()
        incoming.put(observation)
        wait = build_wait(incoming, Process())

        result = wait(lambda _row: False, timeout=0.2,
                      observation_monitor=monitor)

        self.assertEqual(result["event"], "policy_invalidation")
        self.assertEqual(result["invalidation"]["event"],
                         "paired_signal_invalidation")
        self.assertEqual(result["invalidation"]["outcomes"]["ammo"]["reason"],
                         "below_hard_minimum")


if __name__ == "__main__":
    unittest.main()
