"""One frozen actual-X11 pointer-focus transfer through Executor v13."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PREREG = HERE / "pointer_release_transfer_live_v1_prereg.json"


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def verify(plan):
    checks = {name: (REPO / name).is_file() and sha(REPO / name) == digest
              for name, digest in plan["source_sha256"].items()}
    checks.update({"output_absent": not (REPO / plan["output"]).exists(),
                   "one_episode_no_retry": plan["episodes"] == 1 and plan["retry_limit"] == 0,
                   "zero_model": plan["model_calls"] == 0,
                   "thresholds": plan["thresholds_ms"] == {
                       "focus_request_to_physical_release_lte": 50,
                       "focus_request_to_release_publication_lte": 75,
                       "focus_request_to_terminal_lte": 150}})
    return checks


def main():
    verify_only = "--verify-only" in sys.argv
    plan = read(PREREG); verification = verify(plan)
    if verify_only:
        print(json.dumps({"passed": all(verification.values()), "checks": verification}, indent=2))
        return 0 if all(verification.values()) else 1
    if not all(verification.values()): raise RuntimeError(verification)
    if os.name == "nt" or not Path("/mnt/c").is_dir():
        raise RuntimeError("run the frozen X11 allocation from WSL")
    from Xlib import X, display
    from cause_session_v1 import Backend, suite
    from executor_v13 import Executor
    root = REPO / plan["output"]; root.mkdir(parents=True, exist_ok=False)
    events = []; session = backend = executor = controller = sink = original = output = server = None
    report = {"allocation_id": plan["allocation_id"], "verification": verification,
              "scope": plan["scope"]}
    try:
        with (root / "setup.txt").open("w") as diagnostics, contextlib.redirect_stdout(diagnostics):
            session = suite.Session()
            goal, output, server = suite.prepare(session, "inkscape", plan["seed"], "")
            backend = Backend(session, root, events.append)
            controller = display.Display(session.name)
        backend.snapshot("initial", 0)
        initial = next(row for row in events if row["event"] == "observation")
        executor = Executor(backend, events.append)
        identifier = "pointer-release-focus-transfer-01"
        step = {"op": "pointer_drag", "points": plan["points"],
                "duration_ms": plan["duration_ms"]}
        executor.submit(identifier, [step], backend.sequence,
                        time.perf_counter_ns() + 5_000_000_000)
        accepted = next(row for row in events if row["event"] == "accepted")
        root_window = controller.screen().root
        def down(): return bool(root_window.query_pointer().mask & X.Button1Mask)
        deadline = time.monotonic() + 2
        while not down() and time.monotonic() < deadline: time.sleep(.002)
        if not down(): raise RuntimeError("physical pointer admission not observed")
        first_moves = [row for row in events if row.get("event") == "pointer_admission" and
                       row.get("operation") == "move"]
        original = controller.get_input_focus().focus
        sink = root_window.create_window(0, 0, 100, 80, 0,
            controller.screen().root_depth, override_redirect=True)
        sink.map()
        focus_request_ns = time.perf_counter_ns()
        sink.set_input_focus(X.RevertToParent, X.CurrentTime); controller.sync()
        focus_sync_ns = time.perf_counter_ns()
        deadline = time.monotonic() + 2
        while (not any(row.get("event") == "terminal" for row in events) and
               time.monotonic() < deadline): time.sleep(.002)
        released = next(row for row in events if row.get("event") == "input_released")
        terminal = next(row for row in events if row.get("event") == "terminal")
        physical_up = not down()
        original.set_input_focus(X.RevertToParent, X.CurrentTime); controller.sync()
        later_moves = [row for row in events if row.get("event") == "pointer_admission" and
                       row.get("operation") == "move"]
        metrics = {
            "focus_request_to_sync_ms": (focus_sync_ns - focus_request_ns) / 1e6,
            "focus_request_to_physical_release_ms":
                (released["owner_release"]["verified_ns"] - focus_request_ns) / 1e6,
            "focus_request_to_release_publication_ms":
                (released["published_ns"] - focus_request_ns) / 1e6,
            "physical_release_to_publication_ms":
                (released["published_ns"] - released["owner_release"]["verified_ns"]) / 1e6,
            "focus_request_to_terminal_ms":
                (terminal["terminal_ns"] - focus_request_ns) / 1e6,
            "release_publication_to_terminal_ms":
                (terminal["terminal_ns"] - released["published_ns"]) / 1e6,
        }
        owner_record = released["owner_release"]
        checks = {
            "pointer_down_observed": bool(first_moves) and physical_up,
            "focus_release_reason": owner_record["reason"] == "focus_changed",
            "lease_token_bound": released["intent_token"] == accepted["intent_token"],
            "empty_owner_release": owner_record["verified"] is True and
                owner_record["keys_down"] == [] and owner_record["buttons_down"] == [],
            "release_before_terminal": released["published_ns"] < terminal["terminal_ns"],
            "terminal_needs_decision": terminal["status"] == "needs_decision" and
                terminal["decision_reason"] == "focus_changed",
            "terminal_same_cause": terminal["interruption"]["intent_token"] ==
                released["intent_token"] and terminal["interruption"]["record"] == owner_record,
            "terminal_cleanup_empty": terminal["release"]["verified"] is True and
                terminal["release"]["keys_down"] == [] and terminal["release"]["buttons_down"] == [],
            "no_drag_tail": len(later_moves) == 1 and later_moves[0]["payload"] == plan["points"][0],
            "no_explicit_cancel": not any(row.get("event") == "cancel_requested" for row in events),
            "physical_release_threshold": metrics["focus_request_to_physical_release_ms"] <= 50,
            "publication_threshold": metrics["focus_request_to_release_publication_ms"] <= 75,
            "terminal_threshold": metrics["focus_request_to_terminal_ms"] <= 150,
        }
        report.update({"passed": all(checks.values()), "checks": checks,
            "goal": goal, "initial_observation": initial, "accepted": accepted,
            "focus_request_ns": focus_request_ns, "focus_sync_ns": focus_sync_ns,
            "physical_release_event": released, "terminal": terminal,
            "pointer_moves": later_moves, "metrics_ms": metrics,
            "model_calls": 0, "retry_count": 0})
    finally:
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
        if server is not None: server.shutdown(); server.server_close()
        if session is not None:
            session.close(); shutil.rmtree(session.tmp)
        (root / "events.json").write_text(json.dumps(events, indent=2) + "\n")
        (root / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report.get("passed"), "checks": report.get("checks"),
                      "metrics_ms": report.get("metrics_ms")}, indent=2))
    return 0 if report.get("passed") else 1


if __name__ == "__main__": raise SystemExit(main())
