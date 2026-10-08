"""One-shot private-Xvfb backend-process-restart boundary experiment."""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

REPO = Path("/tmp/agent-interface-2437-sparse-58b12a314b26")
sys.path.insert(0, str(REPO))


def key_down(observer, keycode: int) -> bool:
    bits = observer.query_keymap()
    return bool(bits[keycode >> 3] & (1 << (keycode & 7)))


def xvfb_pid(display_name: str) -> int | None:
    listing = subprocess.run(["ps", "-eo", "pid=,args="], check=True, text=True, capture_output=True).stdout
    for line in listing.splitlines():
        fields = line.strip().split()
        if len(fields) >= 3 and fields[1] == "Xvfb" and fields[2] == display_name:
            return int(fields[0])
    return None


def make_program():
    from runtime.core_v1.contract import SCHEMA_PROGRAM
    return {
        "schema": SCHEMA_PROGRAM,
        "program_id": "issue2437-backend-restart-stale-observation-v1",
        "source": {"observation_seq": 7, "binding_revision": 3},
        "authority": {"lease_id": "private-xvfb-research", "expires_at_ns": time.monotonic_ns() + 30_000_000_000},
        "terminal": {"release_all_required": True},
        "ops": [{"op": "key_chord", "keys": ["F8"]}, {"op": "release_all"}],
    }


def hold_worker(display_name: str, ready_path: Path, target: int) -> int:
    from runtime.backends.x11_v1.backend import X11Backend
    from runtime.backends.x11_v1.session import X11RuntimeSession
    backend = X11Backend(display_name, {"fixture": target})
    session = X11RuntimeSession(backend)
    backend.key_state("F8", True)
    ready_path.write_text(json.dumps({"pid": os.getpid(), "session_id": uuid.uuid4().hex,
                                     "recovery_required": session.recovery_required,
                                     "emissions": backend.emissions}) + "\n")
    while True:
        time.sleep(1)


def dispatch_worker(display_name: str, target: int, program_path: Path, result_path: Path) -> int:
    from runtime.backends.x11_v1.backend import X11Backend
    from runtime.backends.x11_v1.session import X11RuntimeSession
    program_bytes = program_path.read_bytes()
    program = json.loads(program_bytes)
    backend = X11Backend(display_name, {"fixture": target})
    try:
        session = X11RuntimeSession(backend)
        session_id = uuid.uuid4().hex
        before = backend.emissions
        dispatch_now_ns = time.monotonic_ns()
        result = session.dispatch(program, current_observation_seq=7, current_binding_revision=3)
        row = {"stale_dispatch": result, "emissions_before": before,
               "emissions_after": backend.emissions,
               "new_session_recovery_required_initial": session.recovery_required,
               "new_session_recovery_required_after": session.recovery_required,
               "pid": os.getpid(), "session_id": session_id,
               "dispatch_now_ns": dispatch_now_ns,
               "request_sha256": __import__("hashlib").sha256(program_bytes).hexdigest()}
        result_path.write_text(json.dumps(row, sort_keys=True, indent=2) + "\n")
        return 0
    finally:
        backend.close()


