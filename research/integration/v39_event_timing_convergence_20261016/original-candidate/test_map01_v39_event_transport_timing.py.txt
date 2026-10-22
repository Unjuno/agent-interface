"""Exercise production reader/wait timing annotations without a GUI process."""
import ast
import json
import queue
import time
import unittest
from pathlib import Path


SOURCE = Path(__file__).with_name("map01_overlap_controller_v39.py")


def load_reader_and_wait(incoming, process, all_events, reader_errors):
    tree = ast.parse(SOURCE.read_bytes(), filename=str(SOURCE))
    main = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "main")
    reader = next(node for node in ast.walk(main)
                  if isinstance(node, ast.FunctionDef) and node.name == "reader")
    wait = next(node for node in ast.walk(main)
                if isinstance(node, ast.FunctionDef) and node.name == "wait")
    outer = ast.FunctionDef(
        name="build_dispatch",
        args=ast.arguments(
            posonlyargs=[],
            args=[ast.arg(arg="incoming"), ast.arg(arg="process"),
                  ast.arg(arg="all_events"), ast.arg(arg="reader_errors")],
            vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
        body=[
            ast.Assign(targets=[ast.Name(id="latest", ctx=ast.Store())],
                       value=ast.Constant(value=None)),
            reader,
            wait,
            ast.Return(value=ast.Tuple(
                elts=[ast.Name(id="reader", ctx=ast.Load()),
                      ast.Name(id="wait", ctx=ast.Load())],
                ctx=ast.Load())),
        ],
        decorator_list=[],
    )
    module = ast.fix_missing_locations(ast.Module(body=[outer], type_ignores=[]))
    namespace = {"json": json, "queue": queue, "time": time}
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace["build_dispatch"](incoming, process, all_events, reader_errors)


def load_timing_summary():
    tree = ast.parse(SOURCE.read_bytes(), filename=str(SOURCE))
    function = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and
                    node.name == "typed_event_transport_timing_rows")
    module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    namespace = {}
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace[function.name]


class Process:
    def __init__(self, rows):
        self.stdout = [json.dumps(row) + "\n" for row in rows]

    def poll(self):
        return None


class Monitor:
    event_types = {"typed_observation"}

    def __init__(self):
        self.seen = []

    def observe(self, row):
        self.seen.append(row)
        return {"event": "running_action_invalidation", "grants_input_authority": False}


class EventTransportTimingTests(unittest.TestCase):
    def test_reader_and_monitor_retain_ordered_parent_handoff_stages(self):
        row = {"event": "typed_observation", "sequence": 9,
               "typed_ready_ns": 80, "emit_ns": 100,
               "stdout_handoff_started_ns": 150}
        incoming, all_events, reader_errors = queue.Queue(), [], []
        reader, wait = load_reader_and_wait(
            incoming, Process([row]), all_events, reader_errors)

        reader()
        self.assertEqual(reader_errors, [])
        queued_row = all_events[0]
        monitor = Monitor()
        wait_result = wait(lambda _event: False, timeout=0.1,
                           observation_monitor=monitor)

        self.assertEqual(wait_result["event"], "running_action_invalidation")
        self.assertIs(all_events[0], queued_row)
        self.assertIs(monitor.seen[0], queued_row)
        stages = ["stdout_handoff_started_ns", "controller_parsed_ns",
                  "controller_enqueued_ns", "controller_dequeued_ns",
                  "controller_monitor_started_ns",
                  "controller_monitor_finished_ns"]
        values = [queued_row[name] for name in stages]
        self.assertTrue(all(type(value) is int for value in values))
        self.assertEqual(values, sorted(values))

    def test_report_summary_keeps_each_boundary_and_marks_incomplete_rows(self):
        summarize = load_timing_summary()
        rows = [
            {"event": "observation", "sequence": 8},
            {"event": "typed_observation", "sequence": 9,
             "typed_ready_ns": 80, "emit_ns": 100,
             "stdout_handoff_started_ns": 150, "controller_parsed_ns": 200,
             "controller_enqueued_ns": 210, "controller_dequeued_ns": 240,
             "controller_monitor_started_ns": 250,
             "controller_monitor_finished_ns": 270},
            {"event": "typed_observation", "sequence": 10,
             "typed_ready_ns": 280, "emit_ns": 300},
        ]

        result = summarize(rows)

        self.assertEqual([row["sequence"] for row in result], [9, 10])
        self.assertTrue(result[0]["stage_order_valid"])
        self.assertFalse(result[1]["stage_order_valid"])
        self.assertEqual(result[0]["controller_monitor_finished_ns"], 270)
        self.assertEqual(
            result[0]["intervals_ms"]["controller_queue_wait_ms"],
            30 / 1e6)
        self.assertIsNone(result[1]["stdout_handoff_started_ns"])
        self.assertIsNone(
            result[1]["intervals_ms"]["stdout_handoff_to_controller_parse_ms"])


if __name__ == "__main__":
    unittest.main()
