"""Matched same-stream client wait comparison for early release versus terminal."""
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
PREREG = HERE / "release_client_wait_live_v2_prereg.json"
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
            "focus_to_early_client_lte": 40,
            "early_client_advantage_gte": 40,
            "focus_to_terminal_client_lte": 300}})
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
    from release_event_socket_v2 import ReleaseEventSocket
    from release_pending_action_v1 import PendingAction
    from release_recovery_backend_v1 import Backend, suite
    from unix_json_deadline import exchange

    root = REPO / plan["output"]; root.mkdir(parents=True, exist_ok=False)
    events = []; session = backend = executor = controller = sink = original = output = app_server = None
    delivery = ReleaseEventSocket(); report = {"allocation_id": plan["allocation_id"],
        "verification": verification, "scope": plan["scope"]}
    clients = {}; threads = []
    def emit(row):
        row["runtime_emit_ns"] = time.perf_counter_ns(); events.append(row); delivery.append(row)
    def call(label, request):
        record = {"request": request, "client_started_ns": time.perf_counter_ns()}
        reply = exchange(delivery.path, request, timeout=request["timeout"] + 1)
        record.update({"reply": reply, "client_returned_ns": time.perf_counter_ns(),
                       "response_bytes": len((json.dumps(reply) + "\n").encode())})
        clients[label] = record
    try:
        with (root / "setup.txt").open("w") as diagnostics, contextlib.redirect_stdout(diagnostics):
            session = suite.Session()
            goal, output, app_server = suite.prepare(session, "inkscape", plan["seed"], "")
            backend = Backend(session, root, emit); controller = display.Display(session.name)
        backend.snapshot("initial", 0); executor = Executor(backend, emit)
        identifier = "release-client-pointer-click-02"
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
        tracker = PendingAction(identifier); pending = tracker.ingest(early["reply"])
        resume_request = {"after": early["reply"]["cursor"], "events": ["terminal"],
            "timeout": 5, "action_id": identifier, "request_id": "early-resume"}
        call("early_resume", resume_request); closed = tracker.ingest(clients["early_resume"]["reply"])
        original.set_input_focus(X.RevertToParent, X.CurrentTime); controller.sync()
        terminal = next(row for row in events if row.get("event") == "terminal")
        observations = [row for row in events if row.get("event") == "observation" and
                        row.get("id") == identifier]
        metrics = {
            "focus_to_runtime_release_ms":
                (early_boundary["owner_release"]["verified_ns"] - focus_request_ns) / 1e6,
            "focus_to_early_client_ms": (early["client_returned_ns"] - focus_request_ns) / 1e6,
            "focus_to_terminal_client_ms":
                (terminal_client["client_returned_ns"] - focus_request_ns) / 1e6,
            "early_client_wait_advantage_ms":
                (terminal_client["client_returned_ns"] - early["client_returned_ns"]) / 1e6,
            "focus_to_early_final_terminal_ms":
                (clients["early_resume"]["client_returned_ns"] - focus_request_ns) / 1e6,
            "runtime_release_to_terminal_ms":
                (terminal["terminal_ns"] - early_boundary["owner_release"]["verified_ns"]) / 1e6,
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
            "pending_client_state": pending["state"] == "input_released_terminal_pending" and
                pending["physical_release_verified"] is True,
            "terminal_client_boundary": terminal_boundary["event"] == "terminal" and
                terminal_boundary["status"] == "needs_decision",
            "early_resume_same_terminal": closed["state"] == "terminal_received" and
                closed["terminal"] == terminal_boundary,
            "lease_and_cause_match": early_boundary["intent_token"] == accepted["intent_token"] and
                terminal_boundary["interruption"]["record"] == early_boundary["owner_release"],
            "real_post_release_observation": len(observations) == 1 and
                any(row.get("event") == "post_release_observation_complete" for row in events),
            "early_reply_smaller": early["response_bytes"] < terminal_client["response_bytes"],
            "round_trip_accounting": len([early, clients["early_resume"]]) == 2,
            "focus_to_early_threshold": metrics["focus_to_early_client_ms"] <= 40,
            "early_advantage_threshold": metrics["early_client_wait_advantage_ms"] >= 40,
            "terminal_threshold": metrics["focus_to_terminal_client_ms"] <= 300,
            "zero_model_retry_cancel": plan["model_calls"] == plan["retry_limit"] == 0 and
                not any(row.get("event") == "cancel_requested" for row in events),
        }
        report.update({"passed": all(checks.values()), "checks": checks, "goal": goal,
            "accepted": accepted, "focus_request_ns": focus_request_ns,
            "server_request_receipts": server_receipts,
            "server_request_receipt_artifact": str(receipt_path),
            "server_request_receipt_sha256": receipt_sha256,
            "clients": clients, "pending_state": pending, "closed_state": closed,
            "terminal": terminal, "post_release_observations": observations,
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

