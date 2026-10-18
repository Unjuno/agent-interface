import ast
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
spec = importlib.util.spec_from_file_location("issue8135_generate", ROOT / "generate.py")
generate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate)


class ConstructionTests(unittest.TestCase):
    def test_factorial_schedule_and_truth_separation(self):
        d = generate.build()
        self.assertEqual(len(d["manifest"]["blocks"]), 40)
        self.assertEqual(len(d["manifest"]["episodes"]), 80)
        self.assertEqual(len(d["truth"]["cases"]), 80)
        self.assertEqual(d["manifest"]["seed"], 20261006)
        self.assertNotIn("truth", d["manifest"])
        self.assertEqual({x["seed_public_history"] for x in d["manifest"]["blocks"]}, {"H_FAST", "H_CHECKED"})
        self.assertEqual({tuple(x["route_order"]) for x in d["manifest"]["blocks"]}, {("plain", "effect_boundary"), ("effect_boundary", "plain")})
        self.assertEqual(len({x["block_id"] for x in d["manifest"]["blocks"]}), 40)

    def test_selector_interfaces_are_narrow(self):
        source = (ROOT / "candidate.py").read_text()
        tree = ast.parse(source)
        node = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "choose_variant")
        self.assertEqual([x.arg for x in node.args.args], ["arm", "prior_public_event", "sham_assignment", "episode_index"])
        self.assertNotIn("sealed_truth", source)
        self.assertNotIn("authorization_truth", source)

    def test_container_isolation_and_one_shot_runner_gates(self):
        run = (ROOT / "run_formal.py").read_text()
        execute = (ROOT / "execute_formal.py").read_text()
        self.assertIn("--network=none", run)
        self.assertIn("--read-only", run)
        self.assertIn("candidate_invocations", run)
        self.assertIn("auditor_invocations", run)
        self.assertLess(execute.index("prepare_freeze.py"), execute.index("run_formal.py"))


if __name__ == "__main__":
    unittest.main()
