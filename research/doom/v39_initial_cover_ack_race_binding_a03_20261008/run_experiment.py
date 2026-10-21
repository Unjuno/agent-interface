"""Join the final-empty queue race to latest candidate's initial-cover wrapper."""
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


def pinned(commit, role):
    expected = FREEZE["sources"][role][CONTROLLER]
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", f"{commit}:{CONTROLLER}"], text=True
    ).strip()
    data = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
    if blob != expected["blob"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
        raise ValueError(f"source mismatch at {commit}")
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
        raise AssertionError(f"missing functions: {set(names) - found}")
    namespace = {"queue": queue}
    exec(compile(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])),
                 "frozen-cover-recovery-functions.py", "exec"), namespace)
    return namespace


class LateArrivalQueue(queue.Queue):
    def __init__(self):
        super().__init__()
        self.inject = True
        super().put({"event": "observation", "sequence": 11,
                     "image": "frame-11.png"})

    def empty(self):
        result = super().empty()
        if result and self.inject:
            self.inject = False
            super().put({"event": "observation", "sequence": 12,
                         "image": "frame-12.png", "hard_crossing": True})
        return result


class Monitor:
    event_types = {"typed_observation", "observation"}

    def __init__(self):
        self.seen = []

    def observe(self, row):
        self.seen.append(row["sequence"])
        if row.get("hard_crossing"):
            return {"event": "policy_invalidation", "sequence": row["sequence"],
                    "reason": "health:below_hard_minimum"}
        return None


def verify_wiring(text):
    tree = ast.parse(text)
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == "main")
    calls = [node for node in ast.walk(main) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name)
             and node.func.id == "submit_initial_cover_with_recovery"]
    if len(calls) != 1:
        raise AssertionError("main must route initial cover through one recovery wrapper")
    return True


def run():
    base_commit, candidate_commit = (FREEZE["baseline_commit"],
                                     FREEZE["candidate_commit"])
    baseline_text = pinned(base_commit, "baseline")
    candidate_text = pinned(candidate_commit, "candidate")
    wired = verify_wiring(candidate_text)
    baseline = load_functions(baseline_text, ["drain_pending_observation_events"])
    incoming = LateArrivalQueue()
    drained = baseline["drain_pending_observation_events"](incoming, None, "terminal")
    if (drained["latest"]["sequence"] != 11 or drained["pending_events"]
            or incoming.qsize() != 1):
        raise AssertionError("final-empty schedule did not leave sequence 12 queued")

    candidate = load_functions(candidate_text, [
        "drain_pending_observation_events", "settle_pending_observation_backlog",
        "recover_pending_observation_backlog", "recover_stale_cover_submission",
        "submit_initial_cover_with_recovery",
    ])
    latest = {"event": "observation", "sequence": 11, "image": "frame-11.png"}
    event_log = []
    monitor = Monitor()
    rejected_ack = {"event": "rejected", "id": "cover-0",
                    "reason": "latest observation sequence required before input"}
    wrapper = candidate["submit_initial_cover_with_recovery"](
        lambda: rejected_ack, identifier="cover-0", latest_reader=lambda: latest,
        event_log=event_log, incoming=incoming,
        wait=lambda *_args, **_kwargs:
            (_ for _ in ()).throw(AssertionError("queued event should be drained")),
        observation_monitor=monitor)
    if wrapper["submitted_sequence"] != 11:
        raise AssertionError("wrapper did not preserve pre-submit source sequence")
    if wrapper["latest"]["sequence"] != 12:
        raise AssertionError("wrapper did not return the recovered late observation")
    if wrapper["invalidation"]["reason"] != "health:below_hard_minimum":
        raise AssertionError("hard crossing not propagated through wrapper")
    if wrapper["cover_policy"] != "discarded_until_fresh_plan":
        raise AssertionError("stale cover policy was not discarded")
    if monitor.seen != [12] or incoming.qsize() != 0:
        raise AssertionError("late row was not evaluated and consumed exactly once")

    return {
        "schema": "v39-initial-cover-ack-race-binding-comparison-v1",
        "baseline_commit": base_commit,
        "candidate_commit": candidate_commit,
        "baseline": {"latest_sequence": 11, "pending_events": False,
                     "queued_late_sequence": 12},
        "candidate": {"wrapper_wired_into_main": wired,
                      "sequence_bound_before_submit": wrapper["submitted_sequence"],
                      "fresh_sequence_after_rejection": wrapper["latest"]["sequence"],
                      "late_hard_crossing": wrapper["invalidation"]["reason"],
                      "old_cover_policy": wrapper["cover_policy"],
                      "queue_empty": incoming.qsize() == 0,
                      "cover_retried": False},
        "decision": "PASS; wrapper preserves pre-submit sequence and recovers final-empty late event",
        "scope": "Exact current-main drain and exact latest-candidate initial-cover recovery wrapper/helper; source-level main wiring; deterministic queue and mock monitor. No full controller, live game, GUI, model, OS input, physical release measurement, or task effect.",
    }


if __name__ == "__main__":
    result = run()
    (ROOT / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n",
                                      encoding="utf-8")
    print(json.dumps(result, indent=2))
