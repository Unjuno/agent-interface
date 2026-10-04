"""Independent audit of retained A01 outputs and the candidate custody fix."""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "research/doom/doom_owner_thread_release_batch_backend_v1.py"
TESTS = ROOT / "research/doom/test_release_backend_v3_actual_composition.py"
PARENT = "12522ccd0b58d3333da1d241d1b04f2c888c46e6"
PARENT_BLOB = "924c99a3838ba49ad0b4ec07aaa568b1a09a1713"
PARENT_TEST_BLOB = "e0a1371247ed1b61ac177503102e64f5710569d3"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("FAIL_AUDIT: " + message)


def read_exit(folder: Path, name: str) -> int:
    return int((folder / name).read_text(encoding="utf-8").strip())


baseline = HERE / "wslc-baseline"
candidate = HERE / "wslc-candidate"
baseline_out = (baseline / "BASELINE_WSL_OUTPUT.txt").read_text(encoding="utf-8")
candidate_out = (candidate / "CANDIDATE_WSL_OUTPUT.txt").read_text(encoding="utf-8")
windows_out = (HERE / "WINDOWS_TEST_OUTPUT.txt").read_text(encoding="utf-8")
matrix = HERE / "wslc-matrix"
matrix_out = (matrix / "MATRIX_WSL_OUTPUT.txt").read_text(encoding="utf-8")
windows_matrix = HERE / "windows-matrix"
windows_matrix_out = (windows_matrix / "MATRIX_WINDOWS_OUTPUT.txt").read_text(encoding="utf-8")

require(read_exit(baseline, "BASELINE_WSL_EXIT_CODE.txt") == 1,
        "frozen parent mutation tests did not exit 1")
require(baseline_out.count("... FAIL") == 2,
        "parent did not fail both mutation regressions")
require(baseline_out.count("'not_attempted'") >= 2 and
        baseline_out.count("'unknown'") >= 2,
        "parent output lacks the not_attempted-versus-unknown counterexample")
require(read_exit(candidate, "CANDIDATE_WSL_EXIT_CODE.txt") == 0,
        "candidate WSLc suite did not exit 0")
require("Ran 12 tests" in candidate_out and candidate_out.rstrip().endswith("OK"),
        "candidate WSLc suite is not 12/12 OK")
require(read_exit(HERE, "WINDOWS_TEST_EXIT_CODE.txt") == 0,
        "candidate Windows suite did not exit 0")
require("Ran 12 tests" in windows_out and windows_out.rstrip().endswith("OK"),
        "candidate Windows suite is not 12/12 OK")
require(read_exit(matrix, "MATRIX_WSL_EXIT_CODE.txt") == 0 and
        matrix_out.count("... ok") == 2 and matrix_out.rstrip().endswith("OK"),
        "expanded WSLc first/middle/last acceptance matrix did not pass")
require(read_exit(windows_matrix, "MATRIX_WINDOWS_EXIT_CODE.txt") == 0 and
        "Ran 12 tests" in windows_matrix_out and windows_matrix_out.rstrip().endswith("OK"),
        "expanded Windows backend suite is not 12/12 OK")

parent_blob = subprocess.run(
    ["git", "rev-parse", f"{PARENT}:research/doom/doom_owner_thread_release_batch_backend_v1.py"],
    cwd=ROOT, check=True, capture_output=True, text=True,
).stdout.strip()
require(parent_blob == PARENT_BLOB, "frozen parent backend blob changed")
parent_test_blob = subprocess.run(
    ["git", "rev-parse", f"{PARENT}:research/doom/test_release_backend_v3_actual_composition.py"],
    cwd=ROOT, check=True, capture_output=True, text=True,
).stdout.strip()
require(parent_test_blob == PARENT_TEST_BLOB, "frozen parent test blob changed")

tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
backend = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Backend")
method = next(node for node in backend.body if isinstance(node, ast.FunctionDef)
              and node.name == "_set_delivery_state")
params = [arg.arg for arg in method.args.args]
require(params == ["self", "context", "position", "state"],
        "delivery-state update still depends on a mutable row")

publish_methods = [node for node in backend.body if isinstance(node, ast.FunctionDef)
                   and node.name in ("_publish_incomplete_release_batch", "_publish_release_batch")]
for method in publish_methods:
    calls = [node for node in ast.walk(method) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute)
             and node.func.attr == "_set_delivery_state"]
    require(len(calls) == 2, f"{method.name} lacks both confirmed/unknown state updates")
    require(all(len(call.args) == 3 and isinstance(call.args[1], ast.Name)
                and call.args[1].id == "position" for call in calls),
            f"{method.name} does not use the frozen position scalar")
    emit_calls = [node for node in ast.walk(method) if isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Attribute) and node.func.attr == "emit"]
    require(len(emit_calls) == 1, f"{method.name} publication boundary changed unexpectedly")
    emit_line = emit_calls[0].lineno
    position_lines = [node.lineno for node in ast.walk(method)
                      if isinstance(node, ast.Assign)
                      and any(isinstance(target, ast.Name) and target.id == "position"
                              for target in node.targets)]
    require(position_lines and min(position_lines) < emit_line,
            f"{method.name} does not capture position before emit")

for path in (SOURCE, TESTS):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"SHA256 {path.relative_to(ROOT)} {digest}")
print("PASS_AUDIT parent-red=2/2 candidate-wslc=12/12 candidate-windows=12/12 matrix-wslc=12-cases")
