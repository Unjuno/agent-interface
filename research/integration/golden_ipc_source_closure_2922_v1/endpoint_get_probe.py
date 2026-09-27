"""One-shot, GET-only private fixture endpoint probe for Issue #2922.

Run inside the pinned historical runtime container with this checkout mounted
read-only. This starts the same session/gui_suite preparation path as
session_v4, requests only the session-owned loopback URL, and verifies that no
submitted-output file appeared.
"""
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path("/repo")
sys.path[:0] = [
    str(ROOT / "research/observation_gating"),
    str(ROOT / "research/observation_tiles"),
    str(ROOT / "research/real_apps_v1"),
    str(ROOT / "research/live_control"),
]
import gui_suite

SEED = 992925
CHROMIUM = "/home/taka/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome"
SOURCES = {
    "research/live_control/executor_v3.py": "ea3fa8c9751a6a41b4814ad6e0d03bec85166765b0a41d2488a51750d17b3a4a",
    "research/live_control/lease.py": "e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f",
    "research/live_control/session_v4.py": "04f06d7b787baa77cae20d0c51b563ccc4985dc19b47308d7c24318c5a9e7fee",
    "research/observation_gating/exact_gate.py": "6780624513a95039657734e76c0420447a3f9ab49f98e1f3137a19a91bc31944",
    "research/observation_gating/gui_suite.py": "953a078a06d55b9278bd7b31e176404912340a4f13407e1db343b7776645e97f",
    "research/observation_tiles/image_artifact.py": "7bf6b71d811aaefa75e87f5d9d20fd9275fc928104e910deaca9e3f00c55363e",
    "research/observation_tiles/tile_transport.py": "f74caf4f2bea59fe3a73b3f04975384d8520bb06c296765566c4dd2542ef12b0",
    "research/real_apps_v1/real_app_suite_v1.py": "22b4cc86af68a0ae866fe24735faaeefa40c0e1722238ab8c04723e1a564db24",
}

def main():
    hashes = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SOURCES}
    assert hashes == SOURCES, "pinned source SHA-256 mismatch"
    session = server = None
    started = time.monotonic_ns()
    result = {
        "schema": "issue2922_private_endpoint_get_probe_v1",
        "allocation": "issue2922-private-endpoint-get-20260927-r1",
        "seed": SEED,
        "repository_commit": "01349d7bc76e5635f5568c53ffeec4d9ff49abb1",
        "source_sha256": hashes,
        "image_requested": "issue-2849-task1-runtime:v3-20260921",
        "network_mode": "none",
        "task_allocated": False,
        "post_requests": 0,
        "model_calls": 0,
        "gui_input": False,
    }
    try:
        session = gui_suite.Session()
        goal, output, server = gui_suite.prepare(session, "chromium", SEED, CHROMIUM)
        result["session_ready"] = True
        result["session_endpoint"] = goal["url"]
        result["output_exists_before"] = output.exists()
        with urllib.request.urlopen(goal["url"], timeout=5) as response:
            body = response.read()
            result.update(
                request_method="GET",
                http_status=response.status,
                content_type=response.headers.get("Content-Type"),
                body_bytes=len(body),
                body_contains_ready_marker=b"AI FORM READY" in body,
            )
        result["output_exists_after"] = output.exists()
        result["container_elapsed_ms"] = (time.monotonic_ns() - started) / 1e6
        result["disposition"] = (
            "PASS_PRIVATE_ENDPOINT_GET_NO_OUTPUT_MUTATION"
            if result["http_status"] == 200
            and result["body_contains_ready_marker"]
            and not result["output_exists_before"]
            and not result["output_exists_after"]
            else "FAIL_PRIVATE_ENDPOINT_GET_GATE"
        )
    except Exception as exc:
        result.update(
            disposition="STOP_OR_FAIL_RUNTIME_GATE",
            error_type=type(exc).__name__,
            error=str(exc),
            container_elapsed_ms=(time.monotonic_ns() - started) / 1e6,
        )
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        if session is not None:
            session.close()
            import shutil
            shutil.rmtree(session.tmp, ignore_errors=True)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["disposition"] == "PASS_PRIVATE_ENDPOINT_GET_NO_OUTPUT_MUTATION" else 1

if __name__ == "__main__":
    raise SystemExit(main())
