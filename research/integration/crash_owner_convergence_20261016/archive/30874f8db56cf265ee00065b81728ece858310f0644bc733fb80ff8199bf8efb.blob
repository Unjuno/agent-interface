"""One isolated outer-cleanup integration candidate; see PLAN.md."""
import hashlib, json, os, select, signal, subprocess, sys, tempfile, threading, time, types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOOM = ROOT / "research" / "doom"
LIVE = ROOT / "research" / "live_control"
for path in (DOOM, LIVE, ROOT / "research" / "observation_tiles",
             ROOT / "research" / "observation_gating", ROOT / "research" / "real_apps_v1"):
    sys.path.insert(0, str(path))
pil = types.ModuleType("PIL"); pil.__path__ = []
pil.Image = types.ModuleType("PIL.Image")
pil.Image.frombytes = lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("capture unused"))
pil.ImageGrab = types.ModuleType("PIL.ImageGrab")
pil.ImageGrab.grab = lambda **_k: (_ for _ in ()).throw(AssertionError("capture unused"))
sys.modules.setdefault("PIL", pil); sys.modules.setdefault("PIL.Image", pil.Image)
sys.modules.setdefault("PIL.ImageGrab", pil.ImageGrab)
suite = types.ModuleType("gui_suite"); suite.APPS = ()
sys.modules.setdefault("gui_suite", suite)
OUT = Path(os.environ["V15_OWNER_OUT"])
RAW = None


def emit_stdout(row):
    sys.stdout.write(json.dumps(row, sort_keys=True) + "\n")
    sys.stdout.flush()


def child(display_name, runtime):
    from doom_owner_thread_release_batch_backend_process_v1 import Backend

    class Session:
        name = display_name
        def __init__(self):
            from Xlib.display import Display
            self.d = Display(display_name)

    backend = Backend(Session(), runtime, emit_stdout, {"health": object(), "ammo": object()})
    for line in sys.stdin:
        request = json.loads(line)
        if request.get("op") == "finish":
            # Test fixtures exercise cleanup's external file/event gates. They
            # do not claim that a real scorer or V39 owner-events writer ran.
            backend.close()
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "score.json").write_text('{"fixture":"synthetic"}\n', encoding="utf-8")
            (runtime / "owner-events.json").write_text(
                json.dumps([{"reason": "close", "verified": True}]) + "\n",
                encoding="utf-8")
            emit_stdout({"event": "post_control_score", "fixture": "synthetic"})
            return
    raise EOFError("controller closed stdin before finish request")


