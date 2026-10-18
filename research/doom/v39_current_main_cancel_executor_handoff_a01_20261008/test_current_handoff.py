"""Exercise the current-main cancel helper with the retained ExecutorV13 stack."""
import ast
import copy
import hashlib
import importlib
import importlib.util
import json
import math
import sys
import threading
import tempfile
import time
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).parent
SOURCE = ROOT / "source"
CONTROLLER = SOURCE / "controller_v39.py"
ADAPTER = SOURCE / "persistent_planner_adapter_v2.py"
CLIENT = SOURCE / "codex_app_server_client_v2.py"
HANDOFF_HARNESS = SOURCE / "prior_handoff_harness.py"
EXECUTOR_STACK = SOURCE / "executor_v13_stack"
EXECUTOR_BLOBS = {
    "lease.py": "b9dac6bb4063928354733d79bf371909a288a3d1",
    "lease_cause_v1.py": "310a3b0ee8f0cca050cc55cadcb635cee2cbc474",
    "lease_cause_v2.py": "7428e22919b019a62fa80f2162ce5c0bc1d9231b",
    "lease_release_v1.py": "e325bd358874ae003e066f5d592c045b0ebef56e",
    "executor_v3.py": "2b072454fd81c41bf9e025217afc78020c7059de",
    "executor_v5.py": "742f7a5368b0bf6c202fdbe0856494abb5795dce",
    "executor_v11.py": "8dc84dc83bd3bb17ec5354d768383738e683d9d4",
    "executor_v12.py": "7e9bb6286d5f674108688ba092300a8ad2421ba9",
    "executor_v13.py": "9eb5ed4dcd42cae07bea69530136f78f9e65fb33",
}


def load_frozen_handoff_harness():
    import_name = (
        "research.doom.v39_cancel_before_interrupt_ack_a01_20261008.test_order")
    placeholder = ModuleType(import_name)
    for name in ("load_cancel_first_counterfactual", "load_class_method",
                 "load_exact_cancel_helper", "load_exact_client_request"):
        setattr(placeholder, name, lambda *args, **kwargs: None)
    previous = sys.modules.get(import_name)
    sys.modules[import_name] = placeholder
    spec = importlib.util.spec_from_file_location("frozen_prior_handoff_harness",
                                                  HANDOFF_HARNESS)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    finally:
        if previous is None:
            sys.modules.pop(import_name, None)
        else:
            sys.modules[import_name] = previous
    return module


retained_handoff = load_frozen_handoff_harness()


def module_source(path):
    return path.read_text(encoding="utf-8")


def top_function(path, name, namespace):
    tree = ast.parse(module_source(path))
    node = copy.deepcopy(next(item for item in tree.body
                              if isinstance(item, ast.FunctionDef) and item.name == name))
    module = ast.Module(body=[node], type_ignores=[])
    scope = dict(namespace)
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), scope)
    return scope[name]


def class_method(path, class_name, method_name, namespace=None):
    tree = ast.parse(module_source(path))
    cls = next(item for item in ast.walk(tree)
               if isinstance(item, ast.ClassDef) and item.name == class_name)
    node = copy.deepcopy(next(item for item in cls.body
                              if isinstance(item, ast.FunctionDef) and
                              item.name == method_name))
    module = ast.Module(body=[node], type_ignores=[])
    scope = {} if namespace is None else dict(namespace)
    exec(compile(ast.fix_missing_locations(module),
                 f"{path}#{class_name}.{method_name}", "exec"), scope)
    return scope[method_name]


def exact_cancel_helper():
    return top_function(CONTROLLER, "cancel_invalidated_cover", {"json": json})


def exact_client_request():
    tree = ast.parse(module_source(CLIENT))
    names = {node.name: node for node in ast.walk(tree)
             if isinstance(node, ast.FunctionDef)}
    nodes = [copy.deepcopy(names["_deadline"]), copy.deepcopy(names["request"])]
    module = ast.Module(body=nodes, type_ignores=[])
    scope = {"json": json, "time": time, "threading": threading, "math": math,
             "AppServerError": RuntimeError}
    exec(compile(ast.fix_missing_locations(module), f"{CLIENT}#request", "exec"), scope)
    return scope["request"]


