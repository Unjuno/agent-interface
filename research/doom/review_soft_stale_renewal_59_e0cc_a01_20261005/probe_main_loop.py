"""Review-only deterministic probe for the pinned V39 renewal/coverless main loop.

No controller source is imported or edited. The exact nested wait/submit_cover
functions and ThreadPoolExecutor `with` block are extracted from the pinned AST.
This file is intended to be frozen and invoked by the parent reviewer.
"""
import ast
import json
import hashlib
from pathlib import Path
import queue
import time
from types import SimpleNamespace

SOURCE = Path(__file__).resolve().parent / "view/research/doom/map01_overlap_controller_v39.py"
STALE = "latest observation sequence required before input"


class Stdin:
    def __init__(self):
        self.writes = []
    def write(self, value): self.writes.append(value)
    def flush(self): pass


class Process:
    def __init__(self): self.stdin = Stdin()
    def poll(self): return None


class Monitor:
    event_types = frozenset({"typed_observation"})
    def __init__(self): self.seen = []
    def observe(self, row):
        self.seen.append(row)
        if row.get("monitor_result") is None:
            return None
        return row["monitor_result"]


class Planner:
    def __init__(self, future): self.future, self.interrupts = future, []
    def interrupt(self, handle):
        receipt = {"status": "interrupted", "turn_id": handle}
        self.interrupts.append(receipt)
        self.future.interrupted = True
        return receipt
    def await_turn(self, handle, timeout):
        raise AssertionError("fake executor must not start a worker")


class ScriptedFuture:
    def __init__(self, incoming): self.incoming, self.interrupted = incoming, False
    def done(self): return self.interrupted or self.incoming.empty()
    def result(self):
        status = "interrupted" if self.interrupted else "completed"
        return SimpleNamespace(answer={"state": "active"}, usage={},
            handle=SimpleNamespace(thread_id="synthetic-thread"), status=status,
            answer_eligible=(status == "completed"))


class Executor:
    scripted_future = None
    def __init__(self, max_workers=1): self.future = Executor.scripted_future
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def submit(self, fn, *args): return self.future


class FailureCleanup:
    def set_stage(self, stage): pass


