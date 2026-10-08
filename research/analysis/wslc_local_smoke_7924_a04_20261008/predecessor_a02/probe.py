"""One-shot offline/read-only WSLc source-mount probe for Issue #7924 A02."""
import errno
import hashlib
import json
import os
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURE = Path("/src/fixture.txt")
WRITE_TARGET = Path("/src/.wslc-write-probe-7924-a02")


def main():
    expected = os.environ["FIXTURE_SHA256"]
    payload = FIXTURE.read_bytes()
    actual = hashlib.sha256(payload).hexdigest()
    write_error = None
    try:
        WRITE_TARGET.write_text("unexpected writable source mount\n", encoding="utf-8")
    except OSError as exc:
        write_error = exc.errno
    result = {
        "schema": "wslc-local-smoke-7924-a02-v1",
        "fixture_sha256": actual,
        "expected_fixture_sha256": expected,
        "read_only_write_errno": write_error,
        "python": platform.python_version(),
        "container_network_mode": "none (requested by frozen command)",
        "model_calls": 0,
        "gui_calls": 0,
        "external_network_calls": 0,
        "status": "PASS_PORTABILITY_SCOPED"
        if actual == expected and write_error == errno.EROFS
        else "FAIL_PORTABILITY_CHECK",
    }
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS_PORTABILITY_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
