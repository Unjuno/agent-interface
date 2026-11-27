"""Exercise production reader/wait timing annotations without a GUI process."""
import ast
import json
import queue
import time
import tempfile
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent))
from doom_controller_failure_cleanup_v1 import (
    reject_duplicate_json_members, reject_control_boundary_failure,
    SessionControlBoundaryFailure)

ROWS = []


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
    namespace = {"json": json, "queue": queue, "time": time,
                 "reject_duplicate_json_members": reject_duplicate_json_members,
                 "reject_control_boundary_failure": reject_control_boundary_failure}
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
        ROWS.append(dict(case="dispatch", event=queued_row,
                         summary=load_timing_summary()(all_events)))

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
        ROWS.append(dict(case="complete-and-missing", events=rows, summary=result))

    def test_monitor_exception_preserves_primary_and_finish_stamp(self):
        incoming, events, errors = queue.Queue(), [], []
        reader, wait = load_reader_and_wait(incoming, Process([
            dict(event="typed_observation", sequence=11)]), events, errors)
        reader()
        primary = TimeoutError("monitor failed")
        def observe(row):
            raise primary
        monitor = SimpleNamespace(event_types={"typed_observation"}, observe=observe)
        with self.assertRaises(TimeoutError) as raised:
            wait(lambda row: True, observation_monitor=monitor)
        self.assertIs(raised.exception, primary)
        self.assertLessEqual(events[0]["controller_monitor_started_ns"],
                             events[0]["controller_monitor_finished_ns"])
        ROWS.append(dict(case="monitor-error", event=events[0],
                         primary_preserved=True, errors=errors))

    def test_duplicate_json_is_refused_before_queue(self):
        incoming, events, errors = queue.Queue(), [], []
        process = Process([])
        process.stdout = ['{"event":"typed_observation","event":"terminal"}\n']
        reader, _ = load_reader_and_wait(incoming, process, events, errors)
        reader()
        self.assertTrue(incoming.empty())
        self.assertEqual(events, [])
        self.assertIn("duplicate JSON member", errors[0])
        ROWS.append(dict(case="duplicate-json", events=events, errors=errors,
                         queue_empty=incoming.empty()))

    def test_control_boundary_failure_precedes_monitor_and_predicate(self):
        incoming, events, errors = queue.Queue(), [], []
        row = dict(event="control_boundary_failed", task_effect="unknown",
                   release_obligation={"verified": False})
        reader, wait = load_reader_and_wait(incoming, Process([row]), events, errors)
        reader()
        called = []
        monitor = SimpleNamespace(event_types={"control_boundary_failed"},
                                  observe=lambda event: called.append("monitor"))
        with self.assertRaises(SessionControlBoundaryFailure):
            wait(lambda event: called.append("predicate"), observation_monitor=monitor)
        self.assertEqual(called, [])
        ROWS.append(dict(case="control-failure", event=events[0], called=called,
                         refused=True))

    def test_strict_summary_rejects_bool_and_reversed_stages(self):
        fields = ("typed_ready_ns", "emit_ns", "stdout_handoff_started_ns",
                  "controller_parsed_ns", "controller_enqueued_ns",
                  "controller_dequeued_ns", "controller_monitor_started_ns",
                  "controller_monitor_finished_ns")
        base = dict(zip(fields, range(10, 90, 10)), event="typed_observation", sequence=12)
        cases = []
        for field, value in (("emit_ns", True), ("controller_parsed_ns", 0)):
            row = dict(base, **{field: value})
            result = load_timing_summary()([row])[0]
            self.assertFalse(result["stage_order_valid"])
            self.assertTrue(any(value is None for value in result["intervals_ms"].values()))
            cases.append(dict(event=row, summary=result))
        ROWS.append(dict(case="invalid-stages", cases=cases))

    def test_actual_emitter_through_dispatch_and_saved_summary(self):
        from test_session_map01_v12_emit_timing import load_actual_emit
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            lines = []
            emit = load_actual_emit(out, time)
            row = dict(event="typed_observation", sequence=13,
                       typed_ready_ns=time.perf_counter_ns())
            with patch("builtins.print", side_effect=lambda text, **kwargs: lines.append(text)):
                emit(row)
            process = Process([])
            process.stdout = lines
            incoming, events, errors = queue.Queue(), [], []
            reader, wait = load_reader_and_wait(incoming, process, events, errors)
            reader()
            result = wait(lambda event: False, observation_monitor=Monitor())
            self.assertEqual(result["event"], "running_action_invalidation")
            summary = load_timing_summary()(events)
            self.assertTrue(summary[0]["stage_order_valid"])
            logs = {name:(out/name).read_text() for name in ("events.jsonl", "delivered.jsonl")}
            self.assertEqual(logs["events.jsonl"], logs["delivered.jsonl"])
            logged = json.loads(logs["events.jsonl"])
            self.assertNotIn("stdout_handoff_started_ns", logged)
            for key, value in logged.items():self.assertEqual(events[0][key], value)
            self.assertEqual(errors, [])
            ROWS.append(dict(case="composed-emitter-dispatch", raw_logs=logs,
                             stdout=lines, events=events, summary=summary))


if __name__ == "__main__":
    unittest.main()
