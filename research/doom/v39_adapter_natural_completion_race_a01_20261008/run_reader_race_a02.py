import ast
import collections
import hashlib
import json
import queue
import threading
import time
from pathlib import Path
from types import MethodType, SimpleNamespace

ROOT = Path(__file__).resolve().parent
FREEZE = json.loads((ROOT / "FREEZE_A02.json").read_text(encoding="utf-8"))
SOURCE = ROOT / "source"
CONTROLLER = (SOURCE / "controller_v39.py").read_text(encoding="utf-8")
ADAPTER = (SOURCE / "persistent_planner_adapter_v2.py").read_text(encoding="utf-8")
CLIENT_SOURCE = (SOURCE / "codex_app_server_client_v2.py").read_text(encoding="utf-8")
events = []
condition = threading.Condition()
terminal_rows = []

def mark(event):
    with condition:
        events.append({"event": event, "at_ns": time.perf_counter_ns()})
        condition.notify_all()

def wait_event(event, timeout=3):
    deadline = time.monotonic() + timeout
    with condition:
        while not any(row["event"] == event for row in events):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(event)
            condition.wait(remaining)

def extract_method(source, class_name, name, scope):
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    node = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)
    module = ast.Module(body=[node], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), name, "exec"), scope)
    return scope[name]

def extract_function(source, name, scope):
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    module = ast.Module(body=[node], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), name, "exec"), scope)
    return scope[name]

class JsonlStream:
    def __init__(self):
        self.lines = queue.Queue()
    def __iter__(self):
        return self
    def __next__(self):
        value = self.lines.get()
        if value is None:
            raise StopIteration
        return value
    def feed(self, message):
        self.lines.put(json.dumps(message, separators=(",", ":")) + "\n")
    def close(self):
        self.lines.put(None)

client_scope = {
    "json": json, "time": time, "threading": threading,
    "collections": collections, "math": __import__("math"),
    "AppServerError": RuntimeError,
}
deadline = extract_function(CLIENT_SOURCE, "_deadline", client_scope)
request = extract_method(CLIENT_SOURCE, "CodexAppServerClient", "request", client_scope)
read_loop = extract_method(CLIENT_SOURCE, "CodexAppServerClient", "_read", client_scope)
wait_notification = extract_method(CLIENT_SOURCE, "CodexAppServerClient", "wait_notification", client_scope)
wait_completed = extract_method(CLIENT_SOURCE, "CodexAppServerClient", "wait_turn_completed", client_scope)
latest_usage = extract_method(CLIENT_SOURCE, "CodexAppServerClient", "latest_turn_usage", client_scope)
interrupt_turn = extract_method(CLIENT_SOURCE, "CodexAppServerClient", "interrupt_turn", client_scope)

class Client:
    def __init__(self):
        self._condition = threading.Condition()
        self._journal_order_lock = threading.RLock()
        self._responses = {}
        self._pending = set()
        self._notifications = collections.deque()
        self._next_id = 1
        self._closed = False
        self.process = SimpleNamespace(stdout=JsonlStream())
        self._reader = threading.Thread(target=read_loop, args=(self,), daemon=True)
        self._reader.start()
    def _record(self, event, message):
        mark("client_" + event + "_" + str(message.get("method") or message.get("id")))
    def _write(self, message, *, deadline=None, request_id=None):
        with self._condition:
            self._pending.add(request_id)
        self.interrupt_id = request_id
        mark("interrupt_request_written")
        self.process.stdout.feed({
            "method": "turn/completed",
            "params": {
                "threadId": "thread", "turn": {
                    "id": "turn", "status": "completed",
                    "items": [{"type": "agentMessage", "text": "{\"action\":\"stale\"}"}],
                },
            },
        })
    def inject_interrupt_response(self):
        mark("interrupt_response_injected")
        self.process.stdout.feed({"id": self.interrupt_id, "result": {}})
    def stop_reader(self):
        self.process.stdout.close()
        self._reader.join(2)
        if self._reader.is_alive():
            raise AssertionError("exact stdout reader did not stop")

Client.request = request
Client.wait_notification = wait_notification
Client.wait_turn_completed = wait_completed
Client.latest_turn_usage = latest_usage
Client.interrupt_turn = interrupt_turn

def observed_wait_notification(self, predicate, timeout=120):
    row = wait_notification(self, predicate, timeout=timeout)
    if row.get("method") == "turn/completed":
        mark("turn_completion_consumed")
    return row
Client.wait_notification = observed_wait_notification

