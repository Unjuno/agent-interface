#!/usr/bin/env python3
"""Static source-only import-boundary classifier; never imports its target."""
import ast


def call_name(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def is_main_guard(node):
    if not isinstance(node, ast.Compare) or len(node.ops) != 1 or len(node.comparators) != 1:
        return False
    if not isinstance(node.ops[0], (ast.Eq, ast.Is)):
        return False
    left, right = node.left, node.comparators[0]
    pairs = ((left, right), (right, left))
    return any(isinstance(name, ast.Name) and name.id == "__name__"
               and isinstance(value, ast.Constant) and value.value == "__main__"
               for name, value in pairs)


class ModuleCallWalker:
    """Find calls evaluated while module code executes, including class bodies."""
    def __init__(self):
        self.calls = []

    def expressions(self, node, zone):
        if node is None:
            return
        if isinstance(node, ast.Lambda):
            # Constructing a lambda does not evaluate its body.
            for default in node.args.defaults + node.args.kw_defaults:
                self.expressions(default, zone)
            return
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for expr in [*node.decorator_list, *node.args.defaults, *node.args.kw_defaults,
                         node.returns]:
                self.expressions(expr, zone)
            return
        if isinstance(node, ast.ClassDef):
            for expr in [*node.decorator_list, *node.bases,
                         *(keyword.value for keyword in node.keywords)]:
                self.expressions(expr, zone)
            for statement in node.body:
                self.statement(statement, zone)
            return
        if isinstance(node, ast.Call):
            self.calls.append({"name": call_name(node.func), "line": node.lineno,
                               "zone": zone})
        for child in ast.iter_child_nodes(node):
            self.expressions(child, zone)

    def statement(self, node, zone="module"):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for expr in [*node.decorator_list, *node.args.defaults, *node.args.kw_defaults,
                         node.returns]:
                self.expressions(expr, zone)
            return
        if isinstance(node, ast.ClassDef):
            self.expressions(node, zone)
            return
        if isinstance(node, ast.If):
            self.expressions(node.test, zone)
            body_zone = "main_guard" if is_main_guard(node.test) else zone
            for child in node.body:
                self.statement(child, body_zone)
            for child in node.orelse:
                self.statement(child, zone)
            return
        if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            self.expressions(getattr(node, "iter", None), zone)
            self.expressions(getattr(node, "test", None), zone)
            for child in node.body + node.orelse:
                self.statement(child, zone)
            return
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                self.expressions(item.context_expr, zone)
            for child in node.body:
                self.statement(child, zone)
            return
        if isinstance(node, (ast.Try, getattr(ast, "TryStar", ast.Try))):
            for child in node.body + node.orelse + node.finalbody:
                self.statement(child, zone)
            for handler in node.handlers:
                self.expressions(handler.type, zone)
                for child in handler.body:
                    self.statement(child, zone)
            return
        if isinstance(node, ast.Match):
            self.expressions(node.subject, zone)
            for case in node.cases:
                self.expressions(case.guard, zone)
                for child in case.body:
                    self.statement(child, zone)
            return
        self.expressions(node, zone)

    def parse(self, source, filename="<source>"):
        tree = ast.parse(source, filename=filename)
        for statement in tree.body:
            self.statement(statement)
        return self.calls


def classify(source, filename="<source>"):
    calls = ModuleCallWalker().parse(source, filename)
    return {"module_calls": [call for call in calls if call["zone"] != "main_guard"],
            "main_guard_calls": [call for call in calls if call["zone"] == "main_guard"]}
