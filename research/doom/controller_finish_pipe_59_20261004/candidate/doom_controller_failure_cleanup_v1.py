"""Best-effort owned cleanup preserving the controller's primary failure."""
import atexit
import json
from pathlib import Path
import threading


FINISH_WRITE_TIMEOUT_SECONDS = 0.5
FINISH_WRITER_JOIN_TIMEOUT_SECONDS = 0.25


def _send_finish_bounded(child, timeout=FINISH_WRITE_TIMEOUT_SECONDS):
    """Write finish on a daemon worker so a full pipe cannot pin cleanup."""
    outcome = {"status": "pending", "timeout_seconds": timeout}

    def write_finish():
        try:
            child.stdin.write('{"op":"finish"}\n')
            child.stdin.flush()
            outcome["status"] = "sent"
        except BaseException as error:
            outcome["status"] = "error"
            outcome["error_type"] = type(error).__name__

    writer = threading.Thread(target=write_finish, name="cleanup-finish-writer",
                              daemon=True)
    writer.start()
    writer.join(timeout)
    if writer.is_alive():
        outcome["status"] = "timed_out"
    return dict(outcome), writer


class ControllerFailureCleanup:
    def __init__(self, planner, out):
        self.planner = planner
        self.out = Path(out)
        self.process = None

    def track(self, process):
        self.process = process

    def __enter__(self):
        return self

    def __exit__(self, kind, error, traceback):
        if error is None:
            return False
        receipt = {
            "format": "controller-failure-cleanup-v1",
            "primary_error_type": kind.__name__,
            "stages": [],
            "input_release_verified": False,
            "scope": "owned child process only; no physical release or scorer certificate",
        }

        def attempt(name, operation):
            try:
                result = operation()
                receipt["stages"].append(
                    {"stage": name, "status": "returned", "result": result})
                return True
            except BaseException as secondary:
                receipt["stages"].append(
                    {"stage": name, "status": "failed",
                     "error_type": type(secondary).__name__})
                try:
                    error.add_note(name + " cleanup failed: " +
                                   type(secondary).__name__)
                except BaseException:
                    pass
                return False

        finish_writer = None
        child = self.process
        if child is not None:
            polled = attempt("child_poll_before", child.poll)
            if not polled or receipt["stages"][-1]["result"] is None:
                def send_finish():
                    nonlocal finish_writer
                    result, finish_writer = _send_finish_bounded(child)
                    return result

                sent = attempt("finish_send", send_finish)
                finish_result = (receipt["stages"][-1]["result"] if sent else
                                 {"status": "error"})
                if finish_result.get("status") == "sent":
                    if not attempt("child_wait", lambda: child.wait(timeout=5)):
                        attempt("child_terminate", child.terminate)
                        if not attempt("terminated_wait", lambda: child.wait(timeout=1)):
                            attempt("child_kill", child.kill)
                            attempt("killed_wait", lambda: child.wait(timeout=1))
                else:
                    reason = finish_result.get("status", "error")
                    try:
                        error.add_note("finish_send did not complete (" + reason +
                                       "); proceeding to owned-child retirement")
                    except BaseException:
                        pass
                    receipt["stages"].append(
                        {"stage": "child_wait", "status": "skipped",
                         "reason": "finish_send_" + reason})
                    poll_ok = attempt("child_poll_after_finish_failure", child.poll)
                    if not poll_ok or receipt["stages"][-1]["result"] is None:
                        attempt("child_terminate", child.terminate)
                        if not attempt("terminated_wait", lambda: child.wait(timeout=1)):
                            attempt("child_kill", child.kill)
                            attempt("killed_wait", lambda: child.wait(timeout=1))

                if finish_writer is not None:
                    joined = attempt(
                        "finish_writer_join",
                        lambda: _join_finish_writer(finish_writer))
                    if joined and not receipt["stages"][-1]["result"]["joined"]:
                        try:
                            error.add_note("finish writer remained blocked after child cleanup")
                        except BaseException:
                            pass

            if attempt("child_poll_after", child.poll):
                receipt["child_exit_code"] = receipt["stages"][-1]["result"]
        if attempt("planner_close", lambda: self.planner.close(timeout=1)):
            attempt("atexit_unregister", lambda: atexit.unregister(self.planner.close))
        attempt("failure_receipt_write", lambda: (
            self.out / "controller-failure.json").write_text(
                json.dumps(receipt, indent=2) + "\n"))
        return False


def _join_finish_writer(writer):
    writer.join(FINISH_WRITER_JOIN_TIMEOUT_SECONDS)
    return {"joined": not writer.is_alive()}