def exact_source_method(path, class_name, method_name):
    if path.endswith("map01_overlap_controller_v39.py"):
        source_path = CONTROLLER
    elif path.endswith("persistent_planner_adapter_v2.py"):
        source_path = ADAPTER
    elif path.endswith("codex_app_server_client_v2.py"):
        source_path = CLIENT
    else:
        raise AssertionError(f"unexpected source path: {path}")
    return class_method(source_path, class_name, method_name)


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def load_pinned_executor_stack(self, temp):
    root = Path(temp)
    for name in retained_handoff.MODULES:
        data = (EXECUTOR_STACK / name).read_bytes()
        if git_blob_sha(data) != EXECUTOR_BLOBS[name]:
            raise AssertionError(f"frozen ExecutorV13 source identity mismatch: {name}")
        (root / name).write_bytes(data)
    sys.path.insert(0, str(root))
    for name in (Path(file).stem for file in retained_handoff.MODULES):
        sys.modules.pop(name, None)
    return importlib.import_module("executor_v13"), importlib.import_module("executor_v3")


def run_replay():
    """Withhold the real adapter request response until ExecutorV13 is released."""
    retained_handoff.source_method = exact_source_method
    retained_handoff.load_exact_client_request = exact_client_request
    retained_handoff.CrossLayerHandoffTests._load_executor_v13 = load_pinned_executor_stack

    captured = {"journal": None}
    original_journal = retained_handoff.EventJournal

    class CapturedEventJournal(original_journal):
        def __init__(self):
            super().__init__()
            captured["journal"] = self

    retained_handoff.EventJournal = CapturedEventJournal
    original_inject = retained_handoff.AppServerProbe.inject_response

    def inject_only_after_verified_executor_terminal(client):
        client.journal.wait_mark("terminal")
        original_inject(client)

    retained_handoff.AppServerProbe.inject_response = inject_only_after_verified_executor_terminal
    try:
        helper = exact_cancel_helper()
        with tempfile.TemporaryDirectory(prefix="v39-current-handoff-") as temp:
            trace = retained_handoff.CrossLayerHandoffTests()._run_order(
                helper, temp, cancel_first=True)
    finally:
        retained_handoff.AppServerProbe.inject_response = original_inject
        retained_handoff.EventJournal = original_journal
    journal = captured["journal"]
    terminal_rows = [row for _stamp, row in journal.rows
                     if row.get("event") == "terminal"]
    assert len(terminal_rows) == 1
    release_receipt = terminal_rows[0].get("release")
    assert type(release_receipt) is dict
    assert release_receipt.get("verified") is True
    assert release_receipt.get("keys_down") == []
    assert release_receipt.get("buttons_down") == []
    trace = [row["event"] for row in journal.trace]
    cancel_write = trace.index("controller_cancel_write")
    cancel_flush = trace.index("controller_cancel_flush")
    request_write = trace.index("appserver_interrupt_request_written")
    release = trace.index("input_released")
    terminal = trace.index("terminal")
    response = trace.index("appserver_interrupt_response_injected")
    assert cancel_write < cancel_flush < request_write
    assert release < terminal < response
    return {"events": trace, "verified_empty_release": release_receipt}


class CurrentMainCancelHandoffTests(unittest.TestCase):
    def test_current_main_helper_releases_executor_before_interrupt_response(self):
        replay = run_replay()
        trace = replay["events"]
        self.assertLess(trace.index("controller_cancel_write"),
                        trace.index("appserver_interrupt_request_written"))
        self.assertLess(trace.index("input_released"),
                        trace.index("appserver_interrupt_response_injected"))
        self.assertLess(trace.index("terminal"),
                        trace.index("appserver_interrupt_response_injected"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
