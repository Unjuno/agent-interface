"""AST-isolated ordering test over the exact current-main V39 cancel helper."""
import ast
import copy
import json
import math
import subprocess
import threading
import time
from types import MethodType, SimpleNamespace
import unittest

CONTROLLER = "research/doom/map01_overlap_controller_v39.py"
ADAPTER = "research/live_control/persistent_planner_adapter_v2.py"
CLIENT = "research/live_control/codex_app_server_client_v2.py"
SOURCE_REF = "708ca59a8128f07fdb7e13a36704c6b2f79c9fb6"


def source_at_head(path):
    return subprocess.check_output(["git", "show", f"{SOURCE_REF}:{path}"], text=True)


def function_node(source, name):
    tree = ast.parse(source)
    return next(node for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == name)


def load_exact_cancel_helper():
    source = source_at_head(CONTROLLER)
    node = copy.deepcopy(function_node(source, "cancel_invalidated_cover"))
    module = ast.Module(body=[node], type_ignores=[])
    namespace = {"json": json}
    exec(compile(ast.fix_missing_locations(module), CONTROLLER, "exec"), namespace)
    return namespace["cancel_invalidated_cover"]


def load_cancel_first_counterfactual():
    """Move only the exact interrupt assignment after cancel write + flush."""
    source = source_at_head(CONTROLLER)
    node = copy.deepcopy(function_node(source, "cancel_invalidated_cover"))
    interrupt = next(n for n in node.body
                     if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)
                     and isinstance(n.value.func, ast.Attribute)
                     and n.value.func.attr == "interrupt")
    node.body.remove(interrupt)
    flush_index = next(i for i, n in enumerate(node.body)
                       if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                       and isinstance(n.value.func, ast.Attribute)
                       and n.value.func.attr == "flush")
    node.body.insert(flush_index + 1, interrupt)
    module = ast.Module(body=[node], type_ignores=[])
    namespace = {"json": json}
    exec(compile(ast.fix_missing_locations(module), CONTROLLER + "#cancel-first-counterfactual",
                 "exec"), namespace)
    return namespace["cancel_invalidated_cover"]


def load_exact_client_request():
    source = source_at_head(CLIENT)
    tree = ast.parse(source)
    deadline = copy.deepcopy(next(n for n in ast.walk(tree)
                                  if isinstance(n, ast.FunctionDef)
                                  and n.name == "_deadline"))
    node = copy.deepcopy(next(n for n in ast.walk(tree)
                              if isinstance(n, ast.FunctionDef) and n.name == "request"))
    module = ast.Module(body=[deadline, node], type_ignores=[])
    namespace = {"json": json, "time": time, "threading": threading, "math": math,
                 "AppServerError": RuntimeError}
    exec(compile(ast.fix_missing_locations(module), CLIENT, "exec"), namespace)
    return namespace["request"]


def load_class_method(path, class_name, method_name, namespace=None):
    source = source_at_head(path)
    tree = ast.parse(source)
    cls = next(n for n in ast.walk(tree)
               if isinstance(n, ast.ClassDef) and n.name == class_name)
    node = copy.deepcopy(next(n for n in cls.body
                              if isinstance(n, ast.FunctionDef) and n.name == method_name))
    module = ast.Module(body=[node], type_ignores=[])
    globals_ = {} if namespace is None else dict(namespace)
    exec(compile(ast.fix_missing_locations(module), f"{path}#{class_name}.{method_name}",
                 "exec"), globals_)
    return globals_[method_name]


class DelayedPlanner:
    def __init__(self, events):
        self.events = events
        self.entered = threading.Event()
        self.respond = threading.Event()
        self.finished = threading.Event()

    def interrupt(self, _handle):
        self.events.append(("planner_interrupt_enter", time.monotonic_ns()))
        self.entered.set()
        if not self.respond.wait(2):
            raise TimeoutError("test did not release delayed planner response")
        self.finished.set()
        self.events.append(("planner_interrupt_return", time.monotonic_ns()))
        return {"outcome": "requested", "response": {}}


class CaptureStdin:
    def __init__(self, events):
        self.events = events
        self.writes = []

    def write(self, value):
        self.writes.append(value)
        self.events.append(("cancel_write", time.monotonic_ns()))

    def flush(self):
        self.events.append(("cancel_flush", time.monotonic_ns()))


class Process:
    def __init__(self, events):
        self.stdin = CaptureStdin(events)


