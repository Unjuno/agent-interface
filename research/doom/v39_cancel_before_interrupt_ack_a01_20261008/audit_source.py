"""Independent AST/source identity check for the frozen ordering finding."""
import ast
import subprocess

PINS = {
    "research/doom/map01_overlap_controller_v39.py": "e9b437979e87347f6aa4dbefffcc84e9a2d01752",
    "research/live_control/persistent_planner_adapter_v2.py": "1a09c8752dff6a87bf8c180cb2e6fa7f43d4ad77",
    "research/live_control/codex_app_server_client_v2.py": "2eecb3de2d1a3d72c3276d13e148564e9c31481b",
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
        actual = git("rev-parse", f"HEAD:{path}").strip()
        assert actual == blob, (path, actual, blob)
    controller = ast.parse(git("show", "HEAD:research/doom/map01_overlap_controller_v39.py"))
    helper = method(controller, "cancel_invalidated_cover")
    interrupt_i = next(i for i, n in enumerate(helper.body)
                       if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)
                       and call_name(n.value) == "interrupt")
    write_i = next(i for i, n in enumerate(helper.body)
                   if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                   and call_name(n.value) == "write")
    assert interrupt_i < write_i

    adapter = ast.parse(git("show", "HEAD:research/live_control/persistent_planner_adapter_v2.py"))
    interrupt = method(adapter, "interrupt")
    assert isinstance(interrupt, ast.FunctionDef)
    assert any(isinstance(n, ast.Call) and call_name(n) == "interrupt_turn"
               for n in ast.walk(interrupt))

    client = ast.parse(git("show", "HEAD:research/live_control/codex_app_server_client_v2.py"))
    request = method(client, "request")
    assert ast.literal_eval(request.args.defaults[-1]) == 30
    assert any(isinstance(n, ast.Call) and call_name(n) == "wait"
               for n in ast.walk(request))
    print("PASS: pinned source hashes, interrupt-before-cancel AST order, synchronous interrupt call, 30s response-wait default")


if __name__ == "__main__":
    main()
