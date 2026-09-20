"""Side-effect-aware, source-text-only module-call classifier for one static audit."""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import sys


def call_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return "<dynamic>"


def calls_in_expr(node: ast.AST, context: str, rows: list[dict]) -> None:
    def visit(child: ast.AST) -> None:
        if isinstance(child, ast.Lambda):
            return
        if isinstance(child, ast.Call):
            rows.append({"call": call_name(child.func), "context": context,
                         "line": child.lineno})
        for descendant in ast.iter_child_nodes(child):
            visit(descendant)
    visit(node)


def is_main_guard(node: ast.If) -> bool:
    test = node.test
    return (isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name) and test.left.id == "__name__"
            and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq)
            and len(test.comparators) == 1
            and isinstance(test.comparators[0], ast.Constant)
            and test.comparators[0].value == "__main__")


def module_calls(tree: ast.Module) -> list[dict]:
    rows: list[dict] = []

    def statements(items: list[ast.stmt], context: str) -> None:
        for node in items:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    calls_in_expr(decorator, "decorator", rows)
                for default in [*node.args.defaults, *node.args.kw_defaults]:
                    if default is not None:
                        calls_in_expr(default, "default_argument", rows)
                # Function/lambda body is deferred; decorators/defaults are not.
            elif isinstance(node, ast.ClassDef):
                for decorator in node.decorator_list:
                    calls_in_expr(decorator, "decorator", rows)
                for base in node.bases:
                    calls_in_expr(base, "class_header", rows)
                for keyword in node.keywords:
                    calls_in_expr(keyword.value, "class_header", rows)
                statements(node.body, "class_body")
            elif isinstance(node, ast.If) and is_main_guard(node):
                calls_in_expr(node.test, "main_guard_test", rows)
                statements(node.body, "main_guarded")
                statements(node.orelse, "main_guard_else")
            elif isinstance(node, ast.Try):
                statements(node.body, "module")
                for handler in node.handlers:
                    if handler.type is not None:
                        calls_in_expr(handler.type, "conditional_top_level", rows)
                    statements(handler.body, "conditional_top_level")
                statements(node.orelse, "module")
                statements(node.finalbody, "module")
            elif isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While,
                                   ast.With, ast.AsyncWith, ast.Match)):
                # These statements execute conditionally during module evaluation.
                for field, value in ast.iter_fields(node):
                    if isinstance(value, ast.expr):
                        calls_in_expr(value, "conditional_top_level", rows)
                    elif isinstance(value, list):
                        statements([x for x in value if isinstance(x, ast.stmt)],
                                   "conditional_top_level")
            else:
                calls_in_expr(node, context, rows)

    statements(tree.body, "module")
    return rows


CONTROLS = {
    "deferred_function": ("def f():\n    main()\n", []),
    "main_guard": ("if __name__ == '__main__':\n    main()\n", ["main"]),
    "direct_top_level": ("main()\n", ["main"]),
    "conditional_top_level": ("if ready():\n    main()\n", ["ready", "main"]),
    "decorator": ("@decorate()\ndef f():\n    pass\n", ["decorate"]),
    "default_argument": ("def f(x=build()):\n    pass\n", ["build"]),
    "class_body": ("class C:\n    main()\n", ["main"]),
    "lambda_body": ("callback = lambda: main()\n", []),
}


def classify(source: str) -> list[dict]:
    return module_calls(ast.parse(source))


def main() -> int:
    root = pathlib.Path(__file__).resolve().parent
    inputs = root / "inputs"
    gate = (inputs / "import_gate.py").read_text(encoding="utf-8")
    target = (inputs / "session_entry.py").read_text(encoding="utf-8")
    controls = {}
    for name, (source, expected) in CONTROLS.items():
        rows = classify(source)
        actual = [r["call"] for r in rows if r["context"] not in
                  {"main_guard_test", "main_guard_else"}]
        controls[name] = {"expected": expected, "actual": actual,
                          "pass": actual == expected}
    target_rows = module_calls(ast.parse(target, filename="frozen/session_entry.py"))
    gate_rows = module_calls(ast.parse(gate, filename="frozen/import_gate.py"))
    result = {
        "status": "PASS_STATIC_IMPORT_BOUNDARY_SCOPED",
        "allocation": "issue-3896-dockerdesktop-import-boundary-audit-01",
        "target_disposition": "REFUSE_UNGUARDED_MODULE_LAUNCH" if any(
            row["call"] == "main" and row["context"] == "module"
            for row in target_rows) else "NO_UNGUARDED_MAIN_FOUND",
        "target_module_calls": target_rows,
        "import_gate_module_calls": gate_rows,
        "controls": controls,
        "counts": {"target_import": 0, "target_execution": 0, "game": 0,
                   "model": 0, "input": 0, "construction": 0, "formal": 0},
        "inputs": {name: hashlib.sha256((inputs / name).read_bytes()).hexdigest()
                   for name in ("import_gate.py", "session_entry.py")},
        "python": sys.version,
    }
    if not all(c["pass"] for c in controls.values()) or result["target_disposition"] != "REFUSE_UNGUARDED_MODULE_LAUNCH":
        result["status"] = "FAIL_CLASSIFIER"
    out = pathlib.Path("/evidence")
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    # One formal Docker process runs the candidate and independent oracle; there is
    # no second allocation if the candidate reports a failure.
    import audit_independent
    audit_exit = audit_independent.main()
    print(json.dumps({"status": result["status"], "target": result["target_disposition"],
                      "controls_pass": sum(c["pass"] for c in controls.values()),
                      "independent_exit": audit_exit}, sort_keys=True))
    return 0 if result["status"] == "PASS_STATIC_IMPORT_BOUNDARY_SCOPED" and audit_exit == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
