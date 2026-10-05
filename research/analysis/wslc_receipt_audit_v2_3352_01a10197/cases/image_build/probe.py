"""Tiny deterministic entrypoint for the Dockerless WSLc build/run smoke."""
from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path


EXPECTED = b"agent-interface-wslc-build-smoke-v1\n"
payload = Path("/opt/agent-interface-wslc-build-smoke/payload.txt").read_bytes()
if platform.system() != "Linux":
    raise SystemExit("expected Linux container")
if payload != EXPECTED:
    raise SystemExit("copied build-context payload mismatch")

print(json.dumps({
    "schema": "wslc-dockerfile-build-smoke-v1",
    "status": "PASS_WSLc_DOCKERFILE_BUILD_RUN_SMOKE",
    "platform": platform.system(),
    "python": platform.python_version(),
    "payload_bytes": len(payload),
    "payload_sha256": hashlib.sha256(payload).hexdigest(),
}, sort_keys=True, separators=(",", ":")))
