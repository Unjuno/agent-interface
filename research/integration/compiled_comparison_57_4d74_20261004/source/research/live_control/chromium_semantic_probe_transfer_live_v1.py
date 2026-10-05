"""One frozen Chromium transfer of pre-artifact semantic feedback."""
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
PREREG = HERE / "chromium_semantic_probe_transfer_live_v1_prereg.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def persist(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2) + "\n")
        stream.flush(); os.fsync(stream.fileno())


def verify(plan):
    checks = {name: (REPO/name).is_file() and sha(REPO/name) == digest
              for name, digest in plan["source_sha256"].items()}
    checks.update({
        "output_absent": not (REPO/plan["output"]).exists(),
        "one_allocation_no_retry": plan["allocations"] == 1 and plan["retry_limit"] == 0,
        "zero_model": plan["model_calls"] == 0,
        "fixed_seed": plan["seed"] == 206,
        "fixed_contract": plan["probe_contract"] == {
            "schema": "exact-rgb-crop-semantic-probe-v1",
            "probe_id": "chromium_submission_title",
            "box": [15, 170, 330, 215],
            "expected_crop_sha256":
                "879ad35b666f63b1c9a401c359bd563c52170146b3e4ca5c7314448fdfb5784c",
            "success_reason": "submission_title_exactly_visible",
            "grants_input_authority": False},
        "thresholds": plan["thresholds_ms"] == {
            "negative_first_feedback_lte": 300,
            "positive_first_feedback_lte": 300,
            "positive_useful_feedback_lte": 600,
            "probe_compute_lte": 5},
    })
    return checks


def wait_terminal(events, identifier, timeout=6):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        row = next((event for event in events if event.get("event") == "terminal"
                    and event.get("id") == identifier), None)
        if row is not None:
            return row
        time.sleep(.001)
    raise RuntimeError("terminal missing: " + identifier)


