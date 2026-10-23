"""One local Linux process-control trial; no X connection or input emission."""
import ast
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def independent_state(pid):
    code = (
        "import json,sys,time; from pathlib import Path; "
        "p=Path('/proc')/sys.argv[1]; "
        "print(json.dumps({'pid':int(sys.argv[1]),'status':(p/'status').read_text(),"
        "'stat':(p/'stat').read_text(),'observed_monotonic_ns':time.monotonic_ns()}))"
    )
    receipt = subprocess.run([sys.executable, "-c", code, str(pid)],
                             capture_output=True, text=True, timeout=3, check=True)
    row = json.loads(receipt.stdout)
    row["state"] = next(line.split(":", 1)[1].strip().split()[0]
                        for line in row["status"].splitlines() if line.startswith("State:"))
    return row


def run():
    result_path = OUT / "result.json"
    if result_path.exists() or (OUT / "attempt-started.json").exists():
        raise RuntimeError("first outcome already exists; refusing replay")
    report = {"status": "RUNNING", "scope": "local WSL2 Linux process signalling only",
              "python": sys.version, "platform": platform.platform(), "cases": [],
              "declared_input_emission_calls": 0, "wslc_operations": 0, "docker_operations": 0}
    child = cleanup_fd = None
    try:
        if (sys.platform != "linux" or not callable(getattr(os, "pidfd_open", None))
                or not callable(getattr(signal, "pidfd_send_signal", None))):
            raise RuntimeError("Linux pidfd APIs unavailable")
        if os.path.lexists("/tmp/.X88-lock") or os.path.lexists("/tmp/.X11-unix/X88"):
            raise RuntimeError("private display slot :88 is already occupied; do not disturb it")
        executable = shutil.which("Xvfb")
        if executable is None:
            raise RuntimeError("Xvfb unavailable; no package install or fallback")
        report["xvfb"] = {"path": executable,
            "sha256": hashlib.sha256(Path(executable).read_bytes()).hexdigest()}
        source_path = ROOT / "runtime/cli_v1/test_mcp_xvfb_blocked_release_integration.py"
        source = source_path.read_text(encoding="utf-8")
        function = next(node for node in ast.parse(source).body
                        if isinstance(node, ast.FunctionDef)
                        and node.name == "_pause_owned_xvfb_for_test")
        report["source"] = {"path": str(source_path.relative_to(ROOT)),
            "normalized_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "function_ast_sha256": hashlib.sha256(ast.dump(function,
                include_attributes=False).encode()).hexdigest()}
        conditions = json.loads((OUT / "conditions.json").read_text())
        if report["source"]["normalized_sha256"] != conditions["helper_normalized_sha256"]:
            raise RuntimeError("frozen helper source changed before execution")
        code = compile(ast.Module(body=[function], type_ignores=[]), str(source_path), "exec")
        with tempfile.TemporaryDirectory(prefix="ai-pidfd-owned-") as temporary:
            log = open(OUT / "xvfb.log", "xb")
            try:
                argv = [executable, ":88", "-screen", "0", "320x240x24", "-nolisten", "tcp"]
                with (OUT / "attempt-started.json").open("x", encoding="utf-8") as marker:
                    marker.write(json.dumps({"argv": argv, "monotonic_ns": time.monotonic_ns(),
                                             "launcher_pid": os.getpid()}) + "\n")
                child = subprocess.Popen(argv, stdout=log, stderr=log)
                cleanup_fd = os.pidfd_open(child.pid, 0)
                report["xvfb"].update(pid=child.pid, argv=argv)
                deadline = time.monotonic() + 5
                while not os.path.exists("/tmp/.X11-unix/X88"):
                    if child.poll() is not None or time.monotonic() >= deadline:
                        raise RuntimeError("owned Xvfb startup failed or timed out")
                    time.sleep(0.01)
                if child.poll() is not None:
                    raise RuntimeError("owned Xvfb exited during readiness")
                report["initial_state"] = independent_state(child.pid)
                os.environ["AGENT_INTERFACE_XVFB_PID"] = str(child.pid)

                for schedule in ("healthy", "status_read_error", "timer_start_error"):
                    row = {"schedule": schedule, "signals": []}
                    report["cases"].append(row)

                    def send(fd, sig):
                        entry = {"signal": int(sig), "fdinfo":
                            Path(f"/proc/self/fdinfo/{fd}").read_text(),
                            "invoked_monotonic_ns": time.monotonic_ns()}
                        row["signals"].append(entry)
                        signal.pidfd_send_signal(fd, sig)
                        entry["returned_monotonic_ns"] = time.monotonic_ns()

                    def fault_path(*parts):
                        path = Path(*parts)
                        if path == Path("/proc", str(child.pid), "status"):
                            def fail():
                                raise OSError("declared injected post-STOP status read failure")
                            return SimpleNamespace(read_text=fail)
                        return path

                    class FailedTimer:
                        def __init__(self, *_args):
                            pass

                        def start(self):
                            raise RuntimeError("declared injected resume timer startup failure")

                    namespace = {"os": os, "Path": fault_path if schedule == "status_read_error"
                        else Path, "time": time, "signal": SimpleNamespace(SIGSTOP=signal.SIGSTOP,
                        SIGCONT=signal.SIGCONT, pidfd_send_signal=send), "threading":
                        SimpleNamespace(Lock=threading.Lock, Timer=FailedTimer)
                        if schedule == "timer_start_error" else threading}
                    exec(code, namespace)
                    try:
                        pause, timer, _resume = namespace[function.name](500)
                    except (OSError, RuntimeError) as error:
                        row["exception"] = repr(error)
                        if schedule == "healthy":
                            raise
                    else:
                        if schedule != "healthy":
                            raise RuntimeError("declared fault did not occur")
                        row["stopped_readback"] = independent_state(child.pid)
                        timer.join(2)
                        if timer.is_alive():
                            raise RuntimeError("resume timer failed to finish")
                        row["pause_receipt"] = pause
                        if pause["resumed"]["error"] or pause["resumed"]["monotonic_ns"] is None:
                            raise RuntimeError("resume receipt unconfirmed")
                    row["resumed_readback"] = independent_state(child.pid)
                    if row["resumed_readback"]["state"] in ("T", "t", "Z"):
                        raise RuntimeError("independent observer did not find a resumed live process")
                    if [item["signal"] for item in row["signals"]] != [signal.SIGSTOP, signal.SIGCONT]:
                        raise RuntimeError("unexpected signal sequence")
                    if schedule == "healthy" and row["stopped_readback"]["state"] not in ("T", "t"):
                        raise RuntimeError("independent observer did not find the stopped process")
                    row["status"] = "PASS_PROCESS_SIGNALLING_SCOPED"
                report["status"] = "PASS_PROCESS_SIGNALLING_SCOPED"
            finally:
                log.close()
    except BaseException:
        report["status"] = "FAIL" if child is not None else "HOLD_BEFORE_PROCESS_START"
        report["error"] = traceback.format_exc()
    finally:
        cleanup = {"signals": []}
        report["cleanup"] = cleanup
        if child is not None and cleanup_fd is not None:
            try:
                if child.poll() is None:
                    for sig in (signal.SIGCONT, signal.SIGTERM):
                        signal.pidfd_send_signal(cleanup_fd, sig)
                        cleanup["signals"].append(int(sig))
                    try:
                        child.wait(2)
                    except subprocess.TimeoutExpired:
                        signal.pidfd_send_signal(cleanup_fd, signal.SIGKILL)
                        cleanup["signals"].append(int(signal.SIGKILL))
                        child.wait(2)
                cleanup["exit_code"] = child.returncode
                cleanup["confirmed_exited"] = child.poll() is not None
            except BaseException:
                cleanup["error"] = traceback.format_exc()
                report["status"] = "FAIL_CLEANUP"
            finally:
                os.close(cleanup_fd)
        elif child is not None:
            # Only this Popen object's unreaped child is eligible for this
            # pre-pidfd failure cleanup; never discover or reopen another PID.
            try:
                child.terminate()
                try:
                    child.wait(2)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(2)
                cleanup.update(method="owned_child_before_pidfd_acquisition",
                               exit_code=child.returncode, confirmed_exited=True)
            except BaseException:
                cleanup["error"] = traceback.format_exc()
                report["status"] = "UNKNOWN_PROCESS_CLEANUP"
        result_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "result": str(result_path)}, sort_keys=True))
    return 0 if report["status"] == "PASS_PROCESS_SIGNALLING_SCOPED" else 1


if __name__ == "__main__":
    sys.exit(run())
