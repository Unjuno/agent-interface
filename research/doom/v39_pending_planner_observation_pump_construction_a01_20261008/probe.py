"""Execute the frozen V39 pump/cancel source block with synthetic events."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import queue
import time
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPOSITORY = PACKAGE.parents[2]


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_probe(package: Path = PACKAGE) -> dict:
    freeze = _read_json(package / "FREEZE.json")
    source_path = REPOSITORY / freeze["controller_path"]
    source = source_path.read_bytes()
    source_sha = _sha(source)
    if source_sha != freeze["controller_sha256"]:
        raise ValueError("controller source hash mismatch")
    event_bytes = (package / "inputs/events.json").read_bytes()
    if _sha(event_bytes) != freeze["events_sha256"]:
        raise ValueError("synthetic event stream hash mismatch")
    event_rows = _read_json(package / "inputs/events.json")["rows"]
    if len(event_rows) != freeze["event_rows"] or len(event_rows) != 2:
        raise ValueError("synthetic event count mismatch")
    if any(row.get("synthetic") is not True for row in event_rows):
        raise ValueError("non-synthetic event supplied to construction probe")

    tree = ast.parse(source.decode("utf-8"), filename=str(source_path))
    main = next(node for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef) and node.name == "main")
    wait_node = next(node for node in ast.walk(main)
                     if isinstance(node, ast.FunctionDef) and node.name == "wait")
    pump_block = next(node for node in ast.walk(main)
                      if isinstance(node, ast.With) and any(
                          isinstance(item.context_expr, ast.Call) and
                          isinstance(item.context_expr.func, ast.Name) and
                          item.context_expr.func.id == "ThreadPoolExecutor"
                          for item in node.items))
    cancel_node = next(node for node in ast.walk(tree)
                       if isinstance(node, ast.FunctionDef) and
                       node.name == "cancel_invalidated_cover")

    trace = []

    class PendingFuture:
        def __init__(self):
            self.complete = False

        def done(self):
            trace.append({"event": "future_done_check", "done": self.complete})
            return self.complete

        def result(self):
            if not self.complete:
                raise AssertionError("synthetic planner future remained pending")
            return {"answer": "synthetic"}

    future = PendingFuture()

    class Planner:
        def __init__(self):
            self.await_body_calls = 0

        def await_turn(self, *_args):
            self.await_body_calls += 1
            raise AssertionError("fake pool must leave planner future pending")

        def interrupt(self, _handle, before_transport=None):
            trace.append({"event": "planner_interrupt_entered",
                          "future_pending": not future.complete})
            before_transport()
            trace.append({"event": "planner_interrupt_transport_sent"})
            future.complete = True
            return {"status": "interrupted"}

    planner = Planner()

    class FakeStdin:
        def __init__(self):
            self.writes = []

        def write(self, value):
            command = json.loads(value)
            self.writes.append(command)
            trace.append({"event": "executor_command_written", "command": command})

        def flush(self):
            pass

    class FakeProcess:
        def __init__(self):
            self.stdin = FakeStdin()

        def poll(self):
            return None

    process = FakeProcess()

    class SyntheticIncoming:
        def __init__(self, rows):
            self.rows = list(rows)

        def get(self, timeout=None):
            if not self.rows:
                raise queue.Empty
            row = self.rows.pop(0)
            trace.append({"event": "executor_event_dequeued", "row_event": row["event"]})
            return row

    class SyntheticMonitor:
        event_types = frozenset({"typed_observation"})

        def __init__(self):
            self.observed_while_pending = False

        def observe(self, row):
            if row.get("synthetic") is not True:
                raise ValueError("monitor received a non-synthetic observation")
            self.observed_while_pending = not future.done()
            trace.append({"event": "typed_observation_monitored",
                          "future_pending": self.observed_while_pending,
                          "sequence": row.get("sequence")})
            return {"event": "policy_invalidation",
                    "invalidation": {"reason": "synthetic_policy_invalidation",
                                     "sequence": row["sequence"]}}

    monitor = SyntheticMonitor()

    class FakePool:
        def __init__(self, max_workers):
            if max_workers != 1:
                raise AssertionError("unexpected planner worker count")

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def submit(self, function, *_args):
            if function != planner.await_turn:
                raise AssertionError("pending future is not planner.await_turn")
            # Deliberately do not execute the worker body. The fixture models a
            # still-pending turn until the invalidation interrupt completes.
            return future

    class FailureCleanup:
        def set_stage(self, stage):
            trace.append({"event": "cleanup_stage", "stage": stage})

    helper_namespace = {"json": json}
    helper_module = ast.fix_missing_locations(ast.Module(
        body=[cancel_node], type_ignores=[]))
    exec(compile(helper_module, str(source_path), "exec"), helper_namespace)

    result_names = ("current_terminal", "invalidation", "planner_interrupt",
                    "cover_terminals")
    body = [
        ast.Assign(targets=[ast.Name(id="latest", ctx=ast.Store())],
                   value=ast.Constant(value=None)),
        wait_node,
        pump_block,
        ast.Return(value=ast.Dict(
            keys=[ast.Constant(name) for name in result_names],
            values=[ast.Name(id=name, ctx=ast.Load()) for name in result_names])),
    ]
    pump_function = ast.FunctionDef(
        name="pump", args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[],
                                         kw_defaults=[], defaults=[]),
        body=body, decorator_list=[])
    pump_module = ast.fix_missing_locations(ast.Module(
        body=[pump_function], type_ignores=[]))
    namespace = {
        "queue": queue,
        "time": time,
        "json": json,
        "ThreadPoolExecutor": FakePool,
        "planner": planner,
        "planner_handle": object(),
        "process": process,
        "incoming": SyntheticIncoming(event_rows),
        "invalidation_monitor": monitor,
        "cover": "cover-0",
        "cover_ids": ["cover-0"],
        "cover_terminals": [],
        "cover_renewal_gaps_ms": [],
        "index": 0,
        "failure_cleanup": FailureCleanup(),
        "require_cover_terminal": lambda _row: None,
        "submit_cover": lambda _id: (_ for _ in ()).throw(
            AssertionError("unexpected cover renewal after invalidation")),
        "cancel_invalidated_cover": helper_namespace["cancel_invalidated_cover"],
        "TimeoutError": TimeoutError,
        "RuntimeError": RuntimeError,
    }
    exec(compile(pump_module, str(source_path), "exec"), namespace)
    pump_result = namespace["pump"]()
    terminal = pump_result["current_terminal"]
    cancel_command = process.stdin.writes[0] if process.stdin.writes else None
    renewals = max(0, len(namespace["cover_ids"]) - 1)
    result = {
        "status": "PASS_SYNTHETIC_PENDING_PUMP_RELEASE_ORDER",
        "schema": "v39-pending-pump-construction-result-v1",
        "main_commit": freeze["main_commit"],
        "controller_git_blob": freeze["controller_git_blob"],
        "controller_sha256": source_sha,
        "synthetic_event_stream_sha256": freeze["events_sha256"],
        "source_composition_executed": [
            "nested wait() event dispatcher",
            "pending planner ThreadPoolExecutor block",
            "cancel_invalidated_cover()",
        ],
        "observation_processed_while_planner_pending": monitor.observed_while_pending,
        "invalidation_reason": pump_result["invalidation"]["invalidation"]["reason"],
        "planner_interrupt_status": pump_result["planner_interrupt"]["status"],
        "cancel_command": cancel_command,
        "terminal_status": terminal.get("status"),
        "release": terminal.get("release"),
        "cover_renewals": renewals,
        "planner_worker_body_calls": planner.await_body_calls,
        "trace": trace,
        "scope": [
            "The production AST block ran with synthetic executor rows and a fake pending future.",
            "FakePool does not start a worker or run planner.await_turn; this is not a real concurrency or planner-latency test.",
            "No game, model, GUI, OS input, physical key state, useful feedback, recovery, or task effect was exercised.",
        ],
    }
    if (result["observation_processed_while_planner_pending"] is not True or
            cancel_command != {"op": "cancel", "id": "cover-0"} or
            terminal.get("status") != "cancelled" or
            terminal.get("release") != {"verified": True, "keys_down": [],
                                         "buttons_down": []} or
            renewals != 0 or planner.await_body_calls != 0):
        raise AssertionError("pending observation / cancellation construction gate failed")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=PACKAGE / "RESULT.json")
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"refusing to overwrite existing output: {args.output}")
    result = run_probe()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
