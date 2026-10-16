"""Compose the exact owner-release producer and consumer methods offline."""
import ast
import copy
import hashlib
import json
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FREEZE_PATH = HERE / "FREEZE-A08.json"
OUT = HERE / "results/a08"
INPUT = HERE / "results/a03/candidate-events.jsonl"
SOURCES = {
    "lease_cause_v1.py": ROOT / "research/live_control/lease_cause_v1.py",
    "lease_cause_v2.py": ROOT / "research/live_control/lease_cause_v2.py",
    "lease_release_v1.py": ROOT / "research/live_control/lease_release_v1.py",
    "executor_v12.py": ROOT / "research/live_control/executor_v12.py",
    "map01_overlap_controller_v39.py": ROOT / "research/doom/map01_overlap_controller_v39.py",
    "running_action_guard_v3.py": ROOT / "research/live_control/running_action_guard_v3.py",
}


def extract(path, names, namespace, super_class=None):
    tree = ast.parse(path.read_bytes())
    nodes = [node for node in ast.walk(tree)
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
             and node.name in names]
    found = {node.name for node in nodes}
    if found != set(names):
        raise RuntimeError(f"method extraction mismatch {path}: {found}")
    if super_class is not None:
        class SuperRewrite(ast.NodeTransformer):
            def visit_Call(self, node):
                self.generic_visit(node)
                if isinstance(node.func, ast.Name) and node.func.id == "super" and not node.args:
                    node.args = [ast.Name(id=super_class, ctx=ast.Load()), ast.Name(id="self", ctx=ast.Load())]
                return node
        nodes = [SuperRewrite().visit(node) for node in nodes]
        ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    return namespace


