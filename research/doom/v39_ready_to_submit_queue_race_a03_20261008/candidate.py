"""Exercise the frozen V39 wait helper at the acceptance boundary."""
import ast
import hashlib
import json
import queue
import subprocess
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def repo_root():
    for parent in HERE.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("repository root not found")


def pinned_source():
    spec = FREEZE["source"]
    root = repo_root()
    data = subprocess.check_output(["git", "-C", str(root), "show",
                                    f"{FREEZE['main_commit']}:{spec['path']}"])
    blob = subprocess.check_output(["git", "-C", str(root), "rev-parse",
                                    f"{FREEZE['main_commit']}:{spec['path']}"],
                                   text=True).strip()
    if blob != spec["git_blob"] or hashlib.sha256(data).hexdigest() != spec["sha256"]:
        raise ValueError("frozen V39 source identity mismatch")
    return data


def source_anchors(source):
    tree = ast.parse(source, filename=FREEZE["source"]["path"])
    main = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "main")
    readiness = next(node for node in ast.walk(main)
                     if isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                     and "READY_FOR_FRESH_EXECUTOR_ADMISSION" in ast.unparse(node.test)
                     and "final_action_admission" in ast.unparse(node.test))
    execute = next(node for node in ast.walk(main)
                   if isinstance(node, ast.FunctionDef) and node.name == "execute_segment")
    calls = []
    submit_line = None
    for index, node in enumerate(execute.body):
        if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and
                isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "write" and
                ast.unparse(node.value.func.value) == "process.stdin"):
            submit_line = node.lineno
        if isinstance(node, ast.Assign):
            wait_calls = [call for call in ast.walk(node.value)
                          if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                          and call.func.id == "wait"]
            for call in wait_calls:
                calls.append((index, node, call))
    after = [(i, node, call) for i, node, call in calls if node.lineno > submit_line]
    ack = next(row for row in after if "accepted" in ast.unparse(row[1].targets[0]))
    terminal = next(row for row in after if "boundary" in ast.unparse(row[1].targets[0]))
    ack_keywords = {keyword.arg for keyword in ack[2].keywords}
    terminal_keywords = {keyword.arg for keyword in terminal[2].keywords}
    if "observation_monitor" in ack_keywords:
        raise ValueError("acceptance wait unexpectedly has an observation monitor")
    if "observation_monitor" not in terminal_keywords or "action_monitor" not in ast.unparse(terminal[2]):
        raise ValueError("later terminal wait is not bound to action monitor")
    call_segment = next(node for node in ast.walk(main)
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id == "execute_segment")
    if readiness.lineno >= call_segment.lineno:
        raise ValueError("readiness check does not precede segment submission")
    wait_def = next(node for node in ast.walk(main)
                    if isinstance(node, ast.FunctionDef) and node.name == "wait")
    return {"readiness_line": readiness.lineno, "submit_write_line": submit_line,
            "ack_wait_line": ack[1].lineno, "later_monitored_wait_line": terminal[1].lineno,
            "production_wait": wait_def}


class RecordingQueue(queue.Queue):
    def __init__(self, events):
        super().__init__()
        self.events = events

    def get(self, *args, **kwargs):
        row = super().get(*args, **kwargs)
        self.events.append({"event": "production_wait_dequeued", "row_event": row["event"],
                            "sequence": row.get("sequence")})
        return row


class FakeProcess:
    def poll(self):
        return None


def build_exact_wait(wait_def, incoming, process):
    holder = ast.FunctionDef(
        name="holder",
        args=ast.arguments(posonlyargs=[], args=[ast.arg(arg="incoming"), ast.arg(arg="process"),
                                                ast.arg(arg="time")], vararg=None,
                           kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
        body=[ast.Assign(targets=[ast.Name(id="latest", ctx=ast.Store())],
                         value=ast.Constant(value=None)),
              wait_def,
              ast.Return(value=ast.Tuple(elts=[ast.Name(id="wait", ctx=ast.Load()),
                                               ast.Lambda(args=ast.arguments(posonlyargs=[], args=[],
                                                   vararg=None, kwonlyargs=[], kw_defaults=[],
                                                   kwarg=None, defaults=[]),
                                                   body=ast.Name(id="latest", ctx=ast.Load()))],
                                        ctx=ast.Load()))],
        decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=[holder], type_ignores=[]))
    namespace = {"queue": queue}
    exec(compile(module, "<frozen-production-wait>", "exec"), namespace)
    return namespace["holder"](incoming, process, time)


def run_once():
    anchors = source_anchors(pinned_source())
    events = [{"event": "action_readiness", "status": "READY_FOR_FRESH_EXECUTOR_ADMISSION",
               "source_sequence": 1, "source_health": 100},
              {"event": "typed_observation_queued", "sequence": 2, "health": 70,
               "hard_minimum": 80},
              {"event": "submit_written", "expected_sequence": 1, "input_emission": "NOT_MODELED"}]
    incoming = RecordingQueue(events)
    incoming.put({"event": "typed_observation", "sequence": 2,
                  "signals": {"health": {"value": 70}}})
    incoming.put({"event": "accepted", "id": "action-0", "accepted_ns": 1})
    wait, read_latest = build_exact_wait(anchors["production_wait"], incoming, FakeProcess())
    monitor_calls = []
    accepted = wait(lambda row: row["event"] in ("accepted", "rejected"), timeout=1)
    events.append({"event": "acceptance_returned", "id": accepted["id"]})
    events.append({"event": "monitor_call_count_after_ack", "count": len(monitor_calls)})
    events.append({"event": "queued_rows_after_ack", "count": incoming.qsize()})
    events.append({"event": "legacy_latest_after_ack", "value": read_latest()})
    return {"schema": "issue59-v39-ready-submit-result-a03",
            "status": "SYNTHETIC_PRODUCTION_WAIT_TRACE",
            "frozen_main": FREEZE["main_commit"],
            "anchors": {key: value for key, value in anchors.items() if key != "production_wait"},
            "events": events,
            "scope": "Exact frozen wait helper and AST caller anchors with fake queue/process; no executor binary, acceptance by a real executor, input, GUI, game, or OS behavior."}


def main():
    result_path = HERE / "RESULT.json"
    events_path = HERE / "events.jsonl"
    if result_path.exists() or events_path.exists():
        raise FileExistsError("refusing to overwrite retained candidate output")
    result = run_once()
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8",
                           newline="\n")
    events_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n"
                                   for row in result["events"]),
                           encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], "event_count": len(result["events"])},
                     separators=(",", ":")))


if __name__ == "__main__":
    main()
