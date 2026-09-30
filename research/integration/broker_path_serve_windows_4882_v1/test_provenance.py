"""Fixture-free source provenance and narrow candidate-delta checks."""
import ast
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent


def top_level_map(path: Path) -> dict[str, ast.AST]:
    return {node.name: node for node in ast.parse(path.read_text(encoding="utf-8")).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


class ProvenanceTests(unittest.TestCase):
    def test_candidate_resolver_matches_pinned_upstream_module(self):
        candidate = ast.parse((HERE / "path_policy.py").read_text(encoding="utf-8"))
        upstream = ast.parse((HERE / "upstream_path_policy.py").read_text(encoding="utf-8"))
        self.assertEqual(ast.dump(candidate, include_attributes=False),
                         ast.dump(upstream, include_attributes=False))

    def test_broker_candidate_changes_only_path_adapter_and_rejection_mapping(self):
        upstream_tree = ast.parse((HERE / "upstream_broker.py").read_text(encoding="utf-8"))
        candidate_tree = ast.parse((HERE / "broker_under_test.py").read_text(encoding="utf-8"))
        upstream = top_level_map(HERE / "upstream_broker.py")
        candidate = top_level_map(HERE / "broker_under_test.py")
        self.assertEqual(set(upstream), set(candidate))
        changed = {name for name in upstream
                   if ast.dump(upstream[name], include_attributes=False) !=
                   ast.dump(candidate[name], include_attributes=False)}
        self.assertEqual(changed, {"host_path", "serve"})
        upstream_other = [node for node in upstream_tree.body
                          if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        candidate_other = [node for node in candidate_tree.body
                           if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                           and not (isinstance(node, ast.ImportFrom) and node.module == "path_policy")]
        self.assertEqual([ast.dump(node, include_attributes=False) for node in upstream_other],
                         [ast.dump(node, include_attributes=False) for node in candidate_other])


if __name__ == "__main__":
    unittest.main()
