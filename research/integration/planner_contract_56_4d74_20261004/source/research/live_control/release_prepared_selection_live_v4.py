"""Execute and independently score one release-prepared visual candidate."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import threading
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PREREG = HERE / "release_prepared_selection_live_v4_prereg.json"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def persist_json_sync(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2) + "\n"); stream.flush(); os.fsync(stream.fileno())


def verify(plan):
    checks = {name: (REPO / name).is_file() and sha(REPO / name) == digest
              for name, digest in plan["source_sha256"].items()}
    checks.update({"output_absent": not (REPO / plan["output"]).exists(),
        "one_episode_no_retry": plan["episodes"] == 1 and plan["retry_limit"] == 0,
        "zero_model": plan["model_calls"] == 0,
        "thresholds": plan["thresholds_ms"] == {
            "focus_to_semantic_score_lte": 600,
            "admission_to_first_feedback_lte": 200,
            "admission_to_semantic_score_lte": 300}})
    return checks


def main():
    plan = read(PREREG); verification = verify(plan)
    if "--verify-only" in sys.argv:
        print(json.dumps({"passed": all(verification.values()), "checks": verification}, indent=2))
        return 0 if all(verification.values()) else 1
    if not all(verification.values()): raise RuntimeError(verification)
    if os.name == "nt" or not Path("/mnt/c").is_dir():
        raise RuntimeError("run frozen Unix/X11 allocation from WSL")
    from Xlib import X, display
    from executor_v13 import Executor
    from executor_v11 import program_sha256
    from release_event_socket_v2 import ReleaseEventSocket
    from release_aware_preparation_v1 import ReleaseAwarePreparation
    from inkscape_red_target_planner_v1 import prepare, validate
    from inkscape_selection_scorer_v2 import score
    from pointer_binding_readiness_v1 import evaluate as binding_readiness
    from first_action_boundary_v1 import first_boundary
    from release_recovery_backend_v1 import Backend, suite
    from unix_json_deadline import exchange

    root = REPO / plan["output"]; root.mkdir(parents=True, exist_ok=False)
    events = []; session = backend = executor = controller = sink = original = output = app_server = None
    delivery = ReleaseEventSocket(); report = {"allocation_id": plan["allocation_id"],
        "verification": verification, "scope": plan["scope"]}
    clients = {}; threads = []
    def emit(row):
        row["runtime_emit_ns"] = time.perf_counter_ns(); events.append(row); delivery.append(row)
    def exchange_record(request):
        record = {"request": request, "client_started_ns": time.perf_counter_ns()}
        reply = exchange(delivery.path, request, timeout=request["timeout"] + 1)
        record.update({"reply": reply, "client_returned_ns": time.perf_counter_ns(),
                       "response_bytes": len((json.dumps(reply) + "\n").encode())})
        return record
    def call(label, request):
        record = exchange_record(request)
        if label == "early":
            tracker = ReleaseAwarePreparation(identifier); tracker.ingest(record["reply"])
            record["preparation_started_ns"] = time.perf_counter_ns()
            tracker.begin(record["preparation_started_ns"])
            record["candidate"] = prepare(root / "001.png", plan["planner_roi"])
            record["preparation_completed_ns"] = time.perf_counter_ns()
            record["prepared_state"] = tracker.complete(
                record["candidate"], record["preparation_completed_ns"])
            resume = {"after": record["reply"]["cursor"], "events": ["terminal"],
                "timeout": 5, "action_id": identifier, "request_id": "early-resume"}
            record["terminal_exchange"] = exchange_record(resume)
            record["reconciled_state"] = tracker.ingest(
                record["terminal_exchange"]["reply"])
            record["validation_started_ns"] = time.perf_counter_ns()
            record["validation"] = validate(record["candidate"], root / "002.png")
            record["useful_ready_ns"] = time.perf_counter_ns()
        elif label == "terminal":
            record["preparation_started_ns"] = time.perf_counter_ns()
            record["candidate"] = prepare(root / "001.png", plan["planner_roi"])
            record["preparation_completed_ns"] = time.perf_counter_ns()
            record["validation_started_ns"] = time.perf_counter_ns()
            record["validation"] = validate(record["candidate"], root / "002.png")
            record["useful_ready_ns"] = time.perf_counter_ns()
        clients[label] = record
    try:
        with (root / "setup.txt").open("w") as diagnostics, contextlib.redirect_stdout(diagnostics):
            session = suite.Session()
            goal, output, app_server = suite.prepare(session, "inkscape", plan["seed"], "")
            backend = Backend(session, root, emit); controller = display.Display(session.name)
        backend.snapshot("initial", 0); executor = Executor(backend, emit)
        identifier = "release-prepared-pointer-click-04"
        step = {"op": "pointer_click", "x": plan["point"]["x"],
                "y": plan["point"]["y"], "duration_ms": plan["duration_ms"]}
        executor.submit(identifier, [step], backend.sequence,
                        time.perf_counter_ns() + 5_000_000_000)
        accepted = next(row for row in events if row["event"] == "accepted")
        root_window = controller.screen().root
        def down(): return bool(root_window.query_pointer().mask & X.Button1Mask)
        deadline = time.monotonic() + 2
        while not down() and time.monotonic() < deadline: time.sleep(.002)
        if not down(): raise RuntimeError("physical Button1 admission not observed")
        early_request = {"after": 0, "events": ["input_released", "terminal"],
            "timeout": 5, "action_id": identifier, "request_id": "early-release"}
        terminal_request = {"after": 0, "events": ["terminal"], "timeout": 5,
            "action_id": identifier, "request_id": "terminal-only"}
        for label, request in (("early", early_request), ("terminal", terminal_request)):
            thread = threading.Thread(target=call, args=(label, request)); threads.append(thread); thread.start()
        if not delivery.wait_requests(2): raise RuntimeError("both client reads must be waiting")
        server_receipts = delivery.request_receipts()
        if (len(server_receipts) != 2 or
                {row["request_id"] for row in server_receipts} !=
                {"early-release", "terminal-only"}):
            raise RuntimeError("exact two server request registrations required")
        receipt_artifact = {"schema": "server-request-registration-v1",
            "snapshot_ns": time.perf_counter_ns(), "requests": server_receipts}
        receipt_path = root / "server-requests-before-focus.json"
        persist_json_sync(receipt_path, receipt_artifact)
        receipt_sha256 = sha(receipt_path)
        original = controller.get_input_focus().focus
        sink = root_window.create_window(0, 0, 100, 80, 0,
            controller.screen().root_depth, override_redirect=True); sink.map()
        focus_request_ns = time.perf_counter_ns()
        sink.set_input_focus(X.RevertToParent, X.CurrentTime); controller.sync()
        for thread in threads: thread.join(5)
        if any(thread.is_alive() for thread in threads): raise RuntimeError("client wait timed out")
        early = clients["early"]; terminal_client = clients["terminal"]
        early_boundary = early["reply"]["records"][-1]
        terminal_boundary = terminal_client["reply"]["records"][-1]
        original.set_input_focus(X.RevertToParent, X.CurrentTime); controller.sync()
        terminal = next(row for row in events if row.get("event") == "terminal")
        observations = [row for row in events if row.get("event") == "observation" and
                        row.get("id") == identifier]
        binding_attempts = []
        admission_observation = None
        for attempt in range(plan["binding_attempt_limit"]):
            backend.snapshot(f"prepared-pre-admission-{attempt}", 0)
            admission_observation = events[-1]
            receipt = binding_readiness(admission_observation, time.perf_counter_ns())
            binding_attempts.append(receipt)
            if receipt["status"] == "READY": break
            time.sleep(plan["binding_retry_ms"] / 1000)
        if binding_attempts[-1]["status"] != "READY":
            raise RuntimeError("coherent pointer binding unavailable")
        admission_image = root / Path(admission_observation["image"]).name
        admission_validation_started_ns = time.perf_counter_ns()
        admission_validation = validate(early["candidate"], admission_image)
        admission_validation_completed_ns = time.perf_counter_ns()
        pre_selection_score = score(early["candidate"], admission_image)
        selection_id = "prepared-red-selection-04"
        selection_program = [early["candidate"]["action"], {"op": "observe"}]
        selection_submit_ns = time.perf_counter_ns()
        executor.submit(selection_id, selection_program,
                        backend.sequence, time.perf_counter_ns() + 5_000_000_000)
        selection_accepted = next(row for row in events
                                  if row.get("event") == "accepted" and
                                  row.get("id") == selection_id)
        deadline = time.monotonic() + 3
        semantic_scores = []; seen_feedback = set(); selection_terminal = None
        semantic_observation = semantic_score = None
        while semantic_score is None and time.monotonic() < deadline:
            for row in list(events):
                if row.get("id") != selection_id: continue
                if row.get("event") == "observation" and row["sequence"] not in seen_feedback:
                    seen_feedback.add(row["sequence"]); detected_ns = time.perf_counter_ns()
                    result = score(early["candidate"], Path(row["image"]))
                    scored_ns = time.perf_counter_ns()
                    semantic_scores.append({"observation": row, "detected_ns": detected_ns,
                                            "score": result, "scored_ns": scored_ns})
                    if result["success"]:
                        semantic_observation, semantic_score = row, result
                        semantic_score_completed_ns = scored_ns; break
                elif row.get("event") == "terminal": selection_terminal = row
            if semantic_score is None:
                if selection_terminal is not None: break
                time.sleep(.0005)
        if not semantic_scores: raise RuntimeError("selection boundary timeout")
        selection_observation = semantic_scores[0]["observation"]
        first_feedback_received_ns = semantic_scores[0]["detected_ns"]
        selection_boundary = first_boundary(events, selection_id)
        if semantic_score is None: raise RuntimeError("terminal before semantic success")
        while selection_terminal is None and time.monotonic() < deadline:
            selection_terminal = next((row for row in events
                if row.get("event") == "terminal" and row.get("id") == selection_id), None)
            if selection_terminal is None: time.sleep(.0005)
        if selection_terminal is None: raise RuntimeError("selection terminal missing")
        metrics = {
            "focus_to_runtime_release_ms":
                (early_boundary["owner_release"]["verified_ns"] - focus_request_ns) / 1e6,
            "focus_to_early_client_ms": (early["client_returned_ns"] - focus_request_ns) / 1e6,
            "focus_to_terminal_client_ms":
                (terminal_client["client_returned_ns"] - focus_request_ns) / 1e6,
            "early_client_wait_advantage_ms":
                (terminal_client["client_returned_ns"] - early["client_returned_ns"]) / 1e6,
            "focus_to_early_candidate_ready_ms":
                (early["preparation_completed_ns"] - focus_request_ns) / 1e6,
            "focus_to_terminal_candidate_ready_ms":
                (terminal_client["preparation_completed_ns"] - focus_request_ns) / 1e6,
            "focus_to_early_useful_ready_ms":
                (early["useful_ready_ns"] - focus_request_ns) / 1e6,
            "focus_to_terminal_useful_ready_ms":
                (terminal_client["useful_ready_ns"] - focus_request_ns) / 1e6,
            "useful_ready_advantage_ms":
                (terminal_client["useful_ready_ns"] - early["useful_ready_ns"]) / 1e6,
            "early_preparation_overlap_before_terminal_ms":
                early["reconciled_state"]["overlap_before_terminal_ns"] / 1e6,
            "runtime_release_to_terminal_ms":
                (terminal["terminal_ns"] - early_boundary["owner_release"]["verified_ns"]) / 1e6,
            "focus_to_selection_admission_ms":
                (selection_accepted["accepted_ns"] - focus_request_ns) / 1e6,
            "selection_admission_to_first_feedback_capture_ms":
                (selection_observation["capture_ns"] - selection_accepted["accepted_ns"]) / 1e6,
            "selection_admission_to_first_feedback_received_ms":
                (first_feedback_received_ns - selection_accepted["accepted_ns"]) / 1e6,
            "selection_admission_to_semantic_score_ms":
                (semantic_score_completed_ns - selection_accepted["accepted_ns"]) / 1e6,
            "selection_admission_to_first_useful_feedback_capture_ms":
                (semantic_observation["capture_ns"] - selection_accepted["accepted_ns"]) / 1e6,
            "focus_to_semantic_score_ms":
                (semantic_score_completed_ns - focus_request_ns) / 1e6,
            "semantic_score_to_terminal_ms":
                (selection_terminal["terminal_ns"] - semantic_score_completed_ns) / 1e6,
        }
        checks = {
            "same_runtime_stream": early_boundary == next(row for row in events
                if row.get("event") == "input_released") and terminal_boundary == terminal,
            "both_waiting_before_focus":
                receipt_artifact["snapshot_ns"] < focus_request_ns and
                all(row["received_ns"] < receipt_artifact["snapshot_ns"]
                    for row in server_receipts),
            "early_boundary_is_verified_release": early_boundary["event"] == "input_released" and
                early_boundary["owner_release"]["verified"] is True and
                early_boundary["owner_release"]["buttons_down"] == [],
            "early_candidate_before_terminal":
                early["preparation_completed_ns"] < terminal["terminal_ns"] and
                early["prepared_state"]["state"] == "PREPARED_AWAITING_TERMINAL",
            "terminal_client_boundary": terminal_boundary["event"] == "terminal" and
                terminal_boundary["status"] == "needs_decision",
            "early_terminal_reconciled_before_validation":
                early["reconciled_state"]["state"] ==
                "PREPARED_REQUIRES_FRESH_ACTION_VALIDITY" and
                early["terminal_exchange"]["reply"]["records"][-1] == terminal_boundary and
                early["validation_started_ns"] >=
                early["terminal_exchange"]["client_returned_ns"],
            "lease_and_cause_match": early_boundary["intent_token"] == accepted["intent_token"] and
                terminal_boundary["interruption"]["record"] == early_boundary["owner_release"],
            "real_post_release_observation": len(observations) == 1 and
                any(row.get("event") == "post_release_observation_complete" for row in events),
            "same_visual_candidate": early["candidate"] == terminal_client["candidate"] and
                early["candidate"]["target"]["center"] == [619, 390],
            "fresh_target_validated": early["validation"] == terminal_client["validation"] and
                early["validation"]["status"] == "VALID_CURRENT" and
                early["validation"]["grants_input_authority"] is False,
            "fresh_admission_validation": admission_validation["status"] ==
                "VALID_CURRENT" and admission_validation["action"] ==
                early["candidate"]["action"] and
                binding_attempts[-1]["may_submit_pointer_input"] is True and
                admission_validation_started_ns >= early["useful_ready_ns"] and
                admission_validation_completed_ns <= selection_submit_ns,
            "prepared_candidate_bound_to_acceptance": len([row for row in events
                if row.get("event") == "accepted"]) == 2 and
                selection_accepted["steps"] == len(selection_program) and
                selection_accepted["program_sha256"] == program_sha256(selection_program) and
                selection_accepted["accepted_ns"] >= admission_validation_completed_ns,
            "first_feedback_distinct_from_first_useful": len(semantic_scores) >= 2 and
                semantic_scores[0]["score"]["success"] is False and
                semantic_scores[-1]["score"]["success"] is True and
                selection_observation != semantic_observation,
            "independent_visible_selection": pre_selection_score["success"] is False and
                semantic_score["success"] is True and
                semantic_score["reason"] == "target_identity_and_selection_handles_visible",
            "selection_terminal_and_release": selection_terminal["status"] == "completed" and
                selection_terminal["steps_completed"] == 2 and
                selection_terminal["release"]["verified"] is True and
                selection_terminal["release"]["keys_down"] == [] and
                selection_terminal["release"]["buttons_down"] == [],
            "round_trip_accounting": early["terminal_exchange"]["request"]["request_id"] ==
                "early-resume",
            "focus_to_semantic_score_threshold":
                metrics["focus_to_semantic_score_ms"] <= 600,
            "admission_to_first_feedback_threshold":
                metrics["selection_admission_to_first_feedback_received_ms"] <= 200,
            "admission_to_semantic_score_threshold":
                metrics["selection_admission_to_semantic_score_ms"] <= 300,
            "zero_model_retry_cancel": plan["model_calls"] == plan["retry_limit"] == 0 and
                not any(row.get("event") == "cancel_requested" for row in events),
        }
        report.update({"passed": all(checks.values()), "checks": checks, "goal": goal,
            "accepted": accepted, "focus_request_ns": focus_request_ns,
            "server_request_receipts": server_receipts,
            "server_request_receipt_artifact": str(receipt_path),
            "server_request_receipt_sha256": receipt_sha256,
            "clients": clients,
            "terminal": terminal, "post_release_observations": observations,
            "admission_validation": admission_validation,
            "binding_attempts": binding_attempts,
            "admission_observation": admission_observation,
            "admission_validation_started_ns": admission_validation_started_ns,
            "admission_validation_completed_ns": admission_validation_completed_ns,
            "pre_selection_score": pre_selection_score,
            "selection_submit_ns": selection_submit_ns,
            "selection_accepted": selection_accepted,
            "selection_program": selection_program,
            "selection_observation": selection_observation,
            "selection_boundary": selection_boundary,
            "first_feedback_received_ns": first_feedback_received_ns,
            "semantic_scores": semantic_scores,
            "semantic_observation": semantic_observation,
            "semantic_score": semantic_score,
            "semantic_score_completed_ns": semantic_score_completed_ns,
            "selection_terminal": selection_terminal,
            "metrics_ms": metrics, "early_exchanges": 2, "terminal_only_exchanges": 1,
            "model_calls": 0, "retry_count": 0})
    finally:
        for thread in threads:
            if thread.is_alive(): thread.join(1)
        if original is not None:
            try: original.set_input_focus(X.RevertToParent, X.CurrentTime); controller.sync()
            except Exception: pass
        if sink is not None:
            try: sink.destroy(); controller.sync()
            except Exception: pass
        if executor is not None: executor.close()
        if backend is not None:
            try: backend.close()
            finally: (root / "owner-events.json").write_text(
                json.dumps(backend.owner.records, indent=2) + "\n")
        if controller is not None: controller.close()
        if output is not None and output.exists(): shutil.copy2(output, root / output.name)
        if app_server is not None: app_server.shutdown(); app_server.server_close()
        if session is not None: session.close(); shutil.rmtree(session.tmp)
        delivery.close()
        (root / "events.json").write_text(json.dumps(events, indent=2) + "\n")
        (root / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report.get("passed"), "checks": report.get("checks"),
                      "metrics_ms": report.get("metrics_ms")}, indent=2))
    return 0 if report.get("passed") else 1


if __name__ == "__main__": raise SystemExit(main())

