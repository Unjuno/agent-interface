#!/usr/bin/env python3
"""Independent AST walk over retained source and result; imports no target."""
import ast
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path("/source")
TARGET = "research/doom/map01_v12_physical_occupancy_live_r1_v1/session_entry.py"
GATE = "research/doom/map01_r4_sparse_checkout_successor_2174/import_gate.py"
FILES = {"target": TARGET, "gate": GATE,
         "analyzer": "research/doom/map01_r4_import_boundary_desktop_v1/analyzer.py",
         "formal": "research/doom/map01_r4_import_boundary_desktop_v1/formal.py",
         "verifier": "research/doom/map01_r4_import_boundary_desktop_v1/verify.py",
         "construction": "research/doom/map01_r4_import_boundary_desktop_v1/construction.py"}
BASE_COMMIT = "8652f6a3527d55610185d1103b87d5d9fd8fa985"
IMAGE_ID = "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"


class ImportTimeCalls(ast.NodeVisitor):
    """Separate import-time evaluation from function-local execution."""
    def __init__(self):
        self.zone = "module"
        self.rows = []

    @staticmethod
    def name(node):
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            prefix = ImportTimeCalls.name(node.value)
            return prefix + "." + node.attr if prefix else node.attr
        return ""

    @staticmethod
    def main_guard(node):
        if not isinstance(node, ast.Compare) or len(node.ops) != 1 or len(node.comparators) != 1:
            return False
        sides = ((node.left, node.comparators[0]), (node.comparators[0], node.left))
        return any(isinstance(left, ast.Name) and left.id == "__name__"
                   and isinstance(right, ast.Constant) and right.value == "__main__"
                   and isinstance(node.ops[0], (ast.Eq, ast.Is)) for left, right in sides)

    def visit_Call(self, node):
        self.rows.append({"name": self.name(node.func), "line": node.lineno,
                          "zone": self.zone})
        self.generic_visit(node)

    def _deferred(self, node):
        for decorator in node.decorator_list:
            self.visit(decorator)
        for default in node.args.defaults + node.args.kw_defaults:
            if default is not None:
                self.visit(default)
        if node.returns is not None:
            self.visit(node.returns)

    def visit_FunctionDef(self, node):
        self._deferred(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, node):
        for default in node.args.defaults + node.args.kw_defaults:
            if default is not None:
                self.visit(default)

    def visit_ClassDef(self, node):
        for decorator in node.decorator_list:
            self.visit(decorator)
        for base in node.bases:
            self.visit(base)
        for keyword in node.keywords:
            self.visit(keyword.value)
        for statement in node.body:
            self.visit(statement)

    def visit_If(self, node):
        self.visit(node.test)
        old = self.zone
        if self.main_guard(node.test):
            self.zone = "main_guard"
        for statement in node.body:
            self.visit(statement)
        self.zone = old
        for statement in node.orelse:
            self.visit(statement)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    formal_path, audit_path = Path(sys.argv[1]), Path(sys.argv[2])
    formal_bytes = formal_path.read_bytes()
    formal = json.loads(formal_bytes)
    source_bytes = {key: (ROOT / path).read_bytes() for key, path in FILES.items()}
    hashes = {FILES[key]: sha(data) for key, data in source_bytes.items()}
    target_bytes = source_bytes["target"]
    errors = []
    if os.environ.get("EXPECTED_MAIN", "") != BASE_COMMIT:
        errors.append("BASE_COMMIT_MISMATCH")
    if os.environ.get("IMAGE_ID", "") != IMAGE_ID:
        errors.append("IMAGE_ID_MISMATCH")
    expected_hashes = {FILES[key]: os.environ.get("EXPECTED_" + key.upper(), "")
                       for key in FILES}
    if hashes != expected_hashes or formal.get("source_hashes") != hashes:
        errors.append("SOURCE_HASH_MISMATCH")
    if formal.get("base_commit") != BASE_COMMIT or formal.get("image_id") != IMAGE_ID:
        errors.append("FORMAL_PROVENANCE_MISMATCH")
    tree = ast.parse(target_bytes.decode("utf-8"), filename=TARGET)
    walker = ImportTimeCalls()
    walker.visit(tree)
    unguarded_launches = [row for row in walker.rows
                          if row["zone"] == "module"
                          and row["name"] == "session_map01_v13.main"]
    if not unguarded_launches:
        errors.append("TARGET_LAUNCH_CLASSIFICATION_MISMATCH")
    if formal.get("target_launch_classification") != "UNGUARDED_MODULE_EXECUTION":
        errors.append("FORMAL_TARGET_DISPOSITION_MISMATCH")
    expected_controls = 8
    if formal.get("controls_expected") != expected_controls or formal.get("controls_passed") != expected_controls:
        errors.append("CONTROL_DENOMINATOR_MISMATCH")
    control_contract = {
        "deferred_function": ("def f():\n    main()\n", [], []),
        "main_guard": ("if __name__ == '__main__':\n    main()\n", [], ["main"]),
        "unguarded_call": ("main()\n", ["main"], []),
        "conditional_call": ("if True:\n    main()\n", ["main"], []),
        "decorator_call": ("@build()\ndef f():\n    pass\n", ["build"], []),
        "default_call": ("def f(arg=build()):\n    pass\n", ["build"], []),
        "class_body_call": ("class C:\n    main()\n", ["main"], []),
        "lambda_body_deferred": ("f = lambda: main()\n", [], []),
    }
    control_rows = formal.get("controls", [])
    if {row.get("name") for row in control_rows} != set(control_contract):
        errors.append("CONTROL_NAMES_MISMATCH")
    for row in control_rows:
        contract = control_contract.get(row.get("name"))
        if contract is None:
            continue
        source, expected_module, expected_guard = contract
        control_walker = ImportTimeCalls()
        control_walker.visit(ast.parse(source))
        module_names = [entry["name"] for entry in control_walker.rows
                        if entry["zone"] == "module"]
        guard_names = [entry["name"] for entry in control_walker.rows
                       if entry["zone"] == "main_guard"]
        if row.get("source") != source or module_names != expected_module or guard_names != expected_guard:
            errors.append("CONTROL_CLASSIFICATION_MISMATCH:" + row.get("name", "?"))
        if (row.get("expected_module_names") != expected_module
                or row.get("expected_main_guard_names") != expected_guard):
            errors.append("CONTROL_EXPECTATION_MISMATCH:" + row.get("name", "?"))
    deferred = next((row for row in control_rows if row.get("name") == "deferred_function"), {})
    if deferred.get("legacy_whole_tree_flags_main") is not True:
        errors.append("LEGACY_OVERAPPROXIMATION_NOT_REPRODUCED")
    endpoints = formal.get("execution_endpoints", {})
    if any(endpoints.get(key) != 0 for key in ("target_import", "target_execution", "game", "model", "input")):
        errors.append("FORBIDDEN_ENDPOINT_RECORDED")
    if formal.get("disposition") != "PASS_STATIC_IMPORT_BOUNDARY_SCOPED":
        errors.append("FORMAL_DISPOSITION_MISMATCH")
    report = {"schema": "issue-3857/import-boundary-independent-audit-v1",
              "formal_result_sha256": sha(formal_bytes),
              "reparsed_target_source_hashes": hashes,
              "independently_found_unguarded_launches": unguarded_launches,
              "errors": errors,
              "decision": "AUDIT_PASS" if not errors else "AUDIT_FAIL"}
    audit_path.write_bytes(json.dumps(report, sort_keys=True,
                                     separators=(",", ":")).encode() + b"\n")
    print(json.dumps({"decision": report["decision"], "errors": len(errors),
                      "unguarded_launches": len(unguarded_launches)}, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
