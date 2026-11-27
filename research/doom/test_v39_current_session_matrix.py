"""Offline matrix for current V39 session selection; never starts a session."""
import ast
import itertools
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest


HERE = Path(__file__).resolve().parent


def controller_functions():
    path = HERE / "map01_overlap_controller_v39.py"
    tree = ast.parse(path.read_bytes(), filename=str(path))
    names = {"validate_input_service_selection", "session_command",
             "require_release_receipt_session"}
    nodes = [node for node in tree.body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in nodes} != names:
        raise AssertionError("controller function missing")
    scope = {"HERE": HERE, "sys": sys}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
                 str(path), "exec"), scope)
    return scope


class CurrentSessionSelectionTests(unittest.TestCase):
    def test_all_flag_combinations(self):
        functions = controller_functions()
        admitted = []
        for measurement, identity, lifecycle, service in itertools.product((False, True), repeat=4):
            args = SimpleNamespace(measurement_session=measurement,
                target_process_identity=identity, target_window_lifecycle=lifecycle,
                owned_input_service=service, seed=7,
                load_fixture_manifest=Path("fixture.json"))
            valid = (not identity or measurement) and (not lifecycle or identity) and (
                not service or (measurement and identity and not lifecycle))
            with self.subTest(flags=(measurement, identity, lifecycle, service)):
                if not valid:
                    with self.assertRaises(ValueError):
                        functions["session_command"](args, Path("inert-runtime"))
                    continue
                command = functions["session_command"](args, Path("inert-runtime"))
                self.assertEqual(Path(command[1]).name,
                    "session_map01_v15.py" if measurement else "session_map01_v12.py")
                self.assertEqual(command[command.index("--seed") + 1], "7")
                self.assertEqual(command[command.index("--out") + 1], "inert-runtime")
                self.assertEqual(command[command.index("--timeout-seconds") + 1], "600")
                self.assertEqual(command[command.index("--load-fixture-manifest") + 1],
                                 str(args.load_fixture_manifest.resolve()))
                for enabled, flag in ((identity, "--target-process-identity"),
                                      (lifecycle, "--target-window-lifecycle"),
                                      (service, "--owned-input-service")):
                    self.assertEqual(flag in command, enabled)
                if measurement:
                    functions["require_release_receipt_session"](args)
                else:
                    with self.assertRaises(ValueError):
                        functions["require_release_receipt_session"](args)
                admitted.append((measurement, identity, lifecycle, service))
        self.assertEqual(len(admitted), 5)


if __name__ == "__main__":
    unittest.main()