class CancellationOrderingTests(unittest.TestCase):
    def test_current_helper_waits_for_interrupt_response_before_cancel_write(self):
        helper = load_exact_cancel_helper()
        events = []
        planner = DelayedPlanner(events)
        process = Process(events)
        result = {}

        def wait(predicate):
            row = {"event": "terminal", "id": "cover-7", "status": "cancelled",
                   "release": {"verified": True, "buttons_down": [], "keys_down": []}}
            if not predicate(row):
                raise AssertionError("unexpected wait predicate")
            events.append(("terminal", time.monotonic_ns()))
            return row

        thread = threading.Thread(target=lambda: result.setdefault(
            "value", helper(planner, "turn-7", process, wait, "cover-7")))
        thread.start()
        self.assertTrue(planner.entered.wait(1), "planner interrupt was not entered")
        time.sleep(0.05)
        self.assertFalse(planner.finished.is_set())
        self.assertEqual(process.stdin.writes, [],
                         "current source unexpectedly sent cancel before interrupt response")
        planner.respond.set()
        thread.join(1)
        self.assertFalse(thread.is_alive(), "cancel helper did not finish")
        self.assertTrue(planner.finished.is_set())
        self.assertEqual(json.loads(process.stdin.writes[0]),
                         {"op": "cancel", "id": "cover-7"})
        self.assertEqual([name for name, _ in events],
                         ["planner_interrupt_enter", "planner_interrupt_return",
                          "cancel_write", "cancel_flush", "terminal"])
        self.assertIsNotNone(result["value"][0])

    def test_cancel_first_counterfactual_emits_cancel_before_interrupt_wait(self):
        helper = load_cancel_first_counterfactual()
        events = []
        planner = DelayedPlanner(events)
        process = Process(events)

        def wait(predicate):
            row = {"event": "terminal", "id": "cover-8", "status": "cancelled",
                   "release": {"verified": True, "buttons_down": [], "keys_down": []}}
            self.assertTrue(predicate(row))
            events.append(("terminal", time.monotonic_ns()))
            return row

        outcome = {}
        thread = threading.Thread(target=lambda: outcome.setdefault(
            "value", helper(planner, "turn-8", process, wait, "cover-8")))
        thread.start()
        self.assertTrue(planner.entered.wait(1), "counterfactual interrupt was not entered")
        names = [name for name, _ in events]
        self.assertEqual(names[:3], ["cancel_write", "cancel_flush", "planner_interrupt_enter"])
        self.assertEqual(json.loads(process.stdin.writes[0]),
                         {"op": "cancel", "id": "cover-8"})
        planner.respond.set()
        thread.join(1)
        self.assertFalse(thread.is_alive(), "counterfactual helper did not finish")
        self.assertIn("value", outcome)

    def test_source_contract_has_response_wait_and_30s_default(self):
        client = ast.parse(source_at_head(CLIENT))
        request = next(node for node in ast.walk(client)
                       if isinstance(node, ast.FunctionDef) and node.name == "request")
        self.assertEqual(ast.literal_eval(request.args.defaults[-1]), 30)
        has_condition_wait = any(isinstance(node, ast.Call) and
                                 isinstance(node.func, ast.Attribute) and
                                 node.func.attr == "wait"
                                 for node in ast.walk(request))
        self.assertTrue(has_condition_wait)

    def test_exact_client_request_times_out_when_interrupt_response_is_missing(self):
        request = load_exact_client_request()

        class ClientProbe:
            def __init__(self):
                self._condition = threading.Condition()
                self._next_id = 1
                self._responses = {}
                self._pending = set()
                self._closed = False
                self.sent = []

            def _write(self, message, deadline=None, request_id=None):
                self.sent.append((message, request_id))
                self._pending.add(request_id)

        client = ClientProbe()
        with self.assertRaisesRegex(TimeoutError, "turn/interrupt"):
            request(client, "turn/interrupt", {"threadId": "t", "turnId": "u"},
                    timeout=0.05)
        self.assertEqual(len(client.sent), 1)
        self.assertEqual(client.sent[0][0]["method"], "turn/interrupt")
        self.assertFalse(client._pending)

    def test_composed_v39_adapter_and_client_wait_before_executor_cancel(self):
        events = []
        helper = load_exact_cancel_helper()
        client_request = load_exact_client_request()
        client_interrupt = load_class_method(
            CLIENT, "CodexAppServerClient", "interrupt_turn")
        planner_interrupt = load_class_method(
            "research/live_control/persistent_planner_adapter_v2.py",
            "PersistentPlannerAdapter", "interrupt")

        class AppServerProbe:
            def __init__(self):
                self._condition = threading.Condition()
                self._next_id = 1
                self._responses = {}
                self._pending = set()
                self._closed = False

            def _write(self, message, deadline=None, request_id=None):
                events.append(("appserver_request_written", time.monotonic_ns()))
                self._pending.add(request_id)

        app = AppServerProbe()

        def bounded_request(self, method, params=None, timeout=30):
            try:
                return client_request(self, method, params, timeout=0.05)
            finally:
                events.append(("appserver_request_returned", time.monotonic_ns()))

        app.request = MethodType(bounded_request, app)
        app.interrupt_turn = MethodType(client_interrupt, app)
        handle = SimpleNamespace(thread_id="t", turn_id="u")
        require_active = load_class_method(
            "research/live_control/persistent_planner_adapter_v2.py",
            "PersistentPlannerAdapter", "_require_active")
        planner = SimpleNamespace(
            _lock=threading.RLock(), _terminal_status=None,
            _cancellation_requested=False, _interrupt_response=None,
            _active=handle, client=app)
        planner._require_active = MethodType(require_active, planner)
        planner.interrupt = MethodType(planner_interrupt, planner)
        process = Process(events)

        def wait(predicate):
            row = {"event": "terminal", "id": "cover-composed", "status": "cancelled",
                   "release": {"verified": True, "buttons_down": [], "keys_down": []}}
            self.assertTrue(predicate(row))
            events.append(("terminal", time.monotonic_ns()))
            return row

        result = helper(planner, handle, process, wait, "cover-composed")
        names = [name for name, _ in events]
        self.assertEqual(names, ["appserver_request_written", "appserver_request_returned",
                                 "cancel_write", "cancel_flush", "terminal"])
        self.assertEqual(json.loads(process.stdin.writes[0]),
                         {"op": "cancel", "id": "cover-composed"})
        self.assertEqual(result[0]["outcome"], "request_error")
        self.assertTrue(planner._cancellation_requested)
        self.assertFalse(app._pending)


if __name__ == "__main__":
    unittest.main(verbosity=2)