def main():
    global RAW
    if len(sys.argv) == 4 and sys.argv[1] == "--child":
        child(sys.argv[2], Path(sys.argv[3])); return
    OUT.mkdir(parents=True, exist_ok=False)
    result = {"schema": "v39-v15-process-owner-xvfb-a30-raw-v1",
              "physical_input": False, "game_or_model": False,
              "synthetic_score_and_owner_events": True, "xvfb_tcp_enabled": False}
    RAW = result
    with tempfile.TemporaryDirectory(prefix="v15-owner-a30-") as td:
        auth = Path(td) / "Xauthority"
        auth.write_bytes(b"")
        env = dict(os.environ, XAUTHORITY=str(auth))
        xvfb = subprocess.Popen(
            ["Xvfb", "-displayfd", "1", "-screen", "0", "640x480x24",
             "-nolisten", "tcp", "-ac"], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, env=env)
        process = None
        reader = None
        try:
            if not select.select([xvfb.stdout], [], [], 5)[0]:
                raise TimeoutError("Xvfb display deadline")
            number = xvfb.stdout.readline().strip()
            if not number.isdecimal():
                raise RuntimeError("invalid Xvfb displayfd")
            display_name = ":" + number
            events, errors = [], []
            event_lock = threading.Lock()
            score_seen = threading.Event()

            def read_stdout():
                try:
                    for line in process.stdout:
                        row = json.loads(line)
                        if type(row) is not dict:
                            raise ValueError("stdout event is not an object")
                        with event_lock:
                            events.append(row)
                        if row.get("event") == "post_control_score":
                            score_seen.set()
                except BaseException as exc:
                    errors.append(type(exc).__name__ + ": " + str(exc))

            process = subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), "--child",
                 display_name, str(OUT)], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                bufsize=1, env=env, start_new_session=True)
            reader = threading.Thread(target=read_stdout, name="a30-stdout-reader")
            reader.start()
            ready_deadline = time.monotonic() + 10
            while time.monotonic() < ready_deadline:
                with event_lock:
                    ready = any(row.get("event") == "input_owner_process_ready" for row in events)
                if ready:
                    break
                if process.poll() is not None:
                    raise RuntimeError("session child exited before owner readiness")
                time.sleep(.02)
            else:
                raise TimeoutError("process-owner ready event deadline")

            from doom_controller_failure_cleanup_v1 import ControllerFailureCleanup

            class Planner:
                def close(self, timeout=1):
                    return None

            def wait_for(predicate, timeout):
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    with event_lock:
                        for row in events:
                            if predicate(row):
                                return row
                    time.sleep(.01)
                raise TimeoutError("event wait deadline")

            cleanup = ControllerFailureCleanup(
                Planner(), OUT, finish_timeout=.5, child_wait_timeout=5,
                escalation_wait_timeout=1, owner_process_recovery=True)
            cleanup.track(process)
            cleanup.observe_output(events, reader, wait_for, OUT, errors)
            primary = RuntimeError("synthetic outer controller failure")
            cleanup.__exit__(RuntimeError, primary, None)
            receipt_path = OUT / "controller-failure.json"
            failure = json.loads(receipt_path.read_text(encoding="utf-8"))
            with event_lock:
                final_events = list(events)
            ready_rows = [r for r in final_events if r.get("event") == "input_owner_process_ready"]
            owner_receipt_path = OUT / "input-owner-process" / "input-owner-recovery-v1.json"
            owner_receipt = json.loads(owner_receipt_path.read_text(encoding="utf-8"))
            result.update({"display": display_name, "child_return_code": process.returncode,
                           "stdout_reader_joined": not reader.is_alive(),
                           "stdout_reader_errors": errors, "events": final_events,
                           "controller_failure": failure,
                           "owner_receipt_sha256": hashlib.sha256(owner_receipt_path.read_bytes()).hexdigest(),
                           "owner_receipt": owner_receipt,
                           "ready_identity": ready_rows[0] if ready_rows else None,
                           "xvfb_tcp_disabled": True})
            identity = ready_rows[0] if len(ready_rows) == 1 else {}
            result["identity_match"] = bool(
                owner_receipt.get("service_pid") == identity.get("service_pid") and
                owner_receipt.get("service_start_ticks") == identity.get("service_start_ticks") and
                owner_receipt.get("owner_id") == identity.get("owner_id"))
            result["pass"] = bool(
                process.returncode == 0 and not reader.is_alive() and not errors and
                score_seen.is_set() and result["identity_match"] and
                owner_receipt.get("receipt_fsynced") is True and
                owner_receipt.get("recovery_verified") is True and
                owner_receipt.get("owner_thread_stopped") is True and
                failure.get("cleanup_complete") is True and
                failure.get("display_reuse_allowed") is True and
                failure.get("owner_process_emergency_recovery_verified") is False and
                failure.get("stdout_reader_retired") is True and
                failure.get("input_terminals_complete") is True and
                failure.get("input_releases_verified_empty") is True and
                failure.get("scorer_terminal_observed") is True and
                failure.get("score_file_present") is True and
                failure.get("owner_events_closed") is True and
                all(row.get("status") == "returned" for row in failure.get("stages", [])))
            if not result["pass"]:
                raise RuntimeError("outer cleanup completion conjunction failed")
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait(timeout=3)
            if reader is not None:
                reader.join(timeout=2)
            xvfb.terminate()
            try:
                result["xvfb_return_code"] = xvfb.wait(timeout=3)
            except subprocess.TimeoutExpired:
                xvfb.kill()
                result["xvfb_return_code"] = xvfb.wait(timeout=3)
            result["xvfb_stderr"] = xvfb.stderr.read()
            xvfb.stdout.close(); xvfb.stderr.close()
            result["pass"] = bool(result.get("pass") and result["xvfb_return_code"] == 0)
            if process is not None:
                result["child_stderr"] = process.stderr.read() if process.stderr else ""
                if process.stdout: process.stdout.close()
                if process.stdin: process.stdin.close()
                if process.stderr: process.stderr.close()
    raw_path = OUT / "RAW.json"
    raw_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"raw": str(raw_path), "pass": result.get("pass")}))
    if not result.get("pass"):
        raise SystemExit(2)


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        if RAW is not None:
            RAW["candidate_error"] = {"type": type(exc).__name__, "message": str(exc)[:1000]}
            RAW["pass"] = False
            if OUT.exists():
                (OUT / "RAW.json").write_text(json.dumps(RAW, indent=2, sort_keys=True) + "\n")
        raise


