"""Read-only source audit of V39 renewal invalidation control flow."""
import ast
import sys
from pathlib import Path

path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    Path(__file__).resolve().parents[1] / "map01_overlap_controller_v39.py")
tree = ast.parse(path.read_text(encoding="utf-8"))
main = next(node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main")
invalidation_branch = next(node for node in ast.walk(main)
                           if isinstance(node, ast.If)
                           and "next_accepted" in ast.dump(node.test)
                           and "policy_invalidation" in ast.dump(node.test))
branch = ast.unparse(invalidation_branch)
assert "resolve_invalidated_cover_renewal" in branch
assert "if renewal_admitted" in branch
assert "cover_terminals.append(current_terminal)" in branch
assert "current_cover = next_cover" not in branch
resolver = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef)
                and node.name == "resolve_invalidated_cover_renewal")
assert "resolution[\"status\"] == \"rejected\"" in ast.unparse(resolver)
assert "planner.interrupt(planner_handle)" in ast.unparse(resolver)
discard = next(node for node in ast.walk(main)
               if isinstance(node, ast.If)
               and isinstance(node.test, ast.Compare)
               and isinstance(node.test.left, ast.Name)
               and node.test.left.id == "invalidation"
               and any(isinstance(part, ast.Constant) and part.value is None
                       for part in node.test.comparators))
assert any(isinstance(node, ast.Continue) for node in ast.walk(discard))
assert "policy_dependency_invalidated" in ast.unparse(discard)
print("read-only renewal invalidation audit: PASS 7/7")
