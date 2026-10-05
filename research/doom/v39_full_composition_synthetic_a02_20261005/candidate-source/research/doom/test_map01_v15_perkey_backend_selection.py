import ast
from pathlib import Path
import sys
import types
import unittest

from v39_measurement_backend_selection_v1 import preserve_opt_in_measurement_backend


HERE = Path(__file__).resolve().parent


def load_controller_session_command():
    source = (HERE / "map01_overlap_controller_v39.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    function = next(node for node in module.body
                    if isinstance(node, ast.FunctionDef)
                    and node.name == "session_command")
    namespace = {"sys": sys, "HERE": HERE}
    exec(compile(ast.Module(body=[function], type_ignores=[]),
                 "map01_overlap_controller_v39.py", "exec"), namespace)
    return namespace["session_command"]


class V15PerKeyBackendSelectionTests(unittest.TestCase):
    def test_controller_passes_v15_and_per_key_opt_in_together(self):
        args = types.SimpleNamespace(
            measurement_session=True, per_key_input_measurement=True, seed=17,
            load_fixture_manifest=HERE / "fixture.json")
        command = load_controller_session_command()(args, HERE / "runtime")
        self.assertEqual(Path(command[1]).name, "session_map01_v15.py")
        self.assertIn("--per-key-input-measurement", command)

    def test_default_v15_uses_release_batch_backend(self):
        base = types.SimpleNamespace(Backend=object())
        release_batch = object()
        selected = preserve_opt_in_measurement_backend(base, release_batch, [])
        self.assertIs(selected, release_batch)

    def test_per_key_opt_in_is_not_overwritten_by_v15_wrapper(self):
        a01_backend = object()
        base = types.SimpleNamespace(Backend=a01_backend)
        selected = preserve_opt_in_measurement_backend(
            base, object(), ["--per-key-input-measurement"])
        self.assertIs(selected, a01_backend)


if __name__ == "__main__":
    unittest.main()