adapter_scope = {
    "threading": threading, "json": json, "PlannerProtocolError": RuntimeError,
    "TurnResult": lambda **kw: SimpleNamespace(**kw),
}
interrupt = extract_method(ADAPTER, "PersistentPlannerAdapter", "interrupt", adapter_scope)
await_turn = extract_method(ADAPTER, "PersistentPlannerAdapter", "await_turn", adapter_scope)
require_active = extract_method(ADAPTER, "PersistentPlannerAdapter", "_require_active", adapter_scope)
cancel_helper = extract_function(CONTROLLER, "cancel_invalidated_cover", {"json": json})

class CancelPipe:
    def write(self, value):
        row = json.loads(value)
        assert row == {"op": "cancel", "id": "cover"}
        mark("executor_cancel_write")
    def flush(self):
        mark("executor_cancel_flush")

class Process:
    stdin = CancelPipe()

handle = SimpleNamespace(thread_id="thread", turn_id="turn")
client = Client()
planner = SimpleNamespace(
    _lock=threading.RLock(), _active=handle, _terminal_status=None,
    _cancellation_requested=False, _interrupt_response=None, _transport_aborted=False,
    _output_schema={"type": "object"}, client=client,
)
planner.interrupt = MethodType(interrupt, planner)
planner.await_turn = MethodType(await_turn, planner)
planner._require_active = MethodType(require_active, planner)
helper_result = {}
helper_error = {}
answer_result = {}
answer_error = {}
def run_helper():
    try:
        helper_result["value"] = cancel_helper(planner, handle, Process(), wait_terminal, "cover")
    except BaseException as error:
        helper_error["value"] = error
def run_await():
    try:
        answer_result["value"] = planner.await_turn(handle, timeout=3)
        mark("planner_await_returned")
    except BaseException as error:
        answer_error["value"] = error

def wait_terminal(predicate):
    deadline_at = time.monotonic() + 3
    with condition:
        while True:
            for row in terminal_rows:
                if predicate(row):
                    mark("verified_empty_terminal_observed")
                    return row
            remaining = deadline_at - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("terminal")
            condition.wait(remaining)

helper_thread = threading.Thread(target=run_helper)
helper_thread.start()
wait_event("interrupt_request_written")
await_thread = threading.Thread(target=run_await)
await_thread.start()
wait_event("planner_await_returned")
answer = answer_result["value"]
response_still_pending = not any(row["event"] == "interrupt_response_injected" for row in events)
assert response_still_pending
assert helper_thread.is_alive()
assert answer.status == "completed"
assert answer.cancellation_requested is True
assert answer.answer_eligible is False
assert answer.answer is None
client.inject_interrupt_response()
terminal_rows.append({
    "event": "terminal", "id": "cover", "status": "cancelled",
    "release": {"verified": True, "keys_down": [], "buttons_down": []},
})
with condition:
    condition.notify_all()
helper_thread.join(2)
await_thread.join(2)
assert not helper_thread.is_alive()
assert not await_thread.is_alive()
assert "value" in helper_result and "value" not in helper_error, repr(helper_error)
assert "value" not in answer_error, repr(answer_error)
client.stop_reader()
assert helper_result["value"][1]["release"] == terminal_rows[0]["release"]
names = [row["event"] for row in events]
assert names.index("executor_cancel_flush") < names.index("interrupt_request_written")
assert names.index("client_received_turn/completed") < names.index("turn_completion_consumed")
assert names.index("turn_completion_consumed") < names.index("interrupt_response_injected")
assert names.index("interrupt_response_injected") < names.index("client_received_1")
result = {
    "schema": "v39-adapter-reader-completion-race-a02-v1",
    "status": "PASS_EXACT_READER_ROUTES_COMPLETION_BEFORE_INTERRUPT_REPLY",
    "main": FREEZE["main_commit"],
    "source_blobs": {row["path"]: row["git_blob"] for row in FREEZE["sources"]},
    "events": events,
    "completion_consumed_before_interrupt_response": response_still_pending,
    "turn_result": {
        "status": answer.status,
        "cancellation_requested": answer.cancellation_requested,
        "answer_eligible": answer.answer_eligible,
        "answer": answer.answer,
        "error": answer.error,
    },
    "helper_terminal": {
        "status": helper_result["value"][1]["status"],
        "release": helper_result["value"][1]["release"],
    },
}
out = ROOT / "RESULT_A02.json"
with out.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(result, stream, indent=2)
    stream.write("\n")
print(json.dumps(result, indent=2))
