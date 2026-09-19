"""Frozen live translation and resize test for a surface-relative predicate."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import parse_qs
import shutil
import sys
import threading
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PREREG = HERE/"target_relative_semantic_probe_live_v1_prereg.json"


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def persist(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2)+"\n"); stream.flush(); os.fsync(stream.fileno())


def verify(plan):
    checks = {name: (REPO/name).is_file() and sha(REPO/name) == digest
              for name, digest in plan["source_sha256"].items()}
    checks.update({"output_absent": not (REPO/plan["output"]).exists(),
        "one_allocation_no_retry": plan["allocations"] == 1 and plan["retry_limit"] == 0,
        "zero_model": plan["model_calls"] == 0, "seed": plan["seed"] == 208,
        "geometry_changes": plan["move_delta"] == [21, 28] and plan["resize_width_delta"] == -120,
        "relative_box": plan["box_in_frame"] == [5, 160, 320, 205],
        "thresholds": plan["thresholds_ms"] == {"first_feedback_lte": 300,
            "useful_feedback_lte": 650, "probe_compute_lte": 5}})
    return checks


def wait_terminal(events, identifier, timeout=7):
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        row = next((item for item in events if item.get("event") == "terminal"
                    and item.get("id") == identifier), None)
        if row is not None: return row
        time.sleep(.001)
    raise RuntimeError("terminal missing: "+identifier)


def main():
    plan = read(PREREG); verification = verify(plan)
    if "--verify-only" in sys.argv:
        print(json.dumps({"passed": all(verification.values()), "checks": verification}, indent=2))
        return 0 if all(verification.values()) else 1
    if not all(verification.values()): raise RuntimeError(verification)
    if os.name == "nt" or not Path("/mnt/c").is_dir():
        raise RuntimeError("run frozen Unix/X11 allocation from WSL")

    from executor_v13 import Executor
    from executor_v11 import program_sha256
    from exact_crop_semantic_probe_v1 import score_path as score_fixed
    from release_event_socket_v3 import ReleaseEventSocket
    from semantic_probe_backend_v3 import Backend, suite
    from unix_json_deadline import exchange

    root = REPO/plan["output"]; root.mkdir(parents=True, exist_ok=False)
    events = []; clients = {}; threads = []; delivery = ReleaseEventSocket()
    session = backend = executor = controller = output = app_server = None

    def emit(row):
        row["runtime_emit_ns"] = time.perf_counter_ns(); events.append(row); delivery.append(row)

    def exchange_record(request):
        row = {"request": request, "client_started_ns": time.perf_counter_ns()}
        reply = exchange(delivery.path, request, timeout=request["timeout"]+1)
        row.update({"reply": reply, "client_returned_ns": time.perf_counter_ns(),
                    "response_bytes": len((json.dumps(reply)+"\n").encode())})
        return row

    def semantic_client(label, action_id, maximum, wanted):
        result = {"feedback": [], "exchanges": []}; after = 0
        for ordinal in range(maximum):
            request = {"after": after, "events": ["semantic_probe", "terminal"],
                "timeout": 4, "action_id": action_id, "request_id": f"{label}-{ordinal}"}
            exchange_row = exchange_record(request); result["exchanges"].append(exchange_row)
            boundary = exchange_row["reply"]["records"][-1]
            if boundary["event"] == "terminal": break
            result["feedback"].append(boundary)
            if boundary["score"]["success"] is wanted: break
            after = exchange_row["reply"]["cursor"]
        result["completed_ns"] = time.perf_counter_ns(); clients[label] = result

    def submit(identifier, program):
        submitted_ns = time.perf_counter_ns()
        executor.submit(identifier, program, backend.sequence,
                        time.perf_counter_ns()+8_000_000_000)
        accepted = next(row for row in events if row.get("event") == "accepted"
                        and row.get("id") == identifier)
        return {"id": identifier, "program": program, "submitted_ns": submitted_ns,
                "accepted": accepted, "terminal": wait_terminal(events, identifier)}

    def wait_binding(predicate, message):
        deadline = time.monotonic()+2; value = backend.binding()
        while not predicate(value) and time.monotonic() < deadline:
            time.sleep(.01); value = backend.binding()
        if not predicate(value): raise RuntimeError(message)
        return value

    report = {"schema": "target-relative-semantic-probe-live-v1",
              "allocation_id": plan["allocation_id"], "verification": verification,
              "scope": plan["scope"]}
    original_geometry = moved_geometry = resized_geometry = None
    try:
        from Xlib import display
        with (root/"setup.txt").open("w") as diagnostics, contextlib.redirect_stdout(diagnostics):
            session = suite.Session()
            goal, output, app_server = suite.prepare(
                session, "chromium", plan["seed"], plan["chromium"])
            backend = Backend(session, root, emit); controller = display.Display(session.name)
        executor = Executor(backend, emit); backend.snapshot("initial", 0)
        navigate = submit("relative-navigate-01", [
            {"op": "chord", "modifier": "Control_L", "key": "l"},
            {"op": "text", "text": goal["url"]}, {"op": "key", "key": "Return"},
            {"op": "wait_title", "contains": "AI FORM READY", "timeout_ms": 1500}])
        fill = submit("relative-fill-01", [
            {"op": "pointer_click", "x": 180, "y": 243, "duration_ms": 80},
            {"op": "chord", "modifier": "Control_L", "key": "a"},
            {"op": "text", "text": goal["token"]}, {"op": "observe"}])
        backend.snapshot("relative-source", 0); source_observation = events[-1]
        source_binding = source_observation["pointer_binding"]
        if source_binding is None: raise RuntimeError("coherent source binding required")
        original_geometry = list(source_binding["geometry"])
        contract = {"schema": "target-relative-rgb-crop-semantic-probe-v1",
            "probe_id": "chromium_submission_relative", "target_reference": "submission_heading",
            "coordinate_frame": "window_content", "source_surface": source_binding["surface"],
            "source_geometry": original_geometry, "box_in_frame": plan["box_in_frame"],
            "expected_crop_sha256": plan["expected_crop_sha256"],
            "success_reason": "submission_title_exactly_visible",
            "allowed_transformations": ["window_translation"], "grants_input_authority": False}

        window = controller.create_resource_object("window", source_binding["surface"])
        window.configure(x=original_geometry[0]+plan["move_delta"][0],
                         y=original_geometry[1]+plan["move_delta"][1]); controller.sync()
        moved_binding = wait_binding(lambda value: value.get("surface") == source_binding["surface"]
            and value.get("geometry", [None, None])[:2] == [original_geometry[0]+21,
                                                             original_geometry[1]+28],
            "surface translation missing")
        moved_geometry = list(moved_binding["geometry"])
        moved_event = {"event": "test_surface_moved", "before": source_binding,
                       "after": moved_binding, "grants_input_authority": False,
                       "runtime_emit_ns": time.perf_counter_ns()}
        events.append(moved_event); delivery.append(moved_event)
        delta = [moved_geometry[0]-original_geometry[0], moved_geometry[1]-original_geometry[1]]

        positive_id = "relative-translated-submit-01"
        registration = backend.register_semantic_probe(positive_id, contract)
        request_count = len(delivery.request_receipts())
        positive_thread = threading.Thread(target=semantic_client,
            args=("positive", positive_id, plan["max_positive_exchanges"], True))
        threads.append(positive_thread); positive_thread.start()
        if not delivery.wait_requests(request_count+1): raise RuntimeError("positive client missing")
        positive_registered_ns = delivery.request_receipts()[-1]["received_ns"]
        submit_action = submit(positive_id, [
            {"op": "pointer_click", "x": 270+delta[0], "y": 243+delta[1], "duration_ms": 80},
            {"op": "wait_title", "contains": "AI FORM SAVED", "timeout_ms": 1500},
            {"op": "observe"}])
        positive_thread.join(4)
        if positive_thread.is_alive(): raise RuntimeError("positive client timed out")
        positive = clients["positive"]
        useful = next((row for row in positive["feedback"] if row["score"]["success"]), None)
        if useful is None: raise RuntimeError("translated success missing")
        useful_observation = next(row for row in events if row.get("event") == "observation"
                                  and row.get("sequence") == useful["sequence"])
        useful_image = root/Path(useful_observation["image"]).name
        fixed_contract = {"schema": "exact-rgb-crop-semantic-probe-v1",
            "probe_id": "fixed_control", "box": [15, 170, 330, 215],
            "expected_crop_sha256": plan["expected_crop_sha256"],
            "success_reason": "submission_title_exactly_visible", "grants_input_authority": False}
        fixed_control = score_fixed(fixed_contract, useful_image)

        window.configure(width=moved_geometry[2]+plan["resize_width_delta"]); controller.sync()
        resized_binding = wait_binding(lambda value: value.get("surface") == source_binding["surface"]
            and value.get("geometry", [0,0,0])[2] == moved_geometry[2]-120,
            "surface resize missing")
        resized_geometry = list(resized_binding["geometry"])
        resize_event = {"event": "test_surface_resized", "before": moved_binding,
                        "after": resized_binding, "grants_input_authority": False,
                        "runtime_emit_ns": time.perf_counter_ns()}
        events.append(resize_event); delivery.append(resize_event)
        resize_id = "relative-resize-refusal-01"
        resize_registration = backend.register_semantic_probe(resize_id, contract)
        request_count = len(delivery.request_receipts())
        resize_thread = threading.Thread(target=semantic_client,
            args=("resize", resize_id, 1, False))
        threads.append(resize_thread); resize_thread.start()
        if not delivery.wait_requests(request_count+1): raise RuntimeError("resize client missing")
        resize_registered_ns = delivery.request_receipts()[-1]["received_ns"]
        resize_action = submit(resize_id, [{"op": "observe"}])
        resize_thread.join(4)
        if resize_thread.is_alive(): raise RuntimeError("resize client timed out")
        resize_probe = clients["resize"]["feedback"][0]

        useful_index = positive["feedback"].index(useful)
        first_received_ns = positive["exchanges"][0]["client_returned_ns"]
        useful_received_ns = positive["exchanges"][useful_index]["client_returned_ns"]
        reconciliations = [row for row in events if row.get("event") == "semantic_probe_reconciled"]
        useful_reconciliation = next(row for row in reconciliations if row["sequence"] == useful["sequence"])
        actual = parse_qs(output.read_text()) if output.exists() else {}
        metrics = {"admission_to_first_feedback_ms":
                (first_received_ns-submit_action["accepted"]["accepted_ns"])/1e6,
            "admission_to_useful_feedback_ms":
                (useful_received_ns-submit_action["accepted"]["accepted_ns"])/1e6,
            "useful_probe_compute_ms":
                (useful["probe_completed_ns"]-useful["probe_started_ns"])/1e6,
            "useful_probe_to_image_ready_ms":
                (useful_reconciliation["image_ready_ns"]-useful["probe_completed_ns"])/1e6,
            "useful_client_to_terminal_ms":
                (submit_action["terminal"]["terminal_ns"]-useful_received_ns)/1e6,
            "positive_exchanges": len(positive["exchanges"])}
        actions = [navigate, fill, submit_action, resize_action]
        probes = positive["feedback"]+clients["resize"]["feedback"]
        checks = {"source_geometry_expected": original_geometry == plan["expected_source_geometry"],
            "exact_translation": delta == plan["move_delta"] and moved_geometry[2:] == original_geometry[2:],
            "client_registered": positive_registered_ns <= submit_action["submitted_ns"] and
                                 resize_registered_ns <= resize_action["submitted_ns"],
            "programs_attested": all(row["accepted"]["program_sha256"] ==
                                      program_sha256(row["program"]) for row in actions),
            "relative_translated_success": useful["score"]["success"] is True and
                useful["score"]["binding_status"] == "CURRENT_TRANSLATED" and
                useful["score"]["translation"] == plan["move_delta"],
            "fixed_control_rejects_moved_crop": fixed_control["success"] is False,
            "resize_refuses_before_crop": resize_probe["score"]["success"] is False and
                resize_probe["score"]["reason"] == "surface_size_changed" and
                resize_probe["score"]["observed_crop_sha256"] is None,
            "independent_saved_value": actual == {"value": [goal["token"]]},
            "no_authority": registration["grants_input_authority"] is False and
                resize_registration["grants_input_authority"] is False and
                all(row["grants_input_authority"] is False for row in probes),
            "exact_reconciliation": all(row["reconciliation"]["matches"] for row in reconciliations)
                and all(any(item["sequence"] == probe["sequence"] for item in reconciliations)
                        for probe in probes),
            "empty_release": all(row["terminal"]["status"] == "completed" and
                row["terminal"]["release"]["verified"] is True and
                row["terminal"]["release"]["keys_down"] == [] and
                row["terminal"]["release"]["buttons_down"] == [] for row in actions),
            "feedback_limits": metrics["admission_to_first_feedback_ms"] <=
                plan["thresholds_ms"]["first_feedback_lte"] and
                metrics["admission_to_useful_feedback_ms"] <=
                plan["thresholds_ms"]["useful_feedback_lte"],
            "probe_compute_limit": metrics["useful_probe_compute_ms"] <=
                plan["thresholds_ms"]["probe_compute_lte"],
            "pre_artifact_and_terminal": metrics["useful_probe_to_image_ready_ms"] > 0 and
                                        metrics["useful_client_to_terminal_ms"] > 0,
            "zero_model_retry": plan["model_calls"] == plan["retry_limit"] == 0}
        report.update({"passed": all(checks.values()), "checks": checks, "goal": goal,
            "contract": contract, "source_observation": source_observation,
            "original_geometry": original_geometry, "moved_geometry": moved_geometry,
            "resized_geometry": resized_geometry, "navigate": navigate, "fill": fill,
            "submit_action": submit_action, "resize_action": resize_action,
            "registration": registration, "resize_registration": resize_registration,
            "clients": clients, "useful_probe": useful,
            "useful_observation": useful_observation, "fixed_control": fixed_control,
            "reconciliations": reconciliations, "actual": actual,
            "metrics_ms": metrics, "model_calls": 0, "retry_count": 0})
    finally:
        for thread in threads:
            if thread.is_alive(): thread.join(1)
        if executor is not None: executor.close()
        if controller is not None and original_geometry is not None and moved_geometry is not None:
            try:
                binding = backend.binding(); window = controller.create_resource_object("window", binding["surface"])
                window.configure(x=original_geometry[0], y=original_geometry[1],
                                 width=original_geometry[2], height=original_geometry[3]); controller.sync()
            except Exception: pass
            controller.close()
        if backend is not None:
            try: backend.close()
            finally: (root/"owner-events.json").write_text(json.dumps(backend.owner.records, indent=2)+"\n")
        if output is not None and output.exists(): shutil.copy2(output, root/output.name)
        if app_server is not None: app_server.shutdown(); app_server.server_close()
        if session is not None: session.close(); shutil.rmtree(session.tmp)
        delivery.close(); (root/"events.json").write_text(json.dumps(events, indent=2)+"\n")
        if len(report) > 4: persist(root/"report.json", report)
    print(json.dumps({"passed": report.get("passed"), "checks": report.get("checks"),
        "metrics_ms": report.get("metrics_ms"), "scope": report["scope"]}, indent=2))
    return 0 if report.get("passed") else 1


if __name__ == "__main__": raise SystemExit(main())
