import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "live_control")]
import map01_overlap_controller_v39 as controller


class TailSessionSelectionTests(unittest.TestCase):
    def test_default_session_remains_v12(self):
        args = SimpleNamespace(seed=7, load_fixture_manifest=Path("fixture.json"))
        command = controller.session_command(args, Path("runtime"))
        self.assertTrue(command[1].endswith("session_map01_v12.py"))

    def test_opt_in_session_selects_tail_composition(self):
        args = SimpleNamespace(seed=7, load_fixture_manifest=Path("fixture.json"),
                               post_release_scorer_tail=True)
        command = controller.session_command(args, Path("runtime"))
        self.assertTrue(command[1].endswith("session_map01_v18.py"))


if __name__ == "__main__":
    unittest.main()
