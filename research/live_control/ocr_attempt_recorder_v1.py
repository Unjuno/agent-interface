"""Record the actual synchronous OCR runner call without retaining image bytes.

The caller owns persistence and must treat missing records as unknown. This
wrapper does not grant input authority, retry, enforce a timeout, or prove what
the operating system executed beyond the arguments passed to the runner.
"""
from __future__ import annotations

import hashlib
import subprocess
import time


def _sha256_or_none(value):
    return hashlib.sha256(value).hexdigest() if isinstance(value, bytes) else None


class OcrAttemptRecorder:
    """Wrap one synchronous subprocess-compatible runner; one row per call."""

    def __init__(self, *, runner=subprocess.run, clock=time.monotonic_ns):
        self._runner = runner
        self._clock = clock
        self.records = []

    def __call__(self, command, *, input, capture_output, timeout, check):
        if not isinstance(command, (list, tuple)) or not command or any(
                not isinstance(item, str) for item in command):
            raise ValueError("OCR command must be a nonempty string sequence")
        if not isinstance(input, bytes):
            raise ValueError("OCR input must be bytes")
        row = {
            "command": list(command),
            "input_sha256": hashlib.sha256(input).hexdigest(),
            "input_bytes": len(input),
            "capture_output": capture_output,
            "timeout_seconds": timeout,
            "check": check,
            "started_ns": self._clock(),
            "ended_ns": None,
            "status": "pending",
            "returncode": None,
            "stdout_sha256": None,
            "stderr_sha256": None,
            "error_type": None,
        }
        self.records.append(row)
        try:
            result = self._runner(command, input=input, capture_output=capture_output,
                                  timeout=timeout, check=check)
            row.update(status="returned", returncode=result.returncode,
                       stdout_sha256=_sha256_or_none(result.stdout),
                       stderr_sha256=_sha256_or_none(result.stderr))
            return result
        except BaseException as error:
            row.update(status="timeout" if isinstance(error, subprocess.TimeoutExpired) else "error",
                       error_type=type(error).__name__,
                       stdout_sha256=_sha256_or_none(getattr(error, "stdout", None)),
                       stderr_sha256=_sha256_or_none(getattr(error, "stderr", None)))
            raise
        finally:
            row["ended_ns"] = self._clock()
