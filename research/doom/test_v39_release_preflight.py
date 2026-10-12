"""Preflight tests for the strict V39 release-receipt producer contract."""
import ast
import sys
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

    def test_preflight_runs_before_output_creation_and_child_process(self):
        main = next(node for node in TREE.body
                    if isinstance(node, ast.FunctionDef) and node.name == "main")
        calls = [(node.lineno, node.func.id if isinstance(node.func, ast.Name)
                  else node.func.attr if isinstance(node.func, ast.Attribute) else "")
                 for node in ast.walk(main) if isinstance(node, ast.Call)]
        preflight = [line for line, name in calls
                     if name == "require_release_receipt_session"]
        output_creation = [node.lineno for node in ast.walk(main)
                           if isinstance(node, ast.Call)
                           and isinstance(node.func, ast.Attribute)
                           and node.func.attr == "mkdir"
                           and isinstance(node.func.value, ast.Attribute)
                           and node.func.value.attr == "out"]
        child_launch = [line for line, name in calls
                        if name == "Popen"]
        self.assertEqual(len(preflight), 1)
        self.assertEqual(len(output_creation), 1)
        self.assertEqual(len(child_launch), 1)
        self.assertLess(preflight[0], output_creation[0])
        self.assertLess(preflight[0], child_launch[0])


if __name__ == "__main__":
    unittest.main()
