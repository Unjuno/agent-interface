import ast
import hashlib
import json
import py_compile
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from io import StringIO


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


source_path = Path(sys.argv[1])
freeze_path = Path(sys.argv[2])
result_path = Path(sys.argv[3])
freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
test_path = Path("/src/test_map01_v39_typed_state_feedback.py")
fixture_path = (Path("/src/map01_v39_perkey_bridge_a01/results/") /
                "construction-a01/candidate-events.jsonl")
runner_path = Path(__file__)
observed = {
    "source_sha256": sha256(source_path),
    "test_sha256": sha256(test_path),
    "fixture_sha256": sha256(fixture_path),
    "runner_sha256": sha256(runner_path),
}
for key, value in observed.items():
    if freeze["sha256"].get(key) != value:
        raise SystemExit(f"frozen {key} mismatch")

source_tree = ast.parse(source_path.read_text(encoding="utf-8"))
projector = next(node for node in source_tree.body
                 if isinstance(node, ast.FunctionDef) and
                 node.name == "input_edge_receipts")
projector_module = ast.Module(
    body=[ast.Import(names=[ast.alias(name="hashlib")]), projector],
    type_ignores=[])
projector_namespace = {}
exec(compile(ast.fix_missing_locations(projector_module),
             str(source_path), "exec"), projector_namespace)

test_tree = ast.parse(test_path.read_text(encoding="utf-8"))
test_class = next(node for node in test_tree.body
                  if isinstance(node, ast.ClassDef) and
                  node.name == "V39TypedStateFeedbackTests")
method = next(node for node in test_class.body
              if isinstance(node, ast.FunctionDef) and
              node.name == "test_input_edge_receipt_rejects_unknown_outer_adapter_rows")
isolated_class = ast.ClassDef(
    name="UnknownOuterAdapterRowsRegression",
    bases=[ast.Attribute(value=ast.Name(id="unittest", ctx=ast.Load()),
                         attr="TestCase", ctx=ast.Load())],
    keywords=[], body=[method], decorator_list=[])
test_module = ast.Module(
    body=[ast.Import(names=[ast.alias(name="json")]),
          ast.Import(names=[ast.alias(name="unittest")]), isolated_class],
    type_ignores=[])
namespace = {
    "HERE": Path("/src"),
    "controller": SimpleNamespace(
        input_edge_receipts=projector_namespace["input_edge_receipts"]),
}
exec(compile(ast.fix_missing_locations(test_module), str(test_path), "exec"),
     namespace)
suite = unittest.defaultTestLoader.loadTestsFromTestCase(
    namespace["UnknownOuterAdapterRowsRegression"])
capture = StringIO()
test_result = unittest.TextTestRunner(stream=capture, verbosity=2).run(suite)
py_compile.compile(str(source_path), cfile="/tmp/v39-controller.pyc", doraise=True)
py_compile.compile(str(test_path), cfile="/tmp/v39-test.pyc", doraise=True)
failures = len(test_result.failures)
errors = len(test_result.errors)
if freeze["expected"] == "EXPECTED_RED":
    success = failures == 3 and errors == 0
    disposition = "EXPECTED_RED" if success else "RED_GATE_MISMATCH"
elif freeze["expected"] == "PASS":
    success = failures == 0 and errors == 0
    disposition = "PASS" if success else "FAIL"
else:
    raise SystemExit("unknown expected disposition")
report = {
    "disposition": disposition,
    "test": method.name,
    "test_methods": 1,
    "cases": 3,
    "failures": failures,
    "errors": errors,
    "py_compile": "PASS",
    **observed,
    "transcript": capture.getvalue(),
}
result_path.parent.mkdir(parents=True, exist_ok=True)
result_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
if not success:
    raise SystemExit(1)
