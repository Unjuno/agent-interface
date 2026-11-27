"""Windows overlapped pipe send with deadline and conservative pending custody.

This bounds the overlapped wait, not serialization or the OS call itself.
An expired or uncertain write must quarantine its peer and is never evidence
of non-delivery. A pending OVERLAPPED and its buffer remain owned by the pipe.
"""
from multiprocessing.reduction import ForkingPickler


def send_before(pipe, value, cutoff_ns, *, clock_ns, api=None):
    if api is None:
        import _winapi as api
    pipe._check_closed()
    pipe._check_writable()
    if pipe._send_ov is not None:
        raise RuntimeError("another overlapped write remains pending")
    payload = ForkingPickler.dumps(value)
    if clock_ns() >= cutoff_ns:
        raise TimeoutError("helper send deadline expired before write")
    ov, error = api.WriteFile(pipe.fileno(), payload, overlapped=True)
    pipe._send_ov = ov
    pipe._deadline_pending = (ov, payload)
    completed = False
    try:
        if error == api.ERROR_IO_PENDING:
            remaining_ns = max(0, cutoff_ns - clock_ns())
            timeout_ms = min(remaining_ns // 1_000_000, 0xFFFFFFFE)
            wait_result = api.WaitForMultipleObjects([ov.event], False, timeout_ms)
            if wait_result != api.WAIT_OBJECT_0:
                raise TimeoutError("helper overlapped write not confirmed before cutoff")
        count, error = ov.GetOverlappedResult(False)
        completed = True
        if error != 0 or count != len(payload):
            raise OSError("helper overlapped write incomplete or failed")
        if clock_ns() >= cutoff_ns:
            raise TimeoutError("helper write completed after cutoff")
    except BaseException:
        if not completed:
            try:
                ov.cancel()
            except OSError:
                pass
        raise
    finally:
        if completed:
            pipe._send_ov = None
            pipe._deadline_pending = None