def formal(output: Path) -> None:
    from Xlib import XK, display
    from runtime.backends.x11_v1.backend import X11Backend
    from runtime.backends.x11_v1.session import X11RuntimeSession

    output.parent.mkdir(parents=True, exist_ok=True)
    record = {"schema": "issue2437-backend-process-restart-v1", "display": os.environ["DISPLAY"]}
    with tempfile.TemporaryDirectory(prefix="ai-2437-") as td:
        root = Path(td)
        meta, effect = root / "meta.json", root / "effect.json"
        fixture = subprocess.Popen([
            sys.executable, "-m", "runtime.backends.x11_v1.fixture_app",
            "--meta", str(meta), "--effect", str(effect),
        ], cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        worker = None
        dispatch = None
        backend = None
        observer = None
        try:
            deadline = time.monotonic() + 8
            while not meta.exists() and time.monotonic() < deadline:
                if fixture.poll() is not None:
                    raise RuntimeError(f"fixture exited {fixture.returncode}")
                time.sleep(.02)
            if not meta.exists():
                raise RuntimeError("fixture metadata timeout")
            target = int(json.loads(meta.read_text())["window_id"])
            observer = display.Display(os.environ["DISPLAY"])
            f8 = observer.keysym_to_keycode(XK.string_to_keysym("F8"))
            server_pid = xvfb_pid(os.environ["DISPLAY"])
            record["fixture_pid"] = fixture.pid
            record["window_id"] = target
            record["f8_keycode"] = f8
            record["server_pid"] = server_pid

            # Create and retain the still-unexpired request before failure injection.
            program_path = root / "stale-request.json"
            program_bytes = json.dumps(make_program(), sort_keys=True, separators=(",", ":")).encode("utf-8")
            program_path.write_bytes(program_bytes)
            import hashlib
            record["stale_request_sha256"] = hashlib.sha256(program_bytes).hexdigest()
            record["stale_request_bytes"] = len(program_bytes)
            record["stale_request_source"] = json.loads(program_bytes)["source"]
            record["stale_request_expiry_ns"] = json.loads(program_bytes)["authority"]["expires_at_ns"]

            ready = root / "hold-ready.json"
            worker = subprocess.Popen([
                sys.executable, str(Path(__file__).resolve()), "--hold-worker",
                os.environ["DISPLAY"], str(ready), str(target),
            ], cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            deadline = time.monotonic() + 5
            while not ready.exists() and time.monotonic() < deadline:
                if worker.poll() is not None:
                    raise RuntimeError(f"hold worker exited {worker.returncode}")
                time.sleep(.01)
            if not ready.exists():
                raise RuntimeError("hold worker readiness timeout")
            record["hold_worker_ready"] = json.loads(ready.read_text())
            record["hold_worker_pid"] = worker.pid
            observer.sync()
            record["key_down_before_crash"] = key_down(observer, f8)
            record["worker_exit_before_kill"] = worker.poll()
            os.kill(worker.pid, signal.SIGKILL)
            worker.wait(timeout=3)
            record["worker_exit_after_kill"] = worker.returncode
            time.sleep(.05)
            observer.sync()
            record["key_down_after_backend_crash"] = key_down(observer, f8)

            result_path = root / "dispatch-result.json"
            dispatch = subprocess.Popen([
                sys.executable, str(Path(__file__).resolve()), "--dispatch-worker",
                os.environ["DISPLAY"], str(target), str(program_path), str(result_path),
            ], cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            record["dispatch_worker_exit"] = dispatch.wait(timeout=12)
            if not result_path.exists():
                raise RuntimeError("dispatch worker result missing")
            dispatch_row = json.loads(result_path.read_text())
            record["stale_dispatch"] = dispatch_row["stale_dispatch"]
            record["emissions_before_stale_dispatch"] = dispatch_row["emissions_before"]
            record["emissions_after_stale_dispatch"] = dispatch_row["emissions_after"]
            record["new_session_recovery_required_initial"] = dispatch_row["new_session_recovery_required_initial"]
            record["new_session_recovery_required_after"] = dispatch_row["new_session_recovery_required_after"]
            record["dispatch_request_sha256"] = dispatch_row["request_sha256"]
            record["dispatch_worker_pid"] = dispatch_row["pid"]
            record["dispatch_session_id"] = dispatch_row["session_id"]
            record["hold_session_id"] = record["hold_worker_ready"].get("session_id")
            observer.sync()
            record["key_down_after_stale_dispatch"] = key_down(observer, f8)
            record["fixture_effect_exists"] = effect.exists()
            record["new_session_recovery_required_after_dispatch"] = session.recovery_required
            record["server_pid_after_restart_boundary"] = xvfb_pid(os.environ["DISPLAY"])
            record["xvfb_same_process_alive"] = (
                record["server_pid"] is not None
                and record["server_pid"] == record["server_pid_after_restart_boundary"]
            )

            # Explicit out-of-band cleanup after recording the scientific outcome.
            from Xlib.ext import xtest
            from Xlib import X
            xtest.fake_input(observer, X.KeyRelease, f8)
            observer.sync()
            record["key_down_after_explicit_cleanup"] = key_down(observer, f8)
            record["cleanup_owner"] = "independent-observer-connection"
        except Exception as error:
            record["harness_exception"] = repr(error)
        finally:
            if observer is not None and "f8" in locals():
                try:
                    if key_down(observer, f8):
                        from Xlib import X
                        from Xlib.ext import xtest
                        xtest.fake_input(observer, X.KeyRelease, f8)
                        observer.sync()
                        record["emergency_cleanup_used"] = True
                except Exception as cleanup_error:
                        record["emergency_cleanup_error"] = repr(cleanup_error)
            if dispatch is not None and dispatch.poll() is None:
                dispatch.kill()
                dispatch.wait(timeout=3)
            if worker is not None and worker.poll() is None:
                worker.kill()
                worker.wait(timeout=3)
            if backend is not None:
                backend.close()
            if observer is not None:
                observer.close()
            if fixture.poll() is None:
                fixture.terminate()
                try:
                    fixture.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    fixture.kill()
                    fixture.wait(timeout=3)
    output.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def audit_document(raw: dict) -> list[str]:
    errors: list[str] = []
    required = ["key_down_before_crash", "key_down_after_backend_crash", "worker_exit_after_kill",
                "new_session_recovery_required_initial", "stale_dispatch", "emissions_before_stale_dispatch",
                "emissions_after_stale_dispatch", "key_down_after_explicit_cleanup", "cleanup_owner",
                "dispatch_now_ns", "stale_request_expiry_ns", "dispatch_worker_exit", "worker_exit_before_kill"]
    errors.extend(f"missing:{key}" for key in required if key not in raw)
    if errors:
        return errors
    if "harness_exception" in raw: errors.append("candidate-harness-exception")
    if "emergency_cleanup_used" in raw: errors.append("emergency-cleanup-changed-formal-boundary")
    if "emergency_cleanup_error" in raw: errors.append("emergency-cleanup-failed")
    if raw["key_down_before_crash"] is not True: errors.append("precrash-key-not-observed-down")
    if raw["worker_exit_after_kill"] != -signal.SIGKILL: errors.append("backend-process-not-killed")
    if raw.get("xvfb_same_process_alive") is not True: errors.append("xvfb-server-identity-not-preserved")
    if raw["key_down_after_backend_crash"] is not True: errors.append("crash-boundary-did-not-retain-key-down")
    if raw.get("dispatch_worker_exit") != 0: errors.append("restart-worker-exit-not-zero")
    if raw.get("worker_exit_before_kill") is not None: errors.append("backend-worker-was-not-live-before-kill")
    ready = raw.get("hold_worker_ready")
    if not isinstance(ready, dict) or ready.get("pid") != raw.get("hold_worker_pid"): errors.append("held-owner-process-identity-mismatch")
    if not raw.get("hold_session_id") or raw.get("hold_session_id") == raw.get("dispatch_session_id"):
        errors.append("backend-session-identities-not-distinct")
    if not isinstance(raw.get("stale_dispatch"), dict): errors.append("dispatch-result-not-object")
    if raw.get("stale_request_expiry_ns", 0) <= raw.get("dispatch_now_ns", 0): errors.append("stale-request-not-unexpired-at-dispatch")
    if raw.get("dispatch_request_sha256") != raw.get("stale_request_sha256"): errors.append("stale-request-bytes-changed")
    if raw["key_down_after_explicit_cleanup"] is not False: errors.append("cleanup-not-independently-neutral")
    if raw["cleanup_owner"] != "independent-observer-connection": errors.append("cleanup-owner-mismatch")
    return errors


def classify(raw: dict) -> tuple[str, list[str]]:
    errors = audit_document(raw)
    if errors:
        return "STOP_AUDIT_ERRORS", errors
    dispatch = raw.get("stale_dispatch", {})
    if not isinstance(dispatch, dict):
        return "STOP_AUDIT_ERRORS", ["dispatch-result-not-object"]
    emitted = raw.get("emissions_after_stale_dispatch", 0) > raw.get("emissions_before_stale_dispatch", 0)
    if raw.get("new_session_recovery_required_initial") is False and dispatch.get("status") == "completed" and emitted:
        return "FAIL_BACKEND_RESTART_STALE_REQUEST_ADMITTED", []
    if (raw.get("new_session_recovery_required_initial") is True
            and dispatch.get("status") == "refused"
            and dispatch.get("error") == "INPUT_RECOVERY_REQUIRED"
            and not emitted):
        return "PASS_BACKEND_RESTART_FAIL_CLOSED_SCOPED", []
    return "STOP_INCONCLUSIVE_DISPATCH_STATE", []


def audit_file(path: Path, receipt: Path) -> None:
    raw_bytes = path.read_bytes()
    raw = json.loads(raw_bytes)
    errors = audit_document(raw)
    import hashlib
    disposition, errors = classify(raw)
    result = {"disposition": disposition,
              "errors": errors, "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
              "raw_bytes": len(raw_bytes)}
    receipt.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--formal", type=Path)
    ap.add_argument("--audit", type=Path)
    ap.add_argument("--receipt", type=Path)
    ap.add_argument("--hold-worker", nargs=3)
    ap.add_argument("--dispatch-worker", nargs=4)
    args = ap.parse_args()
    if args.hold_worker:
        sys.exit(hold_worker(args.hold_worker[0], Path(args.hold_worker[1]), int(args.hold_worker[2])))
    if args.dispatch_worker:
        sys.exit(dispatch_worker(args.dispatch_worker[0], int(args.dispatch_worker[1]), Path(args.dispatch_worker[2]), Path(args.dispatch_worker[3])))
    if args.formal:
        formal(args.formal)
    elif args.audit and args.receipt:
        audit_file(args.audit, args.receipt)
