"""Compare current-main final-empty race with PR #8643 recovery helper."""
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
EXECUTOR = "research/live_control/executor_v12.py"


def pinned_source(commit, path, expected):
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", f"{commit}:{path}"], text=True
    ).strip()
    data = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
    if blob != expected["blob"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
        raise ValueError(f"frozen source mismatch: {commit}:{path}")
    return data.decode("utf-8")


def functions(source, names, namespace):
    tree = ast.parse(source)
    body = [node for node in tree.body if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id in {
            "MAX_PENDING_OBSERVATION_EVENTS",
            "MAX_PENDING_OBSERVATION_RECOVERY_BATCHES",
        } for target in node.targets)]
    body.extend(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name in names)
    missing = set(names) - {node.name for node in body if isinstance(node, ast.FunctionDef)}
    if missing:
        raise ValueError(f"missing frozen functions: {sorted(missing)}")
    exec(compile(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])),
                 "frozen-v39-controller-functions.py", "exec"), namespace)
    return namespace


def verify_controller_wiring(source):
    tree = ast.parse(source)
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == "main")
    execute = next(node for node in ast.walk(main)
                   if isinstance(node, ast.FunctionDef) and
                   node.name == "execute_segment")
    if not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
               and node.func.id == "recover_stale_executor_rejection"
               for node in ast.walk(execute)):
        raise AssertionError("candidate execute_segment is not wired to recovery")
    stale_routes = [node for node in ast.walk(main) if isinstance(node, ast.If)
                    and "stale_rejection" in ast.unparse(node.test)
                    and "is not None" in ast.unparse(node.test)]
    if not any(any(isinstance(child, ast.Continue) for child in ast.walk(route)) and
               "discard_reason" in ast.unparse(route) for route in stale_routes):
        raise AssertionError("recovered stale plan is not discarded before next decision")
    return True


class LateArrivalQueue(queue.Queue):
    """Insert seq 12 immediately after the baseline drain's final empty result."""
    def __init__(self):
        super().__init__()
        self.inject_after_empty = True
        super().put({"event": "observation", "sequence": 11, "id": "before-empty"})

    def empty(self):
        observed = super().empty()
        if observed and self.inject_after_empty:
            self.inject_after_empty = False
            super().put({"event": "observation", "sequence": 12,
                         "id": "arrived-after-empty"})
        return observed


class Guard:
    def record_preacceptance_rejection(self, receipt):
        return {"state": "REJECTED_BEFORE_PROGRAM_ADMISSION",
                "physical_release_verified": True,
                "current_input_authority": False,
                "requires_new_decision": True,
                "receipt": receipt}


def run():
    base_commit = FREEZE["baseline_commit"]
    candidate_commit = FREEZE["candidate_commit"]
    base_source = pinned_source(base_commit, CONTROLLER,
                                FREEZE["sources"]["baseline"][CONTROLLER])
    pinned_source(base_commit, EXECUTOR, FREEZE["sources"]["baseline"][EXECUTOR])
    candidate_source = pinned_source(candidate_commit, CONTROLLER,
                                     FREEZE["sources"]["candidate"][CONTROLLER])
    controller_wiring = verify_controller_wiring(candidate_source)

    # Reproduce the late enqueue against exact current-main drain.
    base_ns = functions(base_source, ["drain_pending_observation_events"],
                        {"queue": queue})
    late_queue = LateArrivalQueue()
    drained = base_ns["drain_pending_observation_events"](late_queue, None, "terminal")
    if (drained["latest"]["sequence"] != 11 or drained["pending_events"]
            or late_queue.qsize() != 1):
        raise AssertionError("baseline fixture did not land after final empty check")
    late = late_queue.queue[0]
    if late["sequence"] != 12:
        raise AssertionError("late event identity mismatch")

    # The exact Executor.submit source is pinned above; its previously retained
    # current-main probe establishes rejection before validation/admission/input.
    rejection = {"event": "rejected",
                 "reason": "latest observation sequence required before input"}
    if late["sequence"] <= drained["latest"]["sequence"]:
        raise AssertionError("fixture must produce stale expected sequence")

    candidate_ns = functions(candidate_source, [
        "drain_pending_observation_events", "settle_pending_observation_backlog",
        "recover_pending_observation_backlog", "recover_stale_executor_rejection",
    ], {"queue": queue, "record_executor_stale_rejection":
        lambda _current, receipt: {
            "status": "REJECTED_EXECUTOR_STALE_SEQUENCE",
            "executor_admission": None,
            "input_authority_admitted": False,
            "receipt": receipt,
        }})
    recovery = candidate_ns["recover_stale_executor_rejection"](
        rejection, identifier="plan-0", expected_sequence=11,
        controller_received_ns=123, latest=drained["latest"],
        incoming=late_queue, wait=lambda *_args, **_kwargs:
            (_ for _ in ()).throw(AssertionError("unexpected wait with queued fresh event")),
        final_action_admission={"status": "VALID"}, running_guard=Guard())
    if recovery["latest"]["sequence"] != 12:
        raise AssertionError("recovery did not consume the queued late observation")
    if late_queue.qsize() != 0:
        raise AssertionError("recovery left the triggering event queued")
    if recovery["admission"]["input_authority_admitted"] is not False:
        raise AssertionError("stale rejection created input authority")
    if recovery["guard"]["current_input_authority"] is not False:
        raise AssertionError("stale rejection restored action authority")

    return {
        "schema": "v39-final-empty-recovery-comparison-v1",
        "baseline_commit": base_commit,
        "candidate_commit": candidate_commit,
        "scenario": {"drained_latest_sequence": 11,
                     "pending_events_reported": False,
                     "late_sequence_left_queued": 12},
        "baseline": {"executor_rejected_stale_sequence": True,
                     "controller_recovery": False,
                     "result_reference": "v39_final_empty_check_race_a01_20261008/RESULT.json"},
        "candidate": {"exact_stale_rejection_helper_invoked": True,
                      "controller_recovery_and_discard_wiring_verified": controller_wiring,
                      "recovered_latest_sequence": recovery["latest"]["sequence"],
                      "recovery_batches": recovery["recovery"]["batches"],
                      "queued_late_event_consumed": late_queue.qsize() == 0,
                      "stale_candidate_authority": False,
                      "fresh_decision_required": recovery["guard"]["requires_new_decision"],
                      "retry_or_input_emitted": False},
        "decision": "PASS; candidate recovery closes the reproduced late-event liveness gap at the helper boundary",
        "scope": "Exact source-bound baseline drain and PR #8643 recovery helper under a deterministic queue schedule. The Executor rejection is supported by the retained current-main experiment. Recovery side-effect APIs are narrow test doubles. No full controller process, live game, GUI, model, OS input, physical release measurement, task effect, or integrated runtime result.",
    }


if __name__ == "__main__":
    result = run()
    (ROOT / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n",
                                      encoding="utf-8")
    print(json.dumps(result, indent=2))