def main():
    if OUT.exists():
        raise SystemExit("STOP: A05 candidate output already exists")
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    for name, record in freeze["sources"].items():
        path = SOURCES.get(name, {
            "a03_candidate_events.jsonl": INPUT,
            "a03_result.json": HERE / "results/a03/RESULT.json",
            "run_a08.py": HERE / "run_a08.py",
            "audit_a08.py": HERE / "audit_a08.py",
        }.get(name))
        if path is None or hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            raise SystemExit(f"STOP: frozen source mismatch: {name}")
    if sys.version.split()[0] != freeze["python_version"]:
        raise SystemExit("STOP: Python runtime mismatch")

    data = {"copy": copy, "threading": threading, "time": time, "json": json,
            "LeaseV1": None, "LeaseV2": None, "LeaseV3": None}
    # Freeze the accepted cancellation reason set directly from source.
    lease_tree = ast.parse(SOURCES["lease_cause_v1.py"].read_bytes())
    reasons_node = next(node for node in lease_tree.body
                        if isinstance(node, ast.Assign) and
                        any(isinstance(t, ast.Name) and t.id == "REASONS" for t in node.targets))
    reasons_value = reasons_node.value
    if (isinstance(reasons_value, ast.Call) and isinstance(reasons_value.func, ast.Name)
            and reasons_value.func.id == "frozenset" and len(reasons_value.args) == 1):
        data["REASONS"] = frozenset(ast.literal_eval(reasons_value.args[0]))
    else:
        data["REASONS"] = ast.literal_eval(reasons_value)
    class LeaseV1:
        pass

    class LeaseV2(LeaseV1):
        pass

    class LeaseV3(LeaseV2):
        pass

    # Correct each layer binding before instantiating the class chain.
    # Namespaces are method globals; methods themselves are assigned explicitly.
    v1 = {"copy": copy, "REASONS": data["REASONS"]}
    extract(SOURCES["lease_cause_v1.py"], ("record_interruption", "interruption_snapshot"), v1)
    v2 = {"threading": threading}
    extract(SOURCES["lease_cause_v2.py"], ("record_interruption",), v2, "LeaseV1")
    v2["LeaseV1"] = LeaseV1
    v3 = {"copy": copy, "threading": threading}
    extract(SOURCES["lease_release_v1.py"], ("record_interruption", "wait_interruption"), v3, "LeaseV2")
    v3["LeaseV2"] = LeaseV2
    data.update({"LeaseV1": LeaseV1, "LeaseV2": LeaseV2, "LeaseV3": LeaseV3})
    LeaseV1.record_interruption = v1["record_interruption"]
    LeaseV1.interruption_snapshot = v1["interruption_snapshot"]
    LeaseV2.record_interruption = v2["record_interruption"]
    LeaseV3.record_interruption = v3["record_interruption"]
    LeaseV3.wait_interruption = v3["wait_interruption"]

    extract(SOURCES["executor_v12.py"], ("_publish_release", "_publish_release_cause"), data)
    extract(SOURCES["map01_overlap_controller_v39.py"], ("cancel_invalidated_action",), data)
    guard_ns = {"deepcopy": copy.deepcopy}
    extract(SOURCES["running_action_guard_v3.py"], ("record_input_released",), guard_ns)

    rows = [json.loads(line) for line in INPUT.read_text(encoding="utf-8").splitlines() if line]
    cleanup = next(row for row in rows if row.get("event") == "owner_release")
    admission = next(row for row in rows if row.get("event") == "input_admission")
    token = admission["physical_key_measurement"]["bracket"]["intent_token"]
    lease = LeaseV3()
    lease._cause_lock = threading.Lock()
    lease._cause = None
    lease.intent_token = token
    lease._wake = threading.Event()
    lease._interruption_ready = threading.Event()
    lease.record_interruption(cleanup)

    class ExecutorHarness:
        _publish_release = data["_publish_release"]
        _publish_release_cause = data["_publish_release_cause"]

    published = []
    executor = ExecutorHarness()
    executor.lock = threading.RLock()
    executor.active = ("hold-a03", lease, None)
    executor.release_publication_attempted_ids = set()
    executor.published_release_ids = set()
    executor.release_publication_errors = {}
    executor._external_emit = published.append
    executor._publish_release("hold-a03", lease)
    if len(published) != 1:
        raise RuntimeError(f"publisher emitted {len(published)} events")

    class GuardHarness:
        record_input_released = guard_ns["record_input_released"]

        def record_cancel_requested(self, event):
            self.guard.cancellation = event

        def record_cancelled_terminal(self, event):
            self.active_intent = None
            self.terminal = copy.deepcopy(event)
            return self.receipt()

        def receipt(self):
            return {"early_releases": copy.deepcopy(self.early_releases),
                    "current_input_authority": False,
                    "program_terminal_pending": self.active_intent is not None and bool(self.early_releases)}

    guard = GuardHarness()
    guard.guard = SimpleNamespace(state="CANCEL_REQUIRED", cancellation=None)
    guard.active_intent = {"id": "hold-a03", "intent_token": token}
    guard.early_releases = []
    cancel_event = {"event": "cancel_requested", "id": "hold-a03",
                    "matched": True, "requested_ns": cleanup["verified_ns"] - 1}
    terminal = {"event": "terminal", "id": "hold-a03", "status": "cancelled",
                "release": {"verified_ns": cleanup["verified_ns"] + 2}}
    sequence = iter((cancel_event, published[0], terminal))

    class Stdin:
        def __init__(self):
            self.lines = []

        def write(self, value):
            self.lines.append(value)

        def flush(self):
            pass

    class Process:
        def __init__(self):
            self.stdin = Stdin()

    process = Process()
    def wait(predicate):
        event = next(sequence)
        if not predicate(event):
            raise RuntimeError(f"unexpected controller event: {event}")
        return event

    controller = data["cancel_invalidated_action"]
    _cancel, released, release_receipt, _terminal, terminal_receipt = controller(
        process, wait, "hold-a03", guard)
    OUT.mkdir(parents=True)
    (OUT / "published-events.jsonl").write_text(
        json.dumps(published[0], sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8", newline="\n")
    (OUT / "controller-handoff.json").write_text(
        json.dumps(released, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8", newline="\n")
    (OUT / "release-receipt.json").write_text(
        json.dumps(release_receipt, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8", newline="\n")
    (OUT / "terminal-receipt.json").write_text(
        json.dumps(terminal_receipt, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8", newline="\n")
    result = {
        "run_id": freeze["run_id"],
        "status": "PASS_SOURCE_COMPOSED_RELEASE_EVIDENCE_FLOW_SCOPED",
        "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "published_event_sha256": hashlib.sha256((OUT / "published-events.jsonl").read_bytes()).hexdigest(),
        "controller_handoff_sha256": hashlib.sha256((OUT / "controller-handoff.json").read_bytes()).hexdigest(),
        "release_receipt_sha256": hashlib.sha256((OUT / "release-receipt.json").read_bytes()).hexdigest(),
        "per_key_release_count": len(cleanup["per_key_release_measurements"]),
        "current_input_authority": release_receipt["current_input_authority"],
        "program_terminal_pending_after_release": release_receipt["program_terminal_pending"],
        "program_terminal_pending_after_terminal": terminal_receipt["program_terminal_pending"],
        "scope": "exact source-extracted lease, executor publisher, controller handoff, and guard methods; A03 fake-display evidence; no runtime or game",
    }
    (OUT / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                     encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