def load_loop():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    nested = {n.name: n for n in ast.walk(main)
              if isinstance(n, ast.FunctionDef) and n.name in {"wait", "submit_cover"}}
    if set(nested) != {"wait", "submit_cover"}:
        raise AssertionError("pinned main no longer has exact wait/submit_cover closures")
    blocks = [n for n in ast.walk(main) if isinstance(n, ast.With) and
              any(isinstance(x.context_expr, ast.Call) and
                  isinstance(x.context_expr.func, ast.Name) and
                  x.context_expr.func.id == "ThreadPoolExecutor" for x in n.items)]
    if len(blocks) != 1:
        raise AssertionError("expected exactly one ThreadPoolExecutor main block")
    loop_parent = next(n for n in ast.walk(main) if isinstance(n, ast.For) and blocks[0] in n.body)
    with_index = loop_parent.body.index(blocks[0])
    post_if = next((n for n in loop_parent.body[with_index + 1:] if isinstance(n, ast.If) and
                    "current_terminal" in ast.dump(n.test) and "Is()" in ast.dump(n.test) and "value=None" in ast.dump(n.test)), None)
    if post_if is None:
        raise AssertionError("main no longer has its post-turn no-active-cover terminal gate")
    helpers = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef) and
               n.name in {"classify_cover_renewal_response", "wait_without_active_cover",
                          "resolve_invalidated_cover_submission", "cancel_invalidated_cover"}}
    required = {"classify_cover_renewal_response", "wait_without_active_cover",
                "resolve_invalidated_cover_submission", "cancel_invalidated_cover"}
    if set(helpers) != required:
        raise AssertionError(f"pinned loop helpers changed: {set(helpers)}")

    factory = ast.FunctionDef(
        name="factory",
        args=ast.arguments(posonlyargs=[], args=[ast.arg(arg="rows"), ast.arg(arg="mode")],
                           kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=[], decorator_list=[])
    setup = ast.parse(
        "incoming = queue.Queue()\n"
        "for row in rows: incoming.put(row)\n"
        "process = Process()\n"
        "monitor = Monitor()\n"
        "future = ScriptedFuture(incoming)\n"
        "Executor.scripted_future = future\n"
        "planner = Planner(future)\n"
        "planner_handle = 'synthetic-turn'\n"
        "failure_cleanup = FailureCleanup()\n"
        "latest = {'event': 'observation', 'sequence': 7, 'capture_ns': 70, 'image': 'source.png'}\n"
        "validity_monitor = monitor\n"
        "invalidation_monitor = monitor\n"
        "model_started_ns = time.perf_counter_ns()\n"
        "all_events = []\n"
        "reader_errors = []\n"
        "clock_ns = 0\n"
        "cover_steps = [{'op': 'observe'}]\n"
        "cover_ids = ['cover-0']\n"
        "cover_terminals = []\n"
        "cover_renewal_gaps_ms = []\n"
        "cover_renewal_rejections = []\n"
        "cover = 'cover-0'\n"
        "index = 0\n"
        "model_session_id = 'synthetic-thread'\n"
        "invalidation = None\n"
        "planner_interrupt = None\n"
        "current_cover = cover\n"
        "current_terminal = None\n"
        "renewal_admission_resolution = None\n"
        "error = None\n").body
    factory.body.extend(setup)
    factory.body.extend([nested["wait"], nested["submit_cover"]])
    post_index = loop_parent.body.index(post_if)
    try_node = ast.Try(body=loop_parent.body[with_index:post_index], handlers=[ast.ExceptHandler(
        type=ast.Name(id="RuntimeError", ctx=ast.Load()), name="caught",
        body=[ast.Assign(targets=[ast.Name(id="error", ctx=ast.Store())],
                         value=ast.Name(id="caught", ctx=ast.Load()))])],
        orelse=[], finalbody=[])
    factory.body.append(try_node)
    factory.body.extend(ast.parse("if error is None:\n    pass").body)
    success_gate = factory.body[-1]
    success_gate.body = [post_if]
    factory.body.extend(ast.parse(
        "return {'error': error, 'future_done': future.done(), 'planner_result': planner_result if error is None else None, "
        "'current_cover': current_cover, 'current_terminal': current_terminal, 'cover_ids': list(cover_ids), "
        "'cover_terminals': list(cover_terminals), 'cover_renewal_rejections': list(cover_renewal_rejections), "
        "'planner_interrupts': list(planner.interrupts), 'monitor_seen': list(monitor.seen), "
        "'latest': latest, 'writes': list(process.stdin.writes)}").body)
    module = ast.fix_missing_locations(ast.Module(body=[*helpers.values(), factory], type_ignores=[]))
    scope = {"queue": queue, "time": time, "json": json, "ThreadPoolExecutor": Executor,
             "Process": Process, "Monitor": Monitor, "Planner": Planner, "Executor": Executor,
             "ScriptedFuture": ScriptedFuture, "FailureCleanup": FailureCleanup,
             "STALE_SEQUENCE_REJECTION_REASON": STALE}
    exec(compile(module, str(SOURCE), "exec"), scope)
    return scope["factory"]


def check(condition):
    if not condition:
        raise AssertionError("main-loop transition contract failed")


def terminal():
    return {"event": "terminal", "id": "cover-0", "status": "completed",
            "terminal_ns": 100, "release": {"verified": True, "keys_down": [], "buttons_down": []}}


def trow(seq, valence="soft"):
    result = None if valence == "soft" else {
        "event": "paired_signal_invalidation", "sequence": seq,
        "reason": "unknown_signal" if valence == "unknown" else "hard_change"}
    return {"event": "typed_observation", "sequence": seq, "capture_ns": seq * 10,
            "monitor_result": result}


def full(seq):
    return {"event": "observation", "sequence": seq, "capture_ns": seq * 10,
            "image": f"frame-{seq}.png", "pointer_binding": {"surface": 1}}


def schedule(tail, rejection_reason=STALE):
    return [terminal(), trow(8), full(8), {"event": "rejected", "id": "cover-0-renew-1",
            "reason": rejection_reason}, *tail]


def run_probe():
    factory = load_loop()
    result = {}
    # Rejection -> no-cover -> soft observations -> normal completion.
    soft = factory(schedule([trow(9), full(9)]), "soft")
    check(soft["error"] is None)
    check(soft["current_cover"] is None)
    check(soft["current_terminal"] is soft["cover_terminals"][0])
    check(soft["current_terminal"]["release"] == {"verified": True, "keys_down": [], "buttons_down": []})
    check([x["id"] for x in soft["cover_renewal_rejections"]] == ["cover-0-renew-1"])
    check(soft["cover_renewal_rejections"][0]["submitted_sequence"] == 7)
    check(soft["cover_renewal_rejections"][0]["latest_sequence_after_rejection"] == 8)
    check(soft["cover_ids"] == ["cover-0"])
    check(len(soft["cover_terminals"]) == 1)
    check(len(soft["planner_interrupts"]) == 0)
    check(len(soft["writes"]) == 1 and json.loads(soft["writes"][0])["op"] == "submit")
    result["soft_completion"] = "PASS: previous terminal retained; rejected renewal untracked; no cancel/interrupt"

    # Same transition, then hard/unknown event while coverless: one bounded interrupt, no replacement terminal.
    for kind in ("hard", "unknown"):
        case = factory(schedule([trow(9), full(9), trow(10, kind)]), kind)
        check(case["error"] is None)
        check(case["current_cover"] is None)
        check(case["current_terminal"] is case["cover_terminals"][0])
        check(case["current_terminal"]["release"]["verified"] is True)
        check(case["current_terminal"]["release"]["keys_down"] == [])
        check(case["current_terminal"]["release"]["buttons_down"] == [])
        check(case["cover_ids"] == ["cover-0"] and len(case["cover_terminals"]) == 1)
        check(len(case["cover_renewal_rejections"]) == 1)
        check(len(case["planner_interrupts"]) == 1)
        check(case["planner_interrupts"][0]["turn_id"] == "synthetic-turn")
        check(case["planner_result"].status == "interrupted")
        check(len(case["writes"]) == 1 and json.loads(case["writes"][0])["op"] == "submit")
        result[f"{kind}_invalidation"] = "PASS: one finite interrupt; no rejected-cover cancel/terminal; old empty release retained"

    # Unknown executor rejection must stop immediately rather than enter coverless continuation.
    bad = schedule([], rejection_reason="invalid program")
    failure = factory(bad, "unexpected")
    check(isinstance(failure["error"], RuntimeError))
    check(failure["current_terminal"] is failure["cover_terminals"][0])
    check(failure["cover_ids"] == ["cover-0"])
    check(len(failure["planner_interrupts"]) == 0)
    check(len(failure["writes"]) == 1 and json.loads(failure["writes"][0])["op"] == "submit")
    result["unexpected_rejection"] = "PASS: fails closed without cancellation of rejected renewal"
    return {"probe": "PASS", "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(), "cases": result,
            "claim_limit": "deterministic extracted-main ordering only; no live executor or model claim"}


if __name__ == "__main__":
    print(json.dumps(run_probe(), indent=2, sort_keys=True))
