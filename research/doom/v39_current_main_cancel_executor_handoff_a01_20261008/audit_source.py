"""Independent provenance and event-order audit for the retained replay."""
import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path):
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def method(tree, class_name, method_name):
    cls = next(node for node in ast.walk(tree)
               if isinstance(node, ast.ClassDef) and node.name == class_name)
    return next(node for node in cls.body
                if isinstance(node, ast.FunctionDef) and node.name == method_name)


def function(tree, name):
    return next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == name)


def call_attr(node, name):
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == name


def audit():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    listed = {item["path"] for item in manifest["files"]}
    actual = {path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*")
              if path.is_file() and "__pycache__" not in path.parts and
              path.name not in {"MANIFEST.json", "AUDIT.json"}}
    assert actual == listed, (sorted(actual - listed), sorted(listed - actual))
    for item in manifest["files"]:
        path = ROOT / item["path"]
        assert path.stat().st_size == item["bytes"]
        assert sha256(path) == item["sha256"]
    for item in freeze["current_main_sources"]:
        path = ROOT / item["local_path"]
        assert path.stat().st_size == item["bytes"]
        assert sha256(path) == item["sha256"]
        assert git_blob(path) == item["git_blob"]
    for item in freeze["executor_stack_modules"]:
        path = ROOT / "source" / "executor_v13_stack" / item["name"]
        assert path.stat().st_size == item["bytes"]
        assert sha256(path) == item["sha256"]
        assert git_blob(path) == item["git_blob"]

    controller = ast.parse((ROOT / "source/controller_v39.py").read_text(encoding="utf-8"))
    helper = function(controller, "cancel_invalidated_cover")
    interrupt = next(node for node in ast.walk(helper)
                     if call_attr(node, "interrupt"))
    before_transport = next(keyword.value for keyword in interrupt.keywords
                            if keyword.arg == "before_transport")
    assert isinstance(before_transport, ast.Name)
    assert before_transport.id == "cancel_executor_program"
    cancel_callback = function(ast.Module(body=helper.body, type_ignores=[]),
                               "cancel_executor_program")
    callback_calls = [node for node in ast.walk(cancel_callback)
                      if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
    assert any(call_attr(node, "write") for node in callback_calls)
    assert any(call_attr(node, "flush") for node in callback_calls)

    adapter = ast.parse((ROOT / "source/persistent_planner_adapter_v2.py").read_text(
        encoding="utf-8"))
    interrupt_method = method(adapter, "PersistentPlannerAdapter", "interrupt")
    callback_call = next(node for node in ast.walk(interrupt_method)
                         if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                         and node.func.id == "before_transport")
    server_call = next(node for node in ast.walk(interrupt_method)
                       if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                       and node.func.attr == "interrupt_turn")
    assert callback_call.lineno < server_call.lineno

    client = ast.parse((ROOT / "source/codex_app_server_client_v2.py").read_text(
        encoding="utf-8"))
    request = method(client, "CodexAppServerClient", "request")
    assert ast.literal_eval(request.args.defaults[-1]) == 30

    result_path = ROOT / "RESULT.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    events = result["observed_events"]
    assert events.index("controller_cancel_write") < events.index("appserver_interrupt_request_written")
    assert events.index("controller_cancel_flush") < events.index("appserver_interrupt_request_written")
    assert events.index("input_released") < events.index("appserver_interrupt_response_injected")
    assert events.index("terminal") < events.index("appserver_interrupt_response_injected")
    release = result["verified_empty_release"]
    assert release == {"verified": True, "keys_down": [], "buttons_down": []}
    assert result["checks"]["exact_executor_v13_stack_hashes_checked"] == 9
    return {
        "status": "PASS_CURRENT_MAIN_CROSS_LAYER_ORDER_AUDIT",
        "current_main_commit": freeze["current_main_commit"],
        "current_source_files_verified": len(freeze["current_main_sources"]),
        "executor_stack_modules_verified": len(freeze["executor_stack_modules"]),
        "manifest_files_verified": len(manifest["files"]),
        "cancel_write_before_interrupt_request": True,
        "empty_terminal_before_interrupt_response": True,
        "interrupt_default_timeout_seconds": 30,
        "result_sha256": sha256(result_path),
    }


if __name__ == "__main__":
    result = audit()
    (ROOT / "AUDIT.json").write_text(json.dumps(result, indent=2) + "\n",
                                     encoding="utf-8")
    print(json.dumps(result, indent=2))
