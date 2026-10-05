import ast
import argparse
import hashlib
import json
import sys
import time
import types
import unittest
from unittest import mock
from argparse import Namespace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOOM = ROOT / "research" / "doom"
CONTROLLER = DOOM / "map01_overlap_controller_v39.py"
SESSION_V12 = DOOM / "session_map01_v12.py"
SESSION_V15 = DOOM / "session_map01_v15.py"

def load_session_command():
    tree = ast.parse(CONTROLLER.read_text(encoding="utf-8"))
    fn = next(node for node in tree.body
              if isinstance(node, ast.FunctionDef) and node.name == "session_command")
    module = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    scope = {"sys": sys, "Path": Path, "HERE": DOOM}
    exec(compile(module, str(CONTROLLER), "exec"), scope)
    return scope["session_command"]

class MeasurementSessionComposition(unittest.TestCase):
    def test_default_and_each_opt_in_compose(self):
        fn = load_session_command()
        args = Namespace(seed=7, load_fixture_manifest=Path("fixture.json"))
        default = fn(args, Path("runtime"))
        self.assertEqual(Path(default[1]).name, SESSION_V12.name)
        self.assertNotIn("--per-key-input-measurement", default)

        args.per_key_input_measurement = True
        per_key = fn(args, Path("runtime"))
        self.assertEqual(Path(per_key[1]).name, SESSION_V12.name)
        self.assertEqual(per_key[-1], "--per-key-input-measurement")

        args.measurement_session = True
        composed = fn(args, Path("runtime"))
        self.assertEqual(Path(composed[1]).name, SESSION_V15.name)
        self.assertEqual(composed[-1], "--per-key-input-measurement")

    def test_v15_wrapper_preserves_per_key_flag_for_v12_parser(self):
        tree = ast.parse(SESSION_V15.read_text(encoding="utf-8"))
        selected = [node for node in tree.body
                    if isinstance(node, ast.FunctionDef)
                    and node.name in {"_option", "main"}]
        module = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
        captured = {}

        class Sink:
            def __init__(self, _out):
                pass

            def finalize(self, _stats):
                pass

        class Polling:
            def __init__(self, _stdin, _sample, _sink, sample_hz):
                self.sample_hz = sample_hz

            def stats(self):
                return {}

        base = types.ModuleType("session_map01_v12")
        base.vd = types.SimpleNamespace(DoomGame=type("DoomGame", (), {}))
        base.sys = sys

        def fake_base_main():
            parser = argparse.ArgumentParser()
            parser.add_argument("--out", required=True)
            parser.add_argument("--timeout-seconds", required=True)
            parser.add_argument("--seed", required=True)
            parser.add_argument("--skill", required=True)
            parser.add_argument("--load-fixture-manifest", required=True)
            parser.add_argument("--per-key-input-measurement", action="store_true")
            captured.update(vars(parser.parse_args()))

        base.main = fake_base_main
        executor = types.ModuleType("executor_v13")
        executor.Executor = type("Executor", (), {})
        backend = types.ModuleType("doom_owner_thread_release_batch_backend_v1")
        backend.Backend = type("Backend", (), {})
        scope = {
            "sys": sys, "Path": Path, "time": time, "hashlib": hashlib,
            "json": json, "ScorerFileSink": Sink,
            "MainThreadScorerStdin": Polling,
            "preserve_opt_in_measurement_backend": lambda _base, _backend, args:
                captured.update(backend_args=list(args)),
            "_merge_sources": lambda _out: False,
        }
        exec(compile(module, str(SESSION_V15), "exec"), scope)
        argv = ["session_map01_v15.py", "--out", "runtime", "--timeout-seconds", "600",
                "--seed", "7", "--skill", "1", "--load-fixture-manifest", "fixture.json",
                "--per-key-input-measurement"]
        with mock.patch.dict(sys.modules, {
                "session_map01_v12": base,
                "executor_v13": executor,
                "doom_owner_thread_release_batch_backend_v1": backend}), \
             mock.patch.object(sys, "argv", argv):
            scope["main"]()
        self.assertTrue(captured["per_key_input_measurement"])
        self.assertIn("--per-key-input-measurement", captured["backend_args"])

    def test_v12_consumer_declares_forwarded_flag_and_v15_delegates(self):
        v12 = ast.parse(SESSION_V12.read_text(encoding="utf-8"))
        self.assertTrue(any(isinstance(node, ast.Call)
                            and isinstance(node.func, ast.Attribute)
                            and node.func.attr == "add_argument"
                            and node.args and isinstance(node.args[0], ast.Constant)
                            and node.args[0].value == "--per-key-input-measurement"
                            for node in ast.walk(v12)))
        v15 = ast.parse(SESSION_V15.read_text(encoding="utf-8"))
        self.assertTrue(any(isinstance(node, ast.Import)
                            and any(alias.name == "session_map01_v12" and alias.asname == "base"
                                    for alias in node.names)
                            for node in ast.walk(v15)))
        self.assertTrue(any(isinstance(node, ast.Call)
                            and isinstance(node.func, ast.Attribute)
                            and isinstance(node.func.value, ast.Name)
                            and node.func.value.id == "base"
                            and node.func.attr == "main"
                            for node in ast.walk(v15)))

if __name__ == "__main__":
    unittest.main(verbosity=2)
