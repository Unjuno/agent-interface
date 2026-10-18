"""Keep stale rejection from falling through into ordinary iteration completion."""
import ast
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
CONTROLLER = HERE / "map01_overlap_controller_v39.py"


class StaleRejectionContinueTests(unittest.TestCase):
    def test_stale_rejection_branch_continues_outer_control_loop(self):
        source = CONTROLLER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        main = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "main")
        loops = [
            node for node in ast.walk(main)
            if isinstance(node, ast.For)
            and isinstance(node.target, ast.Name)
            and node.target.id == "index"
            and isinstance(node.iter, ast.Call)
            and isinstance(node.iter.func, ast.Name)
            and node.iter.func.id == "range"
            and len(node.iter.args) == 1
            and isinstance(node.iter.args[0], ast.Attribute)
            and isinstance(node.iter.args[0].value, ast.Name)
            and node.iter.args[0].value.id == "args"
            and node.iter.args[0].attr == "iterations"]
        self.assertEqual(len(loops), 1)
        loop = loops[0]
        stale_branch = next(
            node for node in loop.body
            if isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Name)
            and node.test.left.id == "stale_rejection"
            and len(node.test.ops) == 1
            and isinstance(node.test.ops[0], ast.IsNot)
            and len(node.test.comparators) == 1
            and isinstance(node.test.comparators[0], ast.Constant)
            and node.test.comparators[0].value is None)

        self.assertIsInstance(
            stale_branch.body[-1], ast.Continue,
            "stale rejection must skip normal completion and continue the outer iteration")


if __name__ == "__main__":
    unittest.main(verbosity=2)
