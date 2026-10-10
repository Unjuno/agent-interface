"""Run frozen session emit and V39 reader/wait across a real child stdout pipe."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
from types import SimpleNamespace


HERE = Path(__file__).resolve().parent
DEFAULT_REPO = HERE.parents[2]
SESSION_PATH = "research/doom/session_map01_v12.py"
CONTROLLER_PATH = "research/doom/map01_overlap_controller_v39.py"


class NonlocalToGlobal(ast.NodeTransformer):
    def visit_Nonlocal(self, node: ast.Nonlocal) -> ast.Global:
        return ast.Global(names=node.names)


def function_node(source: bytes, name: str) -> ast.FunctionDef:
    parsed = ast.parse(source)
    found = [node for node in ast.walk(parsed)
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    if len(found) != 1 or not isinstance(found[0], ast.FunctionDef):
        raise RuntimeError(f"expected one synchronous {name} function, found {len(found)}")
    return NonlocalToGlobal().visit(found[0])


def git_blob(repo: Path, tree: str, path: str) -> bytes:
    return subprocess.check_output(
        ["git", "-C", str(repo), "show", f"{tree}:{path}"]
    )


def compile_function(source: bytes, name: str, namespace: dict[str, object]):
    node = function_node(source, name)
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    exec(compile(module, f"frozen:{name}", "exec"), namespace)
    return namespace[name], node


class RecordingPipe:
    def __init__(self, stream, captured: list[str]):
        self.stream = stream
        self.captured = captured

    def __iter__(self):
        for line in self.stream:
            self.captured.append(line)
            yield line


class ProcessView:
    def __init__(self, process: subprocess.Popen[str], stdout):
        self._process = process
        self.stdout = stdout

    def poll(self):
        return self._process.poll()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO)
    args = parser.parse_args()

    freeze = json.loads((HERE / "FREEZE-A02.json").read_text(encoding="utf-8"))
    tree = args.source_tree
    if tree != freeze["composition_tree"]:
        raise SystemExit("HOLD_CONSTRUCTION: source tree differs from freeze")
    if sys.version.split()[0] != freeze["python_version"]:
        raise SystemExit("HOLD_CONSTRUCTION: Python version differs from freeze")

    session_bytes = git_blob(args.repo_root, tree, SESSION_PATH)
    controller_bytes = git_blob(args.repo_root, tree, CONTROLLER_PATH)
    session_emit, emit_node = compile_function(
        session_bytes, "emit", {"json": json, "time": time, "threading": threading}
    )

    out = HERE / "results" / "a02"
    if out.exists():
        raise SystemExit("STOP: candidate output already exists")
    out.mkdir(parents=True)
    input_path = HERE / "INPUT_EVENT.json"
    input_bytes = input_path.read_bytes()
    input_event = json.loads(input_bytes)
    if input_event.get("event") != "input_released" or input_event.get("grants_input_authority") is not False:
        raise SystemExit("HOLD_CONSTRUCTION: frozen input shape is invalid")

    emit_source = ast.unparse(emit_node)
    child_code = "\n".join([
        "import json, threading, time",
        "from pathlib import Path",
        "from types import SimpleNamespace",
        f"args = SimpleNamespace(out=Path({str(out)!r}))",
        "lock = threading.RLock()",
        "events = []",
        "latest_observation = None",
        emit_source,
        f"emit(json.loads(Path({str(input_path)!r}).read_text(encoding='utf-8')))" ,
        "",
    ])
    child_code_path = out / "child_source.py.txt"
    child_code_path.write_text(child_code, encoding="utf-8", newline="\n")

    process = subprocess.Popen(
        [sys.executable, "-c", child_code], stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", bufsize=1,
    )
    assert process.stdout is not None and process.stderr is not None
    captured_stdout: list[str] = []
    process_view = ProcessView(process, RecordingPipe(process.stdout, captured_stdout))
    incoming: queue.Queue[dict] = queue.Queue()
    all_events: list[dict] = []
    reader_errors: list[str] = []
    controller_ns: dict[str, object] = {
        "json": json, "time": time, "queue": queue,
        "process": process_view, "all_events": all_events,
        "incoming": incoming, "reader_errors": reader_errors, "latest": None,
    }
    reader, _ = compile_function(controller_bytes, "reader", controller_ns)
    wait, _ = compile_function(controller_bytes, "wait", controller_ns)
    reader_thread = threading.Thread(target=reader, daemon=True)
    started_ns = time.perf_counter_ns()
    reader_thread.start()
    try:
        received = wait(
            lambda row: row.get("event") == "input_released" and row.get("id") == input_event["id"],
            timeout=3,
        )
        reader_thread.join(timeout=3)
        process.wait(timeout=3)
        stderr = process.stderr.read()
    except BaseException:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=3)
        reader_thread.join(timeout=3)
        raise
    elapsed_ns = time.perf_counter_ns() - started_ns

    raw_stdout = "".join(captured_stdout)
    (out / "CHILD_STDOUT.jsonl").write_text(raw_stdout, encoding="utf-8", newline="\n")
    (out / "CHILD_STDERR.txt").write_text(stderr, encoding="utf-8", newline="\n")
    (out / "CONTROLLER_RECEIVED.json").write_text(
        json.dumps(received, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8", newline="\n",
    )

    rows = [json.loads(line) for line in raw_stdout.splitlines() if line.strip()]
    if process.returncode != 0 or stderr or reader_errors or reader_thread.is_alive():
        raise SystemExit("FAIL_TRANSPORT: child/reader did not close cleanly")
    if len(rows) != 1 or len(all_events) != 1 or rows[0] != received:
        raise SystemExit("FAIL_TRANSPORT: child/reader row count or payload mismatch")
    if rows[0].get("emit_ns", None).__class__ is not int:
        raise SystemExit("FAIL_TRANSPORT: emit timestamp is not an integer")
    emitted_payload = dict(rows[0])
    emitted_payload.pop("emit_ns")
    if emitted_payload != input_event:
        raise SystemExit("FAIL_TRANSPORT: input payload changed outside emit_ns")
    owner_release = received.get("owner_release", {})
    per_key = owner_release.get("per_key_release_measurements", [])
    if len(per_key) != 2 or any(item.get("grants_input_authority") is not False for item in per_key):
        raise SystemExit("FAIL_TRANSPORT: nested release count/authority mismatch")

    events_path = out / "events.jsonl"
    delivered_path = out / "delivered.jsonl"
    result = {
        "schema": "v39-session-child-pipe-result-v1",
        "disposition": "PASS_CHILD_PIPE_TRANSPORT_SCOPED",
        "source_tree": tree,
        "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "stdout_sha256": hashlib.sha256(raw_stdout.encode("utf-8")).hexdigest(),
        "events_log_sha256": hashlib.sha256(events_path.read_bytes()).hexdigest(),
        "delivered_log_sha256": hashlib.sha256(delivered_path.read_bytes()).hexdigest(),
        "child_exit_code": process.returncode,
        "child_stderr_empty": not stderr,
        "reader_errors": reader_errors,
        "reader_thread_joined": not reader_thread.is_alive(),
        "stdout_lines": len(rows),
        "controller_rows": len(all_events),
        "received_event": received.get("event"),
        "received_id": received.get("id"),
        "per_key_release_count": len(per_key),
        "authority_granted": received.get("grants_input_authority"),
        "elapsed_ns": elapsed_ns,
        "scope": "exact source-extracted emit/reader/wait functions over one actual local child stdout pipe; no session main or live input",
    }
    (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "RUN_RECEIPT.json").write_text(json.dumps({
        "python": sys.version,
        "child_returncode": process.returncode,
        "child_pid": process.pid,
        "input_event_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "exact_emitter_function_sha256": hashlib.sha256(emit_source.encode("utf-8")).hexdigest(),
        "stdout_line_count": len(rows),
        "controller_received_count": len(all_events),
        "stderr_bytes": len(stderr.encode("utf-8")),
        "elapsed_ns": elapsed_ns,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
