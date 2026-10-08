"""Cross-layer cancellation-order test using exact V39 and ExecutorV13 code."""
import importlib
import json
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from types import MethodType, SimpleNamespace
import unittest

from research.doom.v39_cancel_before_interrupt_ack_a01_20261008.test_order import (
    load_cancel_first_counterfactual,
    load_class_method,
    load_exact_cancel_helper,
    load_exact_client_request,
)

MAIN = "708ca59a8128f07fdb7e13a36704c6b2f79c9fb6"
MODULES = (
    "lease.py", "lease_cause_v1.py", "lease_cause_v2.py", "lease_release_v1.py",
    "executor_v3.py", "executor_v5.py", "executor_v11.py", "executor_v12.py",
    "executor_v13.py",
)
MODULE_BLOBS = {
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
LIVE_CONTROL = "research/live_control"
PLANNER = "research/live_control/persistent_planner_adapter_v2.py"
CLIENT = "research/live_control/codex_app_server_client_v2.py"


def show(path):
    return subprocess.check_output(["git", "show", f"{MAIN}:{path}"])


def source_method(path, class_name, method_name):
    method = load_class_method(path, class_name, method_name)
    return method


class EventJournal:
    def __init__(self):
        self.condition = threading.Condition()
        self.rows = []
        self.trace = []

    def mark(self, event, row=None):
        stamp = time.perf_counter_ns()
        with self.condition:
            self.trace.append({"event": event, "at_ns": stamp})
            if row is not None:
                self.rows.append((stamp, row))
            self.condition.notify_all()

    def wait_row(self, predicate, timeout=2):
        deadline = time.monotonic() + timeout
        cursor = 0
        with self.condition:
            while True:
                while cursor < len(self.rows):
                    _stamp, row = self.rows[cursor]
                    cursor += 1
                    if predicate(row):
                        return row
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("event wait expired")
                self.condition.wait(remaining)

    def has(self, event):
        with self.condition:
            return any(item["event"] == event for item in self.trace)

    def wait_mark(self, event, timeout=2):
        deadline = time.monotonic() + timeout
        with self.condition:
            while not self.has(event):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"event not observed: {event}")
                self.condition.wait(remaining)


class EventBackend:
    def __init__(self):
        self.sequence = 0
        self.lease = None
        self.held = {"space"}

    def validate(self, _steps):
        return None

    def execute(self, _step, lease, _identifier, _index):
        if not lease.cancel.wait(2):
            raise TimeoutError("executor never received cancel")
        from executor_v3 import Cancelled
        raise Cancelled()

    def release_all(self):
        # Simulated owner confirmation: software input state is cleared before
        # the exact ExecutorV13 release receipt is generated.
        self.held.clear()
        record = {"event": "owner_release", "reason": "cancelled", "verified": True,
                  "keys_down": [], "buttons_down": [], "keys_unknown": [],
                  "key_state_errors": [], "verified_ns": time.perf_counter_ns()}
        self.lease.record_interruption(record)
        return {"verified": not self.held, "keys_down": [], "buttons_down": []}


class AppServerProbe:
    def __init__(self, journal):
        self.journal = journal
        self._condition = threading.Condition()
        self._next_id = 1
        self._responses = {}
        self._pending = set()
        self._closed = False
        self._request_id = None

    def _write(self, message, deadline=None, request_id=None):
        self._request_id = request_id
        self._pending.add(request_id)
        self.journal.mark("appserver_interrupt_request_written")

    def inject_response(self):
        self.journal.mark("appserver_interrupt_response_injected")
        with self._condition:
            self._responses[self._request_id] = {"result": {}}
            self._condition.notify_all()


class CancelPipe:
    def __init__(self, journal, executor):
        self.journal = journal
        self.executor = executor
        self.writes = []

    def write(self, line):
        self.writes.append(line)
        row = json.loads(line)
        if row.get("op") == "cancel":
            self.journal.mark("controller_cancel_write")
            self.executor.cancel(row["id"])
        else:
            raise AssertionError(f"unexpected executor command: {row}")

    def flush(self):
        self.journal.mark("controller_cancel_flush")


class Process:
    def __init__(self, journal, executor):
        self.stdin = CancelPipe(journal, executor)


