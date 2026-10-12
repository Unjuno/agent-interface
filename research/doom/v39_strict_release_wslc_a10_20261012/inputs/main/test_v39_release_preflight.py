"""Preflight tests for the strict V39 release-receipt producer contract."""
import ast
import argparse
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


SOURCE = Path(__file__).with_name("map01_overlap_controller_v39.py")
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"))


class ReleasePreflightTests(unittest.TestCase):
    def test_default_v10_session_is_rejected_and_v15_is_accepted(self):
        helper = next((node for node in TREE.body
                       if isinstance(node, ast.FunctionDef)
                       and node.name == "require_release_receipt_session"), None)
        self.assertIsNotNone(helper, "strict release preflight is missing")
        namespace = {"ValueError": ValueError}
        exec(compile(ast.Module(body=[helper], type_ignores=[]), str(SOURCE), "exec"),
             namespace)

        with self.assertRaisesRegex(ValueError, "--measurement-session"):
            namespace[helper.name](SimpleNamespace(measurement_session=False))
        namespace[helper.name](SimpleNamespace(measurement_session=True))

        session_builder = next((node for node in TREE.body
                                if isinstance(node, ast.FunctionDef)
                                and node.name == "session_command"), None)
        self.assertIsNotNone(session_builder)
        session_namespace = {"sys": sys, "Path": Path, "HERE": SOURCE.parent}
        exec(compile(ast.Module(body=[session_builder], type_ignores=[]),
                     str(SOURCE), "exec"), session_namespace)
        command = session_namespace[session_builder.name](
            SimpleNamespace(measurement_session=True, seed=1,
                            load_fixture_manifest=Path("fixture.json")),
            Path("runtime"))
        self.assertEqual(Path(command[1]).name, "session_map01_v15.py")

    def test_cli_rejects_default_before_output_creation_or_child_launch(self):
        main = next(node for node in TREE.body
                    if isinstance(node, ast.FunctionDef) and node.name == "main")
        helper = next(node for node in TREE.body
                      if isinstance(node, ast.FunctionDef)
                      and node.name == "require_release_receipt_session")
        namespace = {
            "argparse": argparse,
            "Path": Path,
            "ValueError": ValueError,
            "sys": sys,
        }
        exec(compile(ast.Module(body=[helper], type_ignores=[]), str(SOURCE), "exec"),
             namespace)
        exec(compile(ast.Module(body=[main], type_ignores=[]), str(SOURCE), "exec"),
             namespace)

        original_argv = sys.argv
        try:
            with tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary) / "must-not-be-created"
                sys.argv = [
                    str(SOURCE), "--out", str(output), "--model", "fixture",
                    "--effort", "low", "--load-fixture-manifest",
                    str(Path(temporary) / "fixture.json"),
                ]
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as raised:
                        namespace[main.name]()
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("--measurement-session", stderr.getvalue())
                self.assertFalse(output.exists())
        finally:
            sys.argv = original_argv


if __name__ == "__main__":
    unittest.main()
