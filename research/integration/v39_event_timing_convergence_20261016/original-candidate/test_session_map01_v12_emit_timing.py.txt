"""Check the actual session emitter separates log start from stdout handoff."""
import ast
import builtins
import json
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import patch


SOURCE = Path(__file__).with_name("session_map01_v12.py")


def load_actual_emit(output, clock):
    tree = ast.parse(SOURCE.read_bytes(), filename=str(SOURCE))
    main = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "main")
    emit = next(node for node in main.body
                if isinstance(node, ast.FunctionDef) and node.name == "emit")
    outer = ast.FunctionDef(
        name="build_emit",
        args=ast.arguments(posonlyargs=[], args=[], vararg=None,
                           kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
        body=[
            ast.Assign(targets=[ast.Name(id="latest_observation", ctx=ast.Store())],
                       value=ast.Constant(value=None)),
            ast.Assign(targets=[ast.Name(id="lock", ctx=ast.Store())],
                       value=ast.Call(func=ast.Attribute(
                           value=ast.Name(id="threading", ctx=ast.Load()),
                           attr="RLock", ctx=ast.Load()), args=[], keywords=[])),
            emit,
            ast.Return(value=ast.Name(id="emit", ctx=ast.Load())),
        ],
        decorator_list=[],
    )
    module = ast.fix_missing_locations(ast.Module(body=[outer], type_ignores=[]))
    namespace = {
        "args": types.SimpleNamespace(out=output),
        "json": json,
        "threading": threading,
        "time": clock,
    }
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace["build_emit"]()


class EmitTimingTests(unittest.TestCase):
    def test_stdout_handoff_timestamp_follows_both_raw_log_appends(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)

            class Clock:
                calls = 0

                def perf_counter_ns(self):
                    self.calls += 1
                    if self.calls == 2:
                        for name in ("events.jsonl", "delivered.jsonl"):
                            path = output / name
                            if not path.is_file() or not path.read_text().strip():
                                raise AssertionError(
                                    "stdout timing was captured before raw log append")
                    return self.calls * 100

            printed = []

            def capture_stdout(encoded, *, flush):
                self.assertTrue(flush)
                printed.append(json.loads(encoded))

            emit = load_actual_emit(output, Clock())
            with patch.object(builtins, "print", side_effect=capture_stdout):
                emit({"event": "typed_observation", "sequence": 7,
                      "typed_ready_ns": 50})

            self.assertEqual(len(printed), 1)
            stream_row = printed[0]
            self.assertEqual(stream_row["stdout_handoff_started_ns"], 200)
            self.assertEqual(stream_row["emit_ns"], 100)
            self.assertGreater(stream_row["stdout_handoff_started_ns"],
                               stream_row["emit_ns"])
            event_row = json.loads((output / "events.jsonl").read_text())
            delivered_row = json.loads((output / "delivered.jsonl").read_text())
            self.assertEqual(event_row, delivered_row)
            self.assertNotIn("stdout_handoff_started_ns", event_row)


if __name__ == "__main__":
    unittest.main()
