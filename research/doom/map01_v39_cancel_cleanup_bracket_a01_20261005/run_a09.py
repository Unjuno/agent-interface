"""Replay a retained release row through exact session JSONL and controller methods."""
import ast
import contextlib
import hashlib
import io
import json
import queue
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FREEZE = HERE / "FREEZE-A09.json"
OUT = HERE / "results/a09"
INPUT = HERE / "results/a08/published-events.jsonl"
SESSION = ROOT / "research/doom/session_map01_v12.py"
CONTROLLER = ROOT / "research/doom/map01_overlap_controller_v39.py"


def extract_function(source_path, name, namespace):
    tree = ast.parse(source_path.read_bytes())
    found = [node for node in ast.walk(tree)
             if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(found) != 1:
        raise RuntimeError(f"expected one {name} function in {source_path}, found {len(found)}")
    node = found[0]
    class NonlocalToGlobal(ast.NodeTransformer):
        def visit_Nonlocal(self, item):
            return ast.Global(names=item.names)
    node = NonlocalToGlobal().visit(node)
    ast.fix_missing_locations(node)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source_path), "exec"), namespace)
    return namespace[name]


def main():
    if OUT.exists():
        raise SystemExit("STOP: A09 candidate output already exists")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    frozen_paths = {
        "session_map01_v12.py": SESSION,
        "map01_overlap_controller_v39.py": CONTROLLER,
        "a08_published_event.jsonl": INPUT,
        "run_a09.py": HERE / "run_a09.py",
        "audit_a09.py": HERE / "audit_a09.py",
    }
    for name, record in freeze["sources"].items():
        if hashlib.sha256(frozen_paths[name].read_bytes()).hexdigest() != record["sha256"]:
            raise SystemExit(f"STOP: frozen source mismatch: {name}")
    if sys.version.split()[0] != freeze["python_version"]:
        raise SystemExit("STOP: Python runtime mismatch")

    OUT.mkdir(parents=True)
    session_ns = {"json": json, "time": time, "threading": threading}
    (OUT / "setup.txt").write_text("source-extracted transport harness; no session main invoked\n")
    event = json.loads(INPUT.read_text(encoding="utf-8"))
    lock, events = threading.Lock(), []
    session_ns.update({"args": SimpleNamespace(out=OUT), "lock": lock, "events": events,
                       "latest_observation": None})
    emit = extract_function(SESSION, "emit", session_ns)
    stdout_capture = io.StringIO()
    with contextlib.redirect_stdout(stdout_capture):
        emit(event)
    (OUT / "stdout.jsonl").write_text(stdout_capture.getvalue(), encoding="utf-8", newline="\n")

    class Process:
        def __init__(self, lines):
            self.stdout = lines

        def poll(self):
            return None

    incoming = queue.Queue()
    controller_ns = {"json": json, "time": time, "queue": queue,
                     "process": Process((OUT / "stdout.jsonl").read_text(encoding="utf-8").splitlines(True)),
                     "all_events": [], "incoming": incoming, "reader_errors": [], "latest": None}
    reader = extract_function(CONTROLLER, "reader", controller_ns)
    wait = extract_function(CONTROLLER, "wait", controller_ns)
    reader()
    received = wait(lambda row: row.get("event") == "input_released" and row.get("id") == event["id"], timeout=1)
    (OUT / "received-event.json").write_text(json.dumps(received, sort_keys=True, separators=(",", ":")) + "\n",
                                              encoding="utf-8", newline="\n")
    artifacts = (OUT / "events.jsonl", OUT / "delivered.jsonl", OUT / "stdout.jsonl", OUT / "received-event.json")
    result = {
        "run_id": freeze["run_id"],
        "status": "PASS_SOURCE_COMPOSED_JSONL_TRANSPORT_SCOPED",
        "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "writer_log_sha256": hashlib.sha256(artifacts[0].read_bytes()).hexdigest(),
        "delivered_log_sha256": hashlib.sha256(artifacts[1].read_bytes()).hexdigest(),
        "stdout_sha256": hashlib.sha256(artifacts[2].read_bytes()).hexdigest(),
        "received_sha256": hashlib.sha256(artifacts[3].read_bytes()).hexdigest(),
        "received_event": received["event"],
        "per_key_release_count": len(received["owner_release"]["per_key_release_measurements"]),
        "authority_granted": received["grants_input_authority"],
        "scope": "exact source-extracted emit/reader/wait functions over retained A08 event; no session main, OS input, or game",
    }
    (OUT / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                     encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
