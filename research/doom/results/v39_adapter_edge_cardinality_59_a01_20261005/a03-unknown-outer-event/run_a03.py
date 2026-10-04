"""Replay the exact regression against frozen baseline and candidate projectors."""
from __future__ import annotations

import ast
import contextlib
import hashlib
import io
import json
from pathlib import Path
import unittest
from types import SimpleNamespace


ROOT = Path("/src")
DOOM = ROOT / "research/doom"
BASELINE = ROOT / "research/doom/results/v39_adapter_edge_cardinality_59_a01_20261005/a03-unknown-outer-event/BASELINE_SOURCE.py"
TESTS = DOOM / "test_map01_v39_typed_state_feedback.py"
RAW = DOOM / "map01_v39_perkey_bridge_a01/results/construction-a01/candidate-events.jsonl"
OUTPUT = Path("/out/A03_RESULT.json")


def load_function(path: Path, name: str, globals_: dict):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    node = next(item for item in tree.body
                if isinstance(item, ast.FunctionDef) and item.name == name)
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    exec(compile(module, str(path), "exec"), globals_)
    return globals_[name]


def run(source: Path, method_names: tuple[str, ...]) -> tuple[bool, str, int, int]:
    projector_globals = {"hashlib": hashlib}
    projector = load_function(source, "input_edge_receipts", projector_globals)
    tree = ast.parse(TESTS.read_text(encoding="utf-8"))
    test_class = next(item for item in tree.body
                      if isinstance(item, ast.ClassDef) and
                      item.name == "V39TypedStateFeedbackTests")
    methods = [next(item for item in test_class.body
                    if isinstance(item, ast.FunctionDef) and item.name == name)
               for name in method_names]
    test_class = ast.ClassDef(
        name="A03UnknownOuterEventTests",
        bases=[ast.Attribute(value=ast.Name(id="unittest", ctx=ast.Load()),
                             attr="TestCase", ctx=ast.Load())],
        keywords=[], body=methods, decorator_list=[])
    test_module = ast.Module(
        body=[ast.Import(names=[ast.alias(name="json")]),
              ast.Import(names=[ast.alias(name="unittest")]), test_class],
        type_ignores=[])
    test_globals = {
        "HERE": DOOM,
        "controller": SimpleNamespace(input_edge_receipts=projector),
    }
    exec(compile(ast.fix_missing_locations(test_module), str(TESTS), "exec"),
         test_globals)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        test_globals["A03UnknownOuterEventTests"])
    stream = io.StringIO()
    with contextlib.redirect_stderr(stream), contextlib.redirect_stdout(stream):
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    return result.wasSuccessful(), stream.getvalue(), result.testsRun, len(result.failures) + len(result.errors)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


method_names = (
    "test_input_edge_receipt_rejects_duplicate_adapter_rows",
    "test_input_edge_receipt_rejects_unknown_outer_event_with_adapter_edge",
)
baseline_ok, baseline_log, baseline_tests, baseline_bad = run(BASELINE, method_names)
candidate_ok, candidate_log, candidate_tests, candidate_bad = run(
    DOOM / "map01_overlap_controller_v39.py", method_names)
record = {
    "experiment": "V39_UNKNOWN_OUTER_EVENT_A03",
    "baseline_commit": "a7f9e9e3c4bd31199bde3a14761783ead619ad08",
    "baseline_source_sha256": digest(BASELINE),
    "candidate_source_sha256": digest(DOOM / "map01_overlap_controller_v39.py"),
    "test_sha256": digest(TESTS),
    "fixture_sha256": digest(RAW),
    "methods": list(method_names),
    "baseline": {"expected_fail": not baseline_ok, "tests": baseline_tests,
                 "failed_tests": baseline_bad, "output": baseline_log},
    "candidate": {"passed": candidate_ok, "tests": candidate_tests,
                   "failed_tests": candidate_bad, "output": candidate_log},
    "subcases": ["duplicate_down_unknown_kind", "duplicate_up_unknown_kind",
                 "down_unknown_kind", "up_unknown_kind"],
}
OUTPUT.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: value for key, value in record.items()
                  if key not in ("baseline", "candidate")}, indent=2))
print("BASELINE\n" + baseline_log)
print("CANDIDATE\n" + candidate_log)
raise SystemExit(0 if (not baseline_ok and candidate_ok) else 1)
