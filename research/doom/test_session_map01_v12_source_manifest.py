"""Per-key mode pins the local modules it imports at runtime."""
import ast
import unittest
from pathlib import Path


class SourceManifestTests(unittest.TestCase):
    def test_per_key_source_manifest_includes_imported_executor_v3(self):
        session_path = Path(__file__).with_name("session_map01_v12.py").resolve()
        tree = ast.parse(session_path.read_bytes(), filename=str(session_path))
        main = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "main")
        per_key_branch = next(node for node in ast.walk(main)
                              if isinstance(node, ast.If)
                              and ast.unparse(node.test) == "args.per_key_input_measurement")
        append = next(node for node in per_key_branch.body
                      if isinstance(node, ast.Expr)
                      and isinstance(node.value, ast.Call)
                      and isinstance(node.value.func, ast.Attribute)
                      and isinstance(node.value.func.value, ast.Name)
                      and node.value.func.value.id == "source_paths"
                      and node.value.func.attr == "extend")

        here = session_path.parent
        namespace = {
            "source_paths": [],
            "PERKEY_BRIDGE": here / "map01_v39_perkey_bridge_a01" / "bridge.py",
            "PERKEY_OWNER": (here / "map01_attack_onset_phase_allocation_02_v1"
                             / "dependencies" / "v12" / "input_owner_v12.py"),
            "HERE": here,
        }
        module = ast.fix_missing_locations(ast.Module(body=[append], type_ignores=[]))
        exec(compile(module, str(session_path), "exec"), namespace)

        self.assertIn(here.parent / "live_control" / "executor_v3.py",
                      namespace["source_paths"])


if __name__ == "__main__":
    unittest.main()
