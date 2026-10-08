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
        self.assertTrue(any(isinstance(node, ast.ImportFrom)
                            and node.module == "executor_v12"
                            and any(alias.name == "Executor"
                                    for alias in node.names)
                            for node in session.body))
        self.assertTrue(any(isinstance(node, ast.ImportFrom)
                            and node.module == "doom_typed_release_backend_v1"
                            and any(alias.name == "Backend"
                                    for alias in node.names)
                            for node in session.body))
        emit = function(session, "emit", session_main)
        for component in ("Executor", "Backend"):
            wired = [node for node in ast.walk(session_main)
                     if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Name)
                     and node.func.id == component
                     and any(isinstance(argument, ast.Name)
                             and argument.id == "emit"
                             for argument in node.args)]
            self.assertEqual(len(wired), 1, component)
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

        measured_session = source("research/doom/session_map01_v15.py")
        self.assertTrue(any(isinstance(node, ast.Import)
                            and any(alias.name == "session_map01_v12"
                                    and alias.asname == "base"
                                    for alias in node.names)
                            for node in ast.walk(measured_session)))
        self.assertTrue(any(
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Attribute)
                    and target.attr == "Executor"
                    for target in node.targets)
            and isinstance(node.value, ast.Name)
            and node.value.id == "ReleaseOrderedExecutor"
            for node in ast.walk(measured_session)))
        self.assertTrue(any(
            isinstance(node, ast.ImportFrom)
            and node.module == "doom_owner_thread_release_batch_backend_v1"
            and any(alias.name == "Backend"
                    and alias.asname == "TelemetryBackend"
                    for alias in node.names)
            for node in ast.walk(measured_session)))
        self.assertTrue(any(
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Attribute)
                    and target.attr == "Backend"
                    for target in node.targets)
            and isinstance(node.value, ast.Name)
            and node.value.id == "TelemetryBackend"
            for node in ast.walk(measured_session)))
        executor_v13 = source("research/live_control/executor_v13.py")
        self.assertTrue(any(isinstance(node, ast.ImportFrom)
                            and node.module == "executor_v12"
                            and any(alias.name == "Executor"
                                    and alias.asname == "Previous"
                                    for alias in node.names)
                            for node in executor_v13.body))
        executor_v13_class = next(node for node in executor_v13.body
                                  if isinstance(node, ast.ClassDef)
                                  and node.name == "Executor")
        measured_submit = function(executor_v13, "submit", executor_v13_class)
        parent_submit = [node for node in calls(measured_submit, "submit")
                         if isinstance(node.func.value, ast.Call)
                         and isinstance(node.func.value.func, ast.Name)
                         and node.func.value.func.id == "super"]
        watcher_starts = calls(measured_submit, "start")
        self.assertEqual(len(parent_submit), 1)
        self.assertEqual(len(watcher_starts), 1)
        self.assertLess(parent_submit[0].lineno, watcher_starts[0].lineno)

        release_batch = source(
            "research/doom/doom_owner_thread_release_batch_backend_v1.py")
        release_batch_class = next(node for node in release_batch.body
                                   if isinstance(node, ast.ClassDef)
                                   and node.name == "Backend")
        release_batch_execute = function(release_batch, "execute",
                                         release_batch_class)
        self.assertTrue(any(isinstance(node.func.value, ast.Call)
                            and isinstance(node.func.value.func, ast.Name)
                            and node.func.value.func.id == "super"
                            for node in calls(release_batch_execute, "execute")))
        self.assertFalse(calls(release_batch_execute, "start"))
        self.assertFalse(calls(release_batch_execute, "submit"))

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

        release = source("research/doom/doom_typed_release_backend_v1.py")
        self.assertTrue(any(isinstance(node, ast.ImportFrom)
                            and node.module == "doom_typed_coast_backend_v1"
                            for node in release.body))
        self.assertTrue(any(isinstance(node, ast.ImportFrom)
                            and node.module == "coast_backend_v1"
                            for node in typed.body))
        release_v2 = source("research/doom/doom_typed_release_backend_v2.py")
        self.assertTrue(any(isinstance(node, ast.ImportFrom)
                            and node.module == "doom_typed_release_backend_v1"
                            for node in release_v2.body))

        controller = source("research/doom/map01_overlap_controller_v39.py")
        controller_main = function(controller, "main")
        session_command = function(controller, "session_command")
        session_names = {node.value for node in ast.walk(session_command)
                         if isinstance(node, ast.Constant)
                         and isinstance(node.value, str)}
        self.assertTrue({"session_map01_v12.py", "session_map01_v15.py"}
                        <= session_names)
        session_launches = [node for node in calls(controller_main, "Popen")
                            if node.args and isinstance(node.args[0], ast.Call)
                            and isinstance(node.args[0].func, ast.Name)
                            and node.args[0].func.id == "session_command"]
        self.assertEqual(len(session_launches), 1)
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