def main():
    plan = read(PREREG); verification = verify(plan)
    if "--verify-only" in sys.argv:
        print(json.dumps({"passed": all(verification.values()),
                          "checks": verification}, indent=2))
        return 0 if all(verification.values()) else 1
    if not all(verification.values()):
        raise RuntimeError(verification)
    if os.name == "nt" or not Path("/mnt/c").is_dir():
        raise RuntimeError("run frozen Unix/X11 allocation from WSL")

    from executor_v13 import Executor
    from executor_v11 import program_sha256
    from release_event_socket_v3 import ReleaseEventSocket
    from semantic_probe_backend_v2 import Backend, suite
    from unix_json_deadline import exchange

    root = REPO/plan["output"]
    root.mkdir(parents=True, exist_ok=False)
    events = []; clients = {}; threads = []
    delivery = ReleaseEventSocket()
    session = backend = executor = output = app_server = None

    def emit(row):
        row["runtime_emit_ns"] = time.perf_counter_ns()
        events.append(row); delivery.append(row)

    def exchange_record(request):
        row = {"request": request, "client_started_ns": time.perf_counter_ns()}
        reply = exchange(delivery.path, request, timeout=request["timeout"] + 1)
        row.update({"reply": reply, "client_returned_ns": time.perf_counter_ns(),
                    "response_bytes": len((json.dumps(reply)+"\n").encode())})
        return row

    def semantic_client(label, action_id, max_exchanges, require_success):
        result = {"exchanges": [], "feedback": []}; after = 0
        for ordinal in range(max_exchanges):
            request = {"after": after, "events": ["semantic_probe", "terminal"],
                "timeout": 4, "action_id": action_id,
                "request_id": f"{label}-{ordinal}"}
            row = exchange_record(request); result["exchanges"].append(row)
            boundary = row["reply"]["records"][-1]
            if boundary["event"] == "terminal":
                result["terminal_before_stop"] = boundary
                break
            result["feedback"].append(boundary)
            if boundary["score"]["success"] is require_success:
                break
            after = row["reply"]["cursor"]
        result["completed_ns"] = time.perf_counter_ns(); clients[label] = result

    def submit(identifier, program):
        submitted_ns = time.perf_counter_ns()
        executor.submit(identifier, program, backend.sequence,
                        time.perf_counter_ns() + 8_000_000_000)
        accepted = next(row for row in events if row.get("event") == "accepted"
                        and row.get("id") == identifier)
        terminal = wait_terminal(events, identifier)
        return {"id": identifier, "program": program, "submitted_ns": submitted_ns,
                "accepted": accepted, "terminal": terminal}

    report = {"schema": "chromium-semantic-probe-transfer-live-v1",
              "allocation_id": plan["allocation_id"], "verification": verification,
              "scope": plan["scope"]}
    try:
        with (root/"setup.txt").open("w") as diagnostics, contextlib.redirect_stdout(diagnostics):
            session = suite.Session()
            goal, output, app_server = suite.prepare(
                session, "chromium", plan["seed"], plan["chromium"])
            backend = Backend(session, root, emit)
        executor = Executor(backend, emit)
        backend.snapshot("initial", 0)

        negative_id = "chromium-blank-negative-01"
        negative_registration = backend.register_semantic_probe(
            negative_id, plan["probe_contract"])
        count = len(delivery.request_receipts())
        negative_thread = threading.Thread(target=semantic_client,
            args=("negative", negative_id, 1, False))
        threads.append(negative_thread); negative_thread.start()
        if not delivery.wait_requests(count+1):
            raise RuntimeError("negative client did not register")
        negative_registered_ns = delivery.request_receipts()[-1]["received_ns"]
        negative_action = submit(negative_id, [{"op": "observe"}])
        negative_thread.join(4)
        if negative_thread.is_alive():
            raise RuntimeError("negative client timed out")

        navigate = submit("chromium-navigate-01", [
            {"op": "chord", "modifier": "Control_L", "key": "l"},
            {"op": "text", "text": goal["url"]},
            {"op": "key", "key": "Return"},
            {"op": "wait_title", "contains": "AI FORM READY", "timeout_ms": 1500}])
        fill = submit("chromium-fill-01", [
            {"op": "pointer_click", "x": 180, "y": 243, "duration_ms": 80},
            {"op": "chord", "modifier": "Control_L", "key": "a"},
            {"op": "text", "text": goal["token"]},
            {"op": "observe"}])

        positive_id = "chromium-submit-positive-01"
        positive_registration = backend.register_semantic_probe(
            positive_id, plan["probe_contract"])
        count = len(delivery.request_receipts())
        positive_thread = threading.Thread(target=semantic_client,
            args=("positive", positive_id, plan["max_positive_exchanges"], True))
        threads.append(positive_thread); positive_thread.start()
        if not delivery.wait_requests(count+1):
            raise RuntimeError("positive client did not register")
        positive_registered_ns = delivery.request_receipts()[-1]["received_ns"]
        positive_action = submit(positive_id, [
            {"op": "pointer_click", "x": 270, "y": 243, "duration_ms": 80},
            {"op": "wait_title", "contains": "AI FORM SAVED", "timeout_ms": 1500},
            {"op": "observe"}])
        positive_thread.join(4)
        if positive_thread.is_alive():
            raise RuntimeError("positive client timed out")

        negative = clients["negative"]; positive = clients["positive"]
        if len(negative["feedback"]) != 1 or negative["feedback"][0]["score"]["success"]:
            raise RuntimeError("one negative probe required")
        useful = next((row for row in positive["feedback"]
                       if row["score"]["success"]), None)
        if useful is None:
            raise RuntimeError("positive semantic feedback missing")
        first_positive = positive["feedback"][0]
        negative_feedback_ns = negative["exchanges"][0]["client_returned_ns"]
        first_positive_feedback_ns = positive["exchanges"][0]["client_returned_ns"]
        useful_index = positive["feedback"].index(useful)
        useful_feedback_ns = positive["exchanges"][useful_index]["client_returned_ns"]
        reconciliations = [row for row in events
            if row.get("event") == "semantic_probe_reconciled"]
        useful_reconciliation = next(row for row in reconciliations
            if row.get("id") == positive_id and row["sequence"] == useful["sequence"])
        actual = parse_qs(output.read_text()) if output.exists() else {}
        metrics = {
            "negative_admission_to_first_feedback_ms":
                (negative_feedback_ns-negative_action["accepted"]["accepted_ns"])/1e6,
            "positive_admission_to_first_feedback_ms":
                (first_positive_feedback_ns-positive_action["accepted"]["accepted_ns"])/1e6,
            "positive_admission_to_useful_feedback_ms":
                (useful_feedback_ns-positive_action["accepted"]["accepted_ns"])/1e6,
            "positive_useful_probe_compute_ms":
                (useful["probe_completed_ns"]-useful["probe_started_ns"])/1e6,
            "useful_probe_to_image_ready_ms":
                (useful_reconciliation["image_ready_ns"]-useful["probe_completed_ns"])/1e6,
            "useful_client_to_terminal_ms":
                (positive_action["terminal"]["terminal_ns"]-useful_feedback_ns)/1e6,
            "negative_exchanges": len(negative["exchanges"]),
            "positive_exchanges": len(positive["exchanges"]),
        }
        all_terminals = [negative_action["terminal"], navigate["terminal"],
                         fill["terminal"], positive_action["terminal"]]
        checks = {
            "clients_registered_before_submit": (
                negative_registered_ns <= negative_action["submitted_ns"] and
                positive_registered_ns <= positive_action["submitted_ns"]),
            "programs_attested": all(row["accepted"]["program_sha256"] ==
                program_sha256(row["program"]) for row in
                (negative_action, navigate, fill, positive_action)),
            "blank_rejected": negative["feedback"][0]["score"]["success"] is False,
            "submission_detected": useful["score"]["success"] is True,
            "independent_saved_value": actual == {"value": [goal["token"]]},
            "registrations_no_authority": all(row["status"] == "REGISTERED_NO_AUTHORITY"
                and row["grants_input_authority"] is False
                for row in (negative_registration, positive_registration)),
            "all_probes_no_authority": all(row["grants_input_authority"] is False
                and row["score"]["grants_input_authority"] is False
                for row in negative["feedback"]+positive["feedback"]),
            "all_exact_reconciliations": (len(reconciliations) ==
                len(negative["feedback"])+len(positive["feedback"]) and
                all(row["reconciliation"]["matches"] is True for row in reconciliations)),
            "pre_artifact_useful": metrics["useful_probe_to_image_ready_ms"] > 0,
            "terminal_empty_release": all(row["status"] == "completed" and
                row["release"]["verified"] is True and row["release"]["keys_down"] == []
                and row["release"]["buttons_down"] == [] for row in all_terminals),
            "negative_feedback_limit": metrics["negative_admission_to_first_feedback_ms"] <=
                plan["thresholds_ms"]["negative_first_feedback_lte"],
            "positive_first_feedback_limit": metrics["positive_admission_to_first_feedback_ms"] <=
                plan["thresholds_ms"]["positive_first_feedback_lte"],
            "positive_useful_feedback_limit": metrics["positive_admission_to_useful_feedback_ms"] <=
                plan["thresholds_ms"]["positive_useful_feedback_lte"],
            "probe_compute_limit": metrics["positive_useful_probe_compute_ms"] <=
                plan["thresholds_ms"]["probe_compute_lte"],
            "zero_model_retry": plan["model_calls"] == plan["retry_limit"] == 0,
        }
        report.update({"passed": all(checks.values()), "checks": checks, "goal": goal,
            "negative_registration": negative_registration,
            "positive_registration": positive_registration,
            "negative_action": negative_action, "navigate": navigate, "fill": fill,
            "positive_action": positive_action, "clients": clients,
            "reconciliations": reconciliations, "useful_probe": useful,
            "useful_reconciliation": useful_reconciliation, "actual": actual,
            "metrics_ms": metrics, "model_calls": 0, "retry_count": 0})
    finally:
        for thread in threads:
            if thread.is_alive(): thread.join(1)
        if executor is not None: executor.close()
        if backend is not None:
            try: backend.close()
            finally:
                (root/"owner-events.json").write_text(
                    json.dumps(backend.owner.records, indent=2)+"\n")
        if output is not None and output.exists(): shutil.copy2(output, root/output.name)
        if app_server is not None: app_server.shutdown(); app_server.server_close()
        if session is not None: session.close(); shutil.rmtree(session.tmp)
        delivery.close()
        (root/"events.json").write_text(json.dumps(events, indent=2)+"\n")
        if len(report) > 4: persist(root/"report.json", report)
    print(json.dumps({"passed": report.get("passed"), "checks": report.get("checks"),
                      "metrics_ms": report.get("metrics_ms"),
                      "scope": report["scope"]}, indent=2))
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
