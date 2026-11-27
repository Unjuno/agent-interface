"""Check the actual session emitter separates log start from stdout handoff."""
import ast
import builtins
import importlib.util
import json
import os
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import patch


SOURCE = Path(__file__).with_name("session_map01_v12.py")


def load_actual_emit(output, clock, gate=None):
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
            ast.Assign(targets=[ast.Name(id=name, ctx=ast.Store()) for name in
                                ("latest_observation", "last_terminal", "last_accepted")],
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
        "args": types.SimpleNamespace(out=output, verified_fixture_setup=False, fresh_neutral_fixture_setup=False),
        "json": json,
        "os": os,
        "threading": threading,
        "time": clock,
        "owner_generation_protocol": types.SimpleNamespace(record_terminal=lambda row, backend: None),
        "backend": None,
        "post_load_gate": gate,
        "door_coordinator": None,
    }
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace["build_emit"]()


class EmitTimingTests(unittest.TestCase):
    def test_rejected_admission_is_attached_without_io_or_delivery(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            def reject(_row):
                raise RuntimeError("first key admission proof unverified")
            clock = types.SimpleNamespace(perf_counter_ns=lambda: 123)
            emit = load_actual_emit(output, clock, types.SimpleNamespace(record=reject))
            receipt = {"event": "input_admission", "id": "cover-1", "owner_id": "unexpected"}
            with patch.object(builtins, "print") as printed, \
                 patch.object(Path, "open", side_effect=AssertionError("unexpected I/O")):
                with self.assertRaisesRegex(RuntimeError, "admission proof") as caught:
                    emit(receipt)
            self.assertIn(json.dumps(receipt, sort_keys=True), str(caught.exception))
            self.assertFalse((output / "delivered.jsonl").exists())
            printed.assert_not_called()

    def test_opt_in_private_bus_policy_applies_before_and_after_x11_setup(self):
        spec = importlib.util.spec_from_file_location("offline_session_map01_v12", SOURCE)
        runtime = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"vizdoom": types.ModuleType("vizdoom")}):
            spec.loader.exec_module(runtime)

        class StopBeforeGame(Exception):
            pass

        key = "DBUS_SESSION_BUS_ADDRESS"
        for gate, expected_before, expected_session in (
                (None, "existing:", None), (object(), "disabled:", "disabled:")):
            with self.subTest(gated=gate is not None), tempfile.TemporaryDirectory() as temp:
                workspace = Path(temp)
                private = workspace / "private"
                private.mkdir()
                seen = []

                def stop_before_game(_atom):
                    seen.append((os.environ.get(key), session.env.get(key)))
                    raise StopBeforeGame

                session = types.SimpleNamespace(
                    env={}, d=types.SimpleNamespace(intern_atom=stop_before_game),
                    tmp=private, close=lambda: None)

                def construct():
                    seen.append(os.environ.get(key))
                    return session

                args = [str(SOURCE), "--out", str(workspace / "out"), "--seed", "7",
                        "--load-fixture-manifest", str(workspace / "manifest.json")]
                with patch.object(runtime.suite, "Session", side_effect=construct), \
                     patch.object(sys, "argv", args), patch.dict(os.environ, {key: "existing:"}):
                    with self.assertRaises(StopBeforeGame):
                        runtime.main(post_load_gate=gate)
                self.assertEqual(seen, [expected_before, (expected_before, expected_session)])

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
