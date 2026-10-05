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
