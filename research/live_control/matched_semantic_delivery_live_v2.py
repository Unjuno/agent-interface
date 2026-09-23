"""Matched live comparison of path scoring and pre-artifact frame feedback."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import sys
import threading
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PREREG = HERE / "matched_semantic_delivery_live_v2_prereg.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def persist(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2)+"\n")
        stream.flush(); os.fsync(stream.fileno())


def verify(plan):
    checks = {name: (REPO/name).is_file() and sha(REPO/name) == digest
              for name, digest in plan["source_sha256"].items()}
    checks.update({
        "output_absent": not (REPO/plan["output"]).exists(),
        "one_allocation_no_retry": plan["allocations"] == 1 and plan["retry_limit"] == 0,
        "fixed_order": plan["order"] == ["path", "frame", "frame", "path",
                                                "frame", "path", "path", "frame"],
        "same_seed": type(plan["seed"]) is int,
        "zero_model": plan["model_calls"] == 0,
        "thresholds": plan["thresholds_ms"] == {
            "frame_semantic_ready_median_lte": 260,
            "path_semantic_ready_median_lte": 400,
            "median_advantage_gte": 25,
            "frame_first_feedback_lte": 200,
            "path_first_feedback_lte": 260,
            "probe_compute_lte": 5,
        },
    })
    return checks


def run_arm(plan, root, ordinal, mode):
    from executor_v13 import Executor
    from executor_v11 import program_sha256
    from inkscape_red_target_planner_v1 import prepare, validate
    from inkscape_selection_scorer_v2 import score
    from pointer_binding_readiness_v1 import evaluate as binding_readiness
    from release_event_socket_v3 import ReleaseEventSocket
    from release_recovery_backend_v1 import Backend as PathBackend, suite
    from semantic_probe_backend_v1 import Backend as FrameBackend
    from unix_json_deadline import exchange

    arm = root/f"arm-{ordinal+1:02d}-{mode}"
    arm.mkdir()
    events = []
    delivery = ReleaseEventSocket()
    session = backend = executor = output = app_server = None
    client_thread = None
    report = {"ordinal": ordinal, "mode": mode, "seed": plan["seed"]}
    def emit(row):
        row["runtime_emit_ns"] = time.perf_counter_ns()
        events.append(row); delivery.append(row)
    def exchange_record(request):
        record = {"request": request, "client_started_ns": time.perf_counter_ns()}
        reply = exchange(delivery.path, request, timeout=request["timeout"]+1)
        record.update({"reply": reply, "client_returned_ns": time.perf_counter_ns(),
                       "response_bytes": len((json.dumps(reply)+"\n").encode())})
        return record
    try:
        with (arm/"setup.txt").open("w") as diagnostics, contextlib.redirect_stdout(diagnostics):
            session = suite.Session()
            goal, output, app_server = suite.prepare(session, "inkscape", plan["seed"], "")
            backend_class = FrameBackend if mode == "frame" else PathBackend
            backend = backend_class(session, arm, emit)
        backend.snapshot("initial", 0)
        candidate = prepare(arm/"001.png", plan["planner_roi"])
        binding_attempts = []
        admission_observation = None
        for attempt in range(plan["binding_attempt_limit"]):
            backend.snapshot(f"admission-{attempt}", 0)
            admission_observation = events[-1]
            receipt = binding_readiness(admission_observation, time.perf_counter_ns())
            binding_attempts.append(receipt)
            if receipt["status"] == "READY":
                break
            time.sleep(plan["binding_retry_ms"]/1000)
        if binding_attempts[-1]["status"] != "READY":
            raise RuntimeError("coherent pointer binding unavailable")
        admission_path = arm/Path(admission_observation["image"]).name
        validation = validate(candidate, admission_path)
        pre_score = score(candidate, admission_path)
        action_id = f"matched-selection-{ordinal+1:02d}-{mode}"
        program = [candidate["action"], {"op": "observe"}]
        registration = None
        if mode == "frame":
            registration = backend.register_semantic_probe(action_id, candidate)
        client = {"feedback": [], "exchanges": []}
        def receive():
            after = 0
            for index in range(2):
                requested = ["semantic_probe", "terminal"] if mode == "frame" else [
                    "observation", "terminal"]
                request = {"after": after, "events": requested, "timeout": 3,
                           "action_id": action_id,
                           "request_id": f"matched-{ordinal+1:02d}-{mode}-{index}"}
                exchange_row = exchange_record(request)
                client["exchanges"].append(exchange_row)
                boundary = exchange_row["reply"]["records"][-1]
                if boundary["event"] == "terminal":
                    client["terminal_before_success"] = boundary
                    break
                score_started_ns = time.perf_counter_ns()
                result = (boundary["score"] if mode == "frame" else
                          score(candidate, Path(boundary["image"])))
                score_completed_ns = time.perf_counter_ns()
                client["feedback"].append({"boundary": boundary, "score": result,
                    "score_started_ns": score_started_ns,
                    "score_completed_ns": score_completed_ns,
                    "semantic_ready_ns": (exchange_row["client_returned_ns"] if mode == "frame"
                                          else score_completed_ns)})
                if result["success"]:
                    break
                after = exchange_row["reply"]["cursor"]
            client["completed_ns"] = time.perf_counter_ns()
        request_count = len(delivery.request_receipts())
        client_thread = threading.Thread(target=receive)
        client_thread.start()
        if not delivery.wait_requests(request_count+1):
            raise RuntimeError("client must register before submit")
        client_registered_ns = delivery.request_receipts()[-1]["received_ns"]
        executor = Executor(backend, emit)
        submit_ns = time.perf_counter_ns()
        executor.submit(action_id, program, backend.sequence,
                        time.perf_counter_ns()+5_000_000_000)
        accepted = next(row for row in events if row.get("event") == "accepted" and
                        row.get("id") == action_id)
        client_thread.join(4)
        if client_thread.is_alive():
            raise RuntimeError("semantic client timed out")
        if (len(client["feedback"]) != 2 or
                client["feedback"][0]["score"]["success"] is not False or
                client["feedback"][1]["score"]["success"] is not True):
            raise RuntimeError("exact false then true feedback required")
        deadline = time.monotonic()+3
        terminal = None
        while terminal is None and time.monotonic() < deadline:
            terminal = next((row for row in events if row.get("event") == "terminal" and
                             row.get("id") == action_id), None)
            if terminal is None:
                time.sleep(.0005)
        if terminal is None:
            raise RuntimeError("terminal missing")
        observations = [row for row in events if row.get("event") == "observation" and
                        row.get("id") == action_id]
        useful_feedback = client["feedback"][-1]
        useful_sequence = useful_feedback["boundary"]["sequence"]
        useful_observation = next(row for row in observations
                                  if row["sequence"] == useful_sequence)
        useful_path = arm/Path(useful_observation["image"]).name
        independent_score = score(candidate, useful_path)
        reconciliations = [row for row in events
                           if row.get("event") == "semantic_probe_reconciled" and
                           row.get("id") == action_id]
        metrics = {
            "admission_to_first_capture_ms":
                (observations[0]["capture_ns"]-accepted["accepted_ns"])/1e6,
            "admission_to_first_feedback_ms":
                (client["feedback"][0]["semantic_ready_ns"]-accepted["accepted_ns"])/1e6,
            "admission_to_useful_capture_ms":
                (useful_observation["capture_ns"]-accepted["accepted_ns"])/1e6,
            "admission_to_semantic_ready_ms":
                (useful_feedback["semantic_ready_ns"]-accepted["accepted_ns"])/1e6,
            "capture_to_semantic_ready_ms":
                (useful_feedback["semantic_ready_ns"]-useful_observation["capture_ns"])/1e6,
            "semantic_ready_to_terminal_ms":
                (terminal["terminal_ns"]-useful_feedback["semantic_ready_ns"])/1e6,
            "client_exchanges": len(client["exchanges"]),
            "response_bytes": sum(row["response_bytes"] for row in client["exchanges"]),
        }
        if mode == "frame":
            metrics.update({
                "first_probe_compute_ms": (client["feedback"][0]["boundary"]
                    ["probe_completed_ns"]-client["feedback"][0]["boundary"]
                    ["probe_started_ns"])/1e6,
                "useful_probe_compute_ms": (useful_feedback["boundary"]["probe_completed_ns"]-
                                            useful_feedback["boundary"]["probe_started_ns"])/1e6,
                "semantic_ready_to_image_ready_ms":
                    (next(row for row in reconciliations if row["sequence"] == useful_sequence)
                     ["image_ready_ns"]-useful_feedback["semantic_ready_ns"])/1e6,
            })
        else:
            metrics["first_path_score_ms"] = (client["feedback"][0]["score_completed_ns"]-
                                                client["feedback"][0]["score_started_ns"])/1e6
            metrics["useful_path_score_ms"] = (useful_feedback["score_completed_ns"]-
                                                 useful_feedback["score_started_ns"])/1e6
        checks = {
            "coherent_valid_admission": binding_attempts[-1]["status"] == "READY" and
                validation["status"] == "VALID_CURRENT" and pre_score["success"] is False,
            "client_registered_before_submit": client_registered_ns <= submit_ns,
            "program_attested": accepted["steps"] == 2 and
                accepted["program_sha256"] == program_sha256(program),
            "false_then_true": len(client["feedback"]) == 2 and
                client["feedback"][0]["score"]["success"] is False and
                useful_feedback["score"]["success"] is True,
            "independent_success": independent_score["success"] is True,
            "completed_empty_release": terminal["status"] == "completed" and
                terminal["steps_completed"] == 2 and terminal["release"]["verified"] is True and
                terminal["release"]["keys_down"] == [] and terminal["release"]["buttons_down"] == [],
            "first_feedback_limit": metrics["admission_to_first_feedback_ms"] <=
                plan["thresholds_ms"][mode + "_first_feedback_lte"],
            "two_client_exchanges": metrics["client_exchanges"] == 2,
        }
        if mode == "frame":
            checks.update({
                "registered_no_authority": registration["status"] ==
                    "REGISTERED_NO_AUTHORITY" and registration["grants_input_authority"] is False,
                "probe_compute_limit": max(metrics["first_probe_compute_ms"],
                    metrics["useful_probe_compute_ms"]) <=
                    plan["thresholds_ms"]["probe_compute_lte"],
                "exact_reconciliation": len(reconciliations) == 2 and
                    all(row["reconciliation"]["matches"] for row in reconciliations),
                "pre_artifact_delivery": metrics["semantic_ready_to_image_ready_ms"] > 0,
            })
        report.update({"passed": all(checks.values()), "checks": checks, "goal": goal,
            "candidate": candidate, "binding_attempts": binding_attempts,
            "admission_observation": admission_observation, "validation": validation,
            "pre_score": pre_score, "action_id": action_id, "program": program,
            "registration": registration, "client_registered_ns": client_registered_ns,
            "submit_ns": submit_ns, "accepted": accepted, "client": client,
            "observations": observations, "useful_observation": useful_observation,
            "independent_score": independent_score, "reconciliations": reconciliations,
            "terminal": terminal, "metrics_ms": metrics, "model_calls": 0})
    finally:
        if client_thread is not None and client_thread.is_alive():
            client_thread.join(1)
        if executor is not None:
            executor.close()
        if backend is not None:
            try:
                backend.close()
            finally:
                (arm/"owner-events.json").write_text(
                    json.dumps(backend.owner.records, indent=2)+"\n")
        if output is not None and output.exists():
            shutil.copy2(output, arm/output.name)
        if app_server is not None:
            app_server.shutdown(); app_server.server_close()
        if session is not None:
            session.close(); shutil.rmtree(session.tmp)
        delivery.close()
        (arm/"events.json").write_text(json.dumps(events, indent=2)+"\n")
        (arm/"report.json").write_text(json.dumps(report, indent=2)+"\n")
    return report


def main():
    plan = read(PREREG)
    verification = verify(plan)
    if "--verify-only" in sys.argv:
        print(json.dumps({"passed": all(verification.values()),
                          "checks": verification}, indent=2))
        return 0 if all(verification.values()) else 1
    if not all(verification.values()):
        raise RuntimeError(verification)
    if os.name == "nt" or not Path("/mnt/c").is_dir():
        raise RuntimeError("run frozen Unix/X11 allocation from WSL")
    root = REPO/plan["output"]
    root.mkdir(parents=True, exist_ok=False)
    arms = []
    for ordinal, mode in enumerate(plan["order"]):
        arms.append(run_arm(plan, root, ordinal, mode))
    samples = {mode: [arm["metrics_ms"]["admission_to_semantic_ready_ms"]
                      for arm in arms if arm["mode"] == mode]
               for mode in ("path", "frame")}
    medians = {mode: statistics.median(values) for mode, values in samples.items()}
    metrics = {"path_semantic_ready_median_ms": medians["path"],
               "frame_semantic_ready_median_ms": medians["frame"],
               "median_advantage_ms": medians["path"]-medians["frame"],
               "median_ratio": medians["frame"]/medians["path"],
               "samples_ms": samples}
    checks = {
        "all_arms_pass": all(arm["passed"] for arm in arms),
        "exact_order": [arm["mode"] for arm in arms] == plan["order"],
        "same_candidate": all(arm["candidate"] == arms[0]["candidate"] for arm in arms),
        "same_program": all(arm["program"] == arms[0]["program"] for arm in arms),
        "balanced": len(samples["path"]) == len(samples["frame"]) == 4,
        "frame_median_limit": medians["frame"] <=
            plan["thresholds_ms"]["frame_semantic_ready_median_lte"],
        "path_median_limit": medians["path"] <=
            plan["thresholds_ms"]["path_semantic_ready_median_lte"],
        "median_advantage": metrics["median_advantage_ms"] >=
            plan["thresholds_ms"]["median_advantage_gte"],
        "zero_model": all(arm["model_calls"] == 0 for arm in arms),
    }
    report = {"schema": "matched-semantic-delivery-live-v2",
              "allocation_id": plan["allocation_id"], "verification": verification,
              "passed": all(checks.values()), "checks": checks, "arms": arms,
              "metrics_ms": metrics, "model_calls": 0, "scope": plan["scope"]}
    persist(root/"report.json", report)
    print(json.dumps({"passed": report["passed"], "checks": checks,
                      "metrics_ms": metrics, "scope": plan["scope"]}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
