"""Run the actual session_v4 CLI and probe its private endpoint after ready."""
import hashlib
import json
import selectors
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path("/repo")
OUT = Path("/out")
SEED = 992926
IMAGE_ID = "sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393"
COMMIT = "01349d7bc76e5635f5568c53ffeec4d9ff49abb1"
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

def emit_file(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

def main():
    t0 = time.monotonic_ns()
    actual = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SOURCES}
    if actual != SOURCES:
        raise SystemExit("STOP_SOURCE_HASH_MISMATCH")
    run_out = OUT / "session"
    if run_out.exists():
        raise SystemExit("STOP_OUTPUT_PATH_PREEXISTS")
    command = [sys.executable, str(ROOT / "research/live_control/session_v4.py"),
               "--app", "chromium", "--seed", str(SEED), "--out", str(run_out),
               "--chromium", CHROMIUM]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    selector = selectors.DefaultSelector()
    selector.register(proc.stdout, selectors.EVENT_READ)
    lines = []
    result = {
        "schema": "issue2922_session_cli_endpoint_get_v1",
        "allocation": "issue2922-session-cli-endpoint-get-20260927-r1",
        "seed": SEED, "repository_commit": COMMIT, "runtime_image": IMAGE_ID,
        "source_sha256": actual, "task_allocated": False,
        "model_calls": 0, "gui_input": False, "probe_POST_calls_issued": 0,
        "server_POST_count": "not instrumented",
    }
    try:
        deadline = time.monotonic() + 30
        ready = None
        while time.monotonic() < deadline:
            if not selector.select(timeout=max(0, deadline - time.monotonic())):
                break
            line = proc.stdout.readline()
            if not line:
                break
            lines.append(line)
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("event") == "ready":
                ready = event
                break
        if ready is None:
            result.update(disposition="STOP_SESSION_READY_NOT_REACHED")
        else:
            url = ready.get("goal", {}).get("url")
            parsed = urllib.parse.urlparse(url or "")
            if parsed.scheme != "http" or parsed.hostname != "127.0.0.1":
                result.update(disposition="FAIL_READY_URL_NOT_PRIVATE_LOOPBACK")
            else:
                result["ready_event"] = True
                result["ready_before_get"] = True
                result["session_endpoint_host"] = parsed.hostname
                with urllib.request.urlopen(url, timeout=5) as response:
                    body = response.read()
                    result.update(request_method="GET", http_status=response.status,
                                  content_type=response.headers.get("Content-Type"),
                                  body_bytes=len(body),
                                  body_contains_ready_marker=b"AI FORM READY" in body)
                result["disposition"] = (
                    "PASS_CLI_READY_PRIVATE_ENDPOINT_GET_NO_TASK"
                    if result["http_status"] == 200 and result["body_bytes"] == 187
                    and result["body_contains_ready_marker"]
                    else "FAIL_PRIVATE_ENDPOINT_GET_GATE")
        if proc.poll() is None:
            proc.stdin.write(json.dumps({"op": "finish"}) + "\n")
            proc.stdin.flush()
            rest, _ = proc.communicate(timeout=20)
            lines.extend(rest.splitlines(keepends=True))
        result["container_exit_code"] = proc.returncode
        try:
            events = [json.loads(line) for line in lines if line.lstrip().startswith("{")]
        except ValueError:
            events = []
        result["event_names"] = [e.get("event") for e in events]
        result["submit_commands"] = sum(
            e.get("event") == "command" and e.get("command", {}).get("op") == "submit"
            for e in events)
        result["input_admission_events"] = sum(e.get("event") == "input_admission" for e in events)
        evaluations = [e for e in events if e.get("event") == "independent_evaluation"]
        result["independent_evaluation"] = evaluations[-1] if evaluations else None
        result["cli_output_directory_exists"] = run_out.is_dir()
        result["elapsed_ms"] = (time.monotonic_ns() - t0) / 1e6
        if result["disposition"] == "PASS_CLI_READY_PRIVATE_ENDPOINT_GET_NO_TASK":
            if proc.returncode != 0 or result["submit_commands"] or result["input_admission_events"]:
                result["disposition"] = "FAIL_TASK_BOUNDARY_OR_EXIT"
            elif (not evaluations or evaluations[-1].get("success") is not False):
                result["disposition"] = "HOLD_NO_TASK_EFFECT_ORACLE_UNCLEAR"
    except Exception as exc:
        result.update(disposition="STOP_OR_FAIL_SESSION_CLI_PROBE",
                      error_type=type(exc).__name__, error=str(exc))
        if proc.poll() is None:
            try:
                proc.stdin.write(json.dumps({"op": "finish"}) + "\n")
                proc.stdin.flush()
                rest, _ = proc.communicate(timeout=10)
                lines.extend(rest.splitlines(keepends=True))
            except Exception:
                proc.terminate()
                proc.wait(timeout=5)
        result["container_exit_code"] = proc.returncode
    finally:
        selector.close()
        if proc.stdout:
            proc.stdout.close()
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "session_cli_stdout.jsonl").write_text("".join(lines))
        emit_file(OUT / "session_cli_result.json", result)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if result["disposition"] == "PASS_CLI_READY_PRIVATE_ENDPOINT_GET_NO_TASK" else 1

if __name__ == "__main__":
    raise SystemExit(main())
