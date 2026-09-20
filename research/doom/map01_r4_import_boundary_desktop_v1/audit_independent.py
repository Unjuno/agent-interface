"""Independent stdlib-only AST oracle; intentionally does not import runner.py."""
import ast
import hashlib
import json
import pathlib
import sys


def name(n):
    if isinstance(n, ast.Name):
        return n.id
    if isinstance(n, ast.Attribute):
        return n.attr
    return "<dynamic>"


def guard(n):
    return (isinstance(n, ast.If) and isinstance(n.test, ast.Compare)
            and isinstance(n.test.left, ast.Name) and n.test.left.id == "__name__"
            and len(n.test.ops) == 1 and isinstance(n.test.ops[0], ast.Eq)
            and len(n.test.comparators) == 1
            and isinstance(n.test.comparators[0], ast.Constant)
            and n.test.comparators[0].value == "__main__")


def expression_calls(expr):
    found = []
    def visit(n):
        if isinstance(n, ast.Lambda):
            return
        if isinstance(n, ast.Call):
            found.append(name(n.func))
        for child in ast.iter_child_nodes(n):
            visit(child)
    visit(expr)
    return found


def scan(tree):
    result = []

    def body(statements, ctx="module"):
        for n in statements:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for x in n.decorator_list:
                    result.extend((v, "decorator") for v in expression_calls(x))
                for x in list(n.args.defaults) + [v for v in n.args.kw_defaults if v is not None]:
                    result.extend((v, "default_argument") for v in expression_calls(x))
            elif isinstance(n, ast.ClassDef):
                for x in n.decorator_list:
                    result.extend((v, "decorator") for v in expression_calls(x))
                for x in n.bases + [k.value for k in n.keywords]:
                    result.extend((v, "class_header") for v in expression_calls(x))
                body(n.body, "class_body")
            elif guard(n):
                result.extend((v, "main_guard_test") for v in expression_calls(n.test))
                body(n.body, "main_guarded")
                body(n.orelse, "main_guard_else")
            elif isinstance(n, ast.Try):
                body(n.body, "module")
                for handler in n.handlers:
                    if handler.type is not None:
                        result.extend((v, "conditional_top_level") for v in expression_calls(handler.type))
                    body(handler.body, "conditional_top_level")
                body(n.orelse, "module")
                body(n.finalbody, "module")
            elif isinstance(n, (ast.If, ast.For, ast.AsyncFor, ast.While,
                                ast.With, ast.AsyncWith, ast.Match)):
                for field, value in ast.iter_fields(n):
                    if isinstance(value, ast.expr):
                        result.extend((v, "conditional_top_level") for v in expression_calls(value))
                    elif isinstance(value, list):
                        body([v for v in value if isinstance(v, ast.stmt)], "conditional_top_level")
            else:
                result.extend((v, ctx) for v in expression_calls(n))

    body(tree.body)
    return result


def main():
    root = pathlib.Path(__file__).resolve().parent
    data = root / "inputs"
    target = (data / "session_entry.py").read_text(encoding="utf-8")
    gate_text = (data / "import_gate.py").read_text(encoding="utf-8")
    expected = {
        "deferred_function": [], "main_guard": [("main", "main_guarded")],
        "direct_top_level": [("main", "module")],
        "conditional_top_level": [("ready", "conditional_top_level"),
                                  ("main", "conditional_top_level")],
        "decorator": [("decorate", "decorator")],
        "default_argument": [("build", "default_argument")],
        "class_body": [("main", "class_body")], "lambda_body": [],
    }
    sources = {
        "deferred_function": "def f():\n    main()\n",
        "main_guard": "if __name__ == '__main__':\n    main()\n",
        "direct_top_level": "main()\n",
        "conditional_top_level": "if ready():\n    main()\n",
        "decorator": "@decorate()\ndef f():\n    pass\n",
        "default_argument": "def f(x=build()):\n    pass\n",
        "class_body": "class C:\n    main()\n",
        "lambda_body": "callback = lambda: main()\n",
    }
    checks = {key: scan(ast.parse(source)) == value for key, source in sources.items()
              for value in [expected[key]]}
    target_rows = scan(ast.parse(target))
    gate_rows = scan(ast.parse(gate_text))
    report = {"status": "PASS_INDEPENDENT_AUDIT",
              "target_module_calls": target_rows,
              "gate_module_calls": gate_rows,
              "target_is_unguarded_main": ("main", "module") in target_rows,
              "controls": checks,
              "input_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in (data / "session_entry.py", data / "import_gate.py")},
              "endpoint_counts": {k: 0 for k in
                                  ("target_import", "target_execution", "game", "model", "input")}}
    if not all(checks.values()) or not report["target_is_unguarded_main"]:
        report["status"] = "FAIL_INDEPENDENT_AUDIT"
    pathlib.Path("/evidence/audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "target_unguarded_main": report["target_is_unguarded_main"],
                      "controls_pass": sum(checks.values())}, sort_keys=True))
    return 0 if report["status"] == "PASS_INDEPENDENT_AUDIT" else 3


if __name__ == "__main__":
    raise SystemExit(main())
