"""Independent AST/source identity check for the frozen ordering finding."""
import ast
import subprocess

SOURCE_REF = "708ca59a8128f07fdb7e13a36704c6b2f79c9fb6"
PINS = {
    "research/doom/map01_overlap_controller_v39.py": "fcd97a2483327fc6812b4cd134816cfe5193bf4f",
    "research/live_control/persistent_planner_adapter_v2.py": "e2566d063f9aeba77ea74a3996625fe80425d9f6",
    "research/live_control/codex_app_server_client_v2.py": "8553874221761a7807c846c7dcd66c22fc6340ff",
}


def git(*args):
    return subprocess.check_output(["git", *args], text=True)


def method(tree, name):
    return next(n for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and n.name == name)


def call_name(node):
    fn = node.func
    return fn.attr if isinstance(fn, ast.Attribute) else fn.id if isinstance(fn, ast.Name) else ""


def main():
    for path, blob in PINS.items():
        actual = git("rev-parse", f"{SOURCE_REF}:{path}").strip()
        assert actual == blob, (path, actual, blob)
    controller = ast.parse(git("show", f"{SOURCE_REF}:research/doom/map01_overlap_controller_v39.py"))
    helper = method(controller, "cancel_invalidated_cover")
    interrupt_i = next(i for i, n in enumerate(helper.body)
                       if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)
                       and call_name(n.value) == "interrupt")
    write_i = next(i for i, n in enumerate(helper.body)
                   if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                   and call_name(n.value) == "write")
    assert interrupt_i < write_i

    adapter = ast.parse(git("show", f"{SOURCE_REF}:research/live_control/persistent_planner_adapter_v2.py"))
    interrupt = method(adapter, "interrupt")
    assert isinstance(interrupt, ast.FunctionDef)
    assert any(isinstance(n, ast.Call) and call_name(n) == "interrupt_turn"
               for n in ast.walk(interrupt))

    client = ast.parse(git("show", f"{SOURCE_REF}:research/live_control/codex_app_server_client_v2.py"))
    request = method(client, "request")
    assert ast.literal_eval(request.args.defaults[-1]) == 30
    assert any(isinstance(n, ast.Call) and call_name(n) == "wait"
               for n in ast.walk(request))
    print("PASS: pinned source hashes, interrupt-before-cancel AST order, synchronous interrupt call, 30s response-wait default")


if __name__ == "__main__":
    main()