class CrossLayerHandoffTests(unittest.TestCase):
    def _load_executor_v13(self, temp):
        root = Path(temp)
        for name in MODULES:
            path = f"{LIVE_CONTROL}/{name}"
            actual = subprocess.check_output(
                ["git", "rev-parse", f"{MAIN}:{path}"], text=True).strip()
            if actual != MODULE_BLOBS[name]:
                raise AssertionError(f"source blob changed for {path}: {actual}")
            (root / name).write_bytes(show(path))
        sys.path.insert(0, str(root))
        for name in (Path(file).stem for file in MODULES):
            sys.modules.pop(name, None)
        return importlib.import_module("executor_v13"), importlib.import_module("executor_v3")

    def _run_order(self, helper, temp, *, cancel_first):
        executor_module, v3 = self._load_executor_v13(temp)
        journal = EventJournal()
        backend = EventBackend()

        def emit(row):
            journal.mark(row["event"], row)

        executor = executor_module.Executor(backend, emit)
        executor.submit("cover-live-order", [{"op": "hold", "keys": ["space"],
                                              "duration_ms": 5000}],
                        expected_sequence=0,
                        valid_until_ns=time.perf_counter_ns() + 10_000_000_000)
        journal.wait_mark("step_started", timeout=1)

        client = AppServerProbe(journal)
        request = load_exact_client_request()
        interrupt_turn = source_method(CLIENT, "CodexAppServerClient", "interrupt_turn")
        planner_interrupt = source_method(
            PLANNER, "PersistentPlannerAdapter", "interrupt")

        def bounded_request(self, method, params=None, timeout=30):
            # Only timeout is injected; wait/response logic is the frozen method.
            return request(self, method, params, timeout=1.0)

        client.request = MethodType(bounded_request, client)
        client.interrupt_turn = MethodType(interrupt_turn, client)
        handle = SimpleNamespace(thread_id="thread", turn_id="turn")
        require_active = source_method(
            PLANNER, "PersistentPlannerAdapter", "_require_active")
        planner = SimpleNamespace(
            _lock=threading.RLock(), _terminal_status=None,
            _cancellation_requested=False, _interrupt_response=None,
            _active=handle, client=client)
        planner._require_active = MethodType(require_active, planner)
        planner.interrupt = MethodType(planner_interrupt, planner)
        process = Process(journal, executor)
        helper_result = {}
        helper_error = {}

        def run_helper():
            try:
                helper_result["value"] = helper(
                    planner, handle, process, journal.wait_row, "cover-live-order")
            except BaseException as error:
                helper_error["value"] = error

        thread = threading.Thread(target=run_helper)
        thread.start()

        if not cancel_first:
            try:
                journal.wait_mark("appserver_interrupt_request_written")
            except TimeoutError as error:
                thread.join(0.1)
                raise AssertionError(
                    f"planner path exited before request: {helper_error!r}; "
                    f"helper_alive={thread.is_alive()}; trace={journal.trace!r}; "
                    f"executor_active={executor.active!r}; lease_cancel="
                    f"{None if backend.lease is None else backend.lease.cancel.is_set()}") from error
            self.assertFalse(journal.has("controller_cancel_write"))
            self.assertFalse(journal.has("input_released"))
            client.inject_response()
        else:
            journal.wait_mark("controller_cancel_write")
            journal.wait_mark("appserver_interrupt_request_written")
            journal.wait_mark("input_released")
            self.assertFalse(journal.has("appserver_interrupt_response_injected"))
            self.assertEqual(backend.held, set())
            client.inject_response()

        thread.join(2)
        self.assertFalse(thread.is_alive(), "V39 helper did not finish")
        self.assertNotIn("value", helper_error, repr(helper_error.get("value")))
        self.assertTrue(journal.has("terminal"))
        self.assertEqual(backend.held, set())
        self.assertEqual(helper_result["value"][1]["release"]["keys_down"], [])
        executor.close()
        trace = [row["event"] for row in journal.trace]
        for name in (Path(file).stem for file in MODULES):
            sys.modules.pop(name, None)
        sys.path.remove(str(Path(temp)))
        return trace

    def test_exact_executor_release_can_precede_delayed_interrupt_response_only_after_early_cancel(self):
        with tempfile.TemporaryDirectory() as current_temp, tempfile.TemporaryDirectory() as candidate_temp:
            current = self._run_order(load_exact_cancel_helper(), current_temp,
                                       cancel_first=False)
            candidate = self._run_order(load_cancel_first_counterfactual(), candidate_temp,
                                        cancel_first=True)
        self.assertLess(current.index("appserver_interrupt_response_injected"),
                        current.index("controller_cancel_write"))
        self.assertLess(current.index("controller_cancel_write"),
                        current.index("input_released"))
        self.assertLess(candidate.index("controller_cancel_write"),
                        candidate.index("input_released"))
        self.assertLess(candidate.index("input_released"),
                        candidate.index("appserver_interrupt_response_injected"))
        print(json.dumps({"current": current, "cancel_first_counterfactual": candidate},
                         separators=(",", ":")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
