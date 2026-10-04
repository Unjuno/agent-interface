"""Guard the opt-in session's minimal telemetry-only composition delta."""
import ast
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
BASE = HERE / "session_map01_v12.py"
CANDIDATE = HERE / "session_map01_v13_release_telemetry.py"


class SessionReleaseTelemetryCompositionTests(unittest.TestCase):
    def test_candidate_differs_only_by_telemetry_backend_and_its_source_hashes(self):
        base = BASE.read_text(encoding="utf-8").rstrip("\n") + "\n"
        candidate = CANDIDATE.read_text(encoding="utf-8")
        expected = base.replace(
            '"""MAP01 v12 publishes lease-bound physical release before terminal closure."""',
            '"""MAP01 v13 adds opt-in ordinary per-key release RPC receipts."""',
            1,
        ).replace(
            "from doom_typed_release_backend_v1 import Backend, suite",
            "from doom_typed_release_backend_v2 import Backend, suite",
            1,
        ).replace(
            'HERE.parent / "live_control/input_owner_v10.py",',
            'HERE.parent / "live_control/input_owner_v10.py",\n'
            '                 HERE.parent / "live_control/input_owner_v11.py",',
            1,
        ).replace(
            'HERE / "doom_typed_release_backend_v1.py",',
            'HERE / "doom_typed_release_backend_v2.py",',
            1,
        )
        self.assertEqual(candidate, expected)

    def test_selected_backend_is_the_typed_release_telemetry_v2(self):
        tree = ast.parse(CANDIDATE.read_text(encoding="utf-8"))
        imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        selected = [node for node in imports if node.module == "doom_typed_release_backend_v2"]
        self.assertEqual(len(selected), 1)
        self.assertEqual([alias.name for alias in selected[0].names], ["Backend", "suite"])
        self.assertFalse(any(node.module == "doom_typed_release_backend_v1"
                             for node in imports))


if __name__ == "__main__":
    unittest.main(verbosity=2)
