"""R31 trace-only wrappers for current-main cancellation recovery boundaries."""
import json
import os
import sys
import time

ROOT = os.environ.get("AGENT_INTERFACE_REPO_ROOT")
if ROOT and ROOT not in sys.path:
    sys.path.insert(0, ROOT)
TRACE = os.environ.get("AGENT_INTERFACE_CANCEL_TRACE")


def emit(event, **fields):
    if not TRACE:
        return
    row = {"event": event, "pid": os.getpid(),
           "monotonic_ns": time.perf_counter_ns(), **fields}
    fd = os.open(TRACE, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
    try:
        os.write(fd, (json.dumps(row, sort_keys=True) + "\n").encode("utf-8"))
    finally:
        os.close(fd)


emit("sitecustomize_loaded")
try:
    from runtime.guarded_win32_v1.process_cancellation import OperationCancellationSupervisor
    _exchange_helper = OperationCancellationSupervisor._exchange_helper

    def traced_exchange(self, name, request, deadline_ns):
        emit("exchange_enter", helper=name,
             request_id=request.get("request_id"),
             recovery_id=request.get("recovery_id"),
             deadline_ns=deadline_ns)
        started = time.perf_counter_ns()
        try:
            result = _exchange_helper(self, name, request, deadline_ns)
        except BaseException as error:
            emit("exchange_exception", helper=name,
                 request_id=request.get("request_id"),
                 elapsed_ns=time.perf_counter_ns() - started,
                 error_type=type(error).__name__, error=str(error)[:160])
            raise
        emit("exchange_return", helper=name,
             request_id=request.get("request_id"),
             elapsed_ns=time.perf_counter_ns() - started,
             result_release_accepted=(result.get("release_accepted")
                                      if type(result) is dict else None),
             result_neutral=(result.get("neutral")
                             if type(result) is dict else None))
        return result

    OperationCancellationSupervisor._exchange_helper = traced_exchange

    from runtime.cli_v1 import win32_supervisor_helpers as helpers
    _helper_main = helpers._helper_main
    _recover = helpers._recover

    def traced_helper_main(kind, targets, connection):
        emit("helper_enter", helper=kind)
        try:
            return _helper_main(kind, targets, connection)
        finally:
            emit("helper_exit", helper=kind)

    def traced_recover(request, *args, **kwargs):
        emit("recover_enter", recovery_id=(request.get("recovery_id")
                                           if type(request) is dict else None),
             operation_id=(request.get("operation_id")
                           if type(request) is dict else None))
        started = time.perf_counter_ns()
        try:
            result = _recover(request, *args, **kwargs)
        except BaseException as error:
            emit("recover_exception", recovery_id=(request.get("recovery_id") if type(request) is dict else None),
                 operation_id=(request.get("operation_id") if type(request) is dict else None),
                 elapsed_ns=time.perf_counter_ns() - started,
                 error_type=type(error).__name__, error=str(error)[:160])
            raise
        emit("recover_return", recovery_id=(request.get("recovery_id") if type(request) is dict else None),
             operation_id=(request.get("operation_id") if type(request) is dict else None),
             elapsed_ns=time.perf_counter_ns() - started,
             release_accepted=(result.get("release_accepted")
                              if type(result) is dict else None))
        return result

    helpers._helper_main = traced_helper_main
    helpers._recover = traced_recover

    from runtime.backends.win32_v1.backend import Win32Backend
    _release_all = Win32Backend.release_all
    _send = Win32Backend._send

    def traced_release_all(self, *args, **kwargs):
        emit("release_all_enter")
        started = time.perf_counter_ns()
        try:
            result = _release_all(self, *args, **kwargs)
        except BaseException as error:
            emit("release_all_exception", elapsed_ns=time.perf_counter_ns() - started,
                 error_type=type(error).__name__, error=str(error)[:160])
            raise
        emit("release_all_return", elapsed_ns=time.perf_counter_ns() - started,
             verified=(result.get("verified") if type(result) is dict else None))
        return result

    def traced_send(self, item, *args, **kwargs):
        input_type = int(item.type)
        event = {"input_type": input_type}
        if input_type == 1:
            event.update(vk=int(item.ki.wVk), scan_code=int(item.ki.wScan),
                         flags=int(item.ki.dwFlags),
                         key_up=bool(int(item.ki.dwFlags) & 0x0002))
        else:
            event.update(mouse_flags=int(item.mi.dwFlags))
        emit("sendinput_enter", **event)
        started = time.perf_counter_ns()
        try:
            result = _send(self, item, *args, **kwargs)
        except BaseException as error:
            emit("sendinput_exception", **event,
                 elapsed_ns=time.perf_counter_ns() - started,
                 error_type=type(error).__name__, error=str(error)[:160])
            raise
        emit("sendinput_return", **event,
             elapsed_ns=time.perf_counter_ns() - started)
        return result

    Win32Backend.release_all = traced_release_all
    Win32Backend._send = traced_send
    emit("recovery_trace_wrappers_installed")
except BaseException as error:
    emit("instrumentation_import_error", error_type=type(error).__name__,
         error=str(error)[:256])