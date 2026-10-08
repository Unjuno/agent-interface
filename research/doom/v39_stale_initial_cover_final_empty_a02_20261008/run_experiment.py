"""Exercise latest PR #8643 initial-cover recovery on the final-empty schedule."""
import ast
import hashlib
import json
import queue
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
CONTROLLER = "research/doom/map01_overlap_controller_v39.py"


def source(commit, role):
    expected = FREEZE["sources"][role][CONTROLLER]
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", f"{commit}:{CONTROLLER}"], text=True
    ).strip()
    data = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
    if blob != expected["blob"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
        raise ValueError(f"frozen controller source mismatch: {commit}")
    return data.decode("utf-8")


def load_functions(text, names):
    tree = ast.parse(text)
    body = [node for node in tree.body if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id in {
            "MAX_PENDING_OBSERVATION_EVENTS",
            "MAX_PENDING_OBSERVATION_RECOVERY_BATCHES",
        } for target in node.targets)]
    body.extend(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name in names)
    found = {node.name for node in body if isinstance(node, ast.FunctionDef)}
    if set(names) - found:
        raise AssertionError(f"missing helper functions: {set(names) - found}")
    namespace = {"queue": queue}
    exec(compile(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])),
                 "frozen-controller-helpers.py", "exec"), namespace)
    return namespace


class LateArrivalQueue(queue.Queue):
    def __init__(self):
        super().__init__()
        self.inject = True
        super().put({"event": "observation", "sequence": 11,
                     "image": "frame-11.png"})

    def empty(self):
        empty = super().empty()
        if empty and self.inject:
            self.inject = False
            super().put({"event": "observation", "sequence": 12,
                         "image": "frame-12.png", "health": 72,
                         "hard_crossing": True})
        return empty


class Monitor:
    event_types = {"typed_observation", "observation"}

    def __init__(self):
        self.seen = []

    def observe(self, row):
        self.seen.append(row["sequence"])
        if row.get("hard_crossing"):
            return {"event": "policy_invalidation",
                    "reason": "health:below_hard_minimum",
                    "sequence": row["sequence"]}
        return None


def verify_wiring(text):
    tree = ast.parse(text)
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == "main")
    call_found = any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                     and node.func.id == "recover_stale_cover_submission"
                     for node in ast.walk(main))
    branch = ast.unparse(main)
    if not call_found or "cover_ack" not in branch or "cover_submission_recovery" not in branch:
        raise AssertionError("main controller does not wire initial-cover stale recovery")
    return True


def run():
    base_commit = FREEZE["baseline_commit"]
    candidate_commit = FREEZE["candidate_commit"]
    base_source = source(base_commit, "baseline")
    candidate_source = source(candidate_commit, "candidate")
    wired = verify_wiring(candidate_source)

    baseline_ns = load_functions(base_source, ["drain_pending_observation_events"])
    incoming = LateArrivalQueue()
    drained = baseline_ns["drain_pending_observation_events"](incoming, None, "terminal")
    if (drained["latest"]["sequence"] != 11 or drained["pending_events"]
            or incoming.qsize() != 1):
        raise AssertionError("final-empty late-arrival schedule was not reproduced")
    late_sequence = incoming.queue[0]["sequence"]
    if late_sequence != 12:
        raise AssertionError("unexpected late observation sequence")

    candidate_ns = load_functions(candidate_source, [
        "drain_pending_observation_events", "settle_pending_observation_backlog",
        "recover_pending_observation_backlog", "recover_stale_cover_submission",
    ])
    monitor = Monitor()
    recovered = candidate_ns["recover_stale_cover_submission"](
        {"event": "rejected", "id": "cover-0",
         "reason": "latest observation sequence required before input"},
        identifier="cover-0", expected_sequence=11, consumed_events=[],
        latest=drained["latest"], incoming=incoming,
        wait=lambda *_args, **_kwargs:
            (_ for _ in ()).throw(AssertionError("queued event should avoid wait")),
        observation_monitor=monitor)
    if recovered["latest"]["sequence"] != 12:
        raise AssertionError("initial cover recovery did not return the late full observation")
    if recovered["invalidation"] is None or recovered["invalidation"]["sequence"] != 12:
        raise AssertionError("late hard crossing was not evaluated by cover monitor")
    if recovered["cover_policy"] != "discarded_until_fresh_plan":
        raise AssertionError("stale cover was not discarded")
    if incoming.qsize() != 0 or monitor.seen != [12]:
        raise AssertionError("late event not consumed exactly once")

    return {
        "schema": "v39-stale-initial-cover-final-empty-comparison-v1",
        "baseline_commit": base_commit,
        "candidate_commit": candidate_commit,
        "baseline": {"latest_sequence": 11, "pending_events": False,
                     "late_sequence_still_queued": 12},
        "candidate": {"initial_cover_recovery_wired": wired,
                      "recovered_sequence": recovered["latest"]["sequence"],
                      "late_hard_crossing_observed": recovered["invalidation"]["reason"],
                      "stale_cover_disposition": recovered["cover_policy"],
                      "queue_empty_after_recovery": incoming.qsize() == 0,
                      "stale_cover_resubmitted": False},
        "decision": "PASS; candidate initial-cover recovery consumes and evaluates final-empty late arrival",
        "scope": "Exact current-main drain and exact latest-PR recovery helper under deterministic queue scheduling; static caller-wiring check; mock observation monitor. No full controller process, live game, GUI, model, OS input, physical release measurement, or task effect.",
    }


if __name__ == "__main__":
    result = run()
    (ROOT / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n",
                                      encoding="utf-8")
    print(json.dumps(result, indent=2))
