"""Capture child stdout exactly through initial observation, then finish safely.

This bounded diagnostic uses the current V15 session and fixture without an
app-server or model. It preserves each raw stdout line before attempting JSON
decode so a parent reader failure can be attributed to its exact input.
"""
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import threading
import time


REPO = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent / "raw"
FIXTURE = REPO / "research/doom/fixtures/map01-threat-contact-v2/fixture.json"


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, "research/doom/session_map01_v15.py",
               "--out", str(OUT / "runtime"), "--seed", "20261025",
               "--timeout-seconds", "600", "--skill", "1",
               "--load-fixture-manifest", str(FIXTURE),
               "--target-process-identity"]
    process = subprocess.Popen(command, cwd=REPO, env=os.environ.copy(),
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, encoding="utf-8",
                               errors="replace", bufsize=1, start_new_session=True)
    stderr_path = OUT / "stderr.raw"

    def drain_stderr():
        with stderr_path.open("xb") as sink:
            while True:
                chunk = process.stderr.buffer.read(4096)
                if not chunk:
                    return
                sink.write(chunk)
                sink.flush()

    stderr_thread = threading.Thread(target=drain_stderr, daemon=True)
    stderr_thread.start()
    output_path = OUT / "stdout-lines.jsonl"
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    finish_sent = False
    parse_failures = 0
    line_number = 0
    score_seen = False
    deadline = time.monotonic() + 45
    forced_deadline = None
    with output_path.open("x", encoding="utf-8", newline="\n") as sink:
        while True:
            if time.monotonic() >= deadline and forced_deadline is None:
                if not finish_sent and process.poll() is None:
                    process.stdin.write('{"op":"finish"}\n')
                    process.stdin.flush()
                    finish_sent = True
                forced_deadline = time.monotonic() + 10
            if forced_deadline is not None and time.monotonic() >= forced_deadline:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                break
            ready = selector.select(timeout=0.25)
            for key, _ in ready:
                line = key.fileobj.readline()
                if line == "":
                    try:
                        selector.unregister(key.fileobj)
                    except Exception:
                        pass
                    continue
                line_number += 1
                row = {"line_number": line_number, "raw_line": line,
                       "json_valid": False, "event": None}
                try:
                    parsed = json.loads(line)
                    row["json_valid"] = True
                    row["event"] = parsed.get("event") if isinstance(parsed, dict) else None
                    row["id"] = parsed.get("id") if isinstance(parsed, dict) else None
                    if (not finish_sent and parsed.get("event") == "observation" and
                            parsed.get("id") == "initial"):
                        process.stdin.write('{"op":"finish"}\n')
                        process.stdin.flush()
                        finish_sent = True
                    if parsed.get("event") == "post_control_score":
                        score_seen = True
                except Exception as error:
                    parse_failures += 1
                    row["parse_error"] = type(error).__name__
                sink.write(json.dumps(row, separators=(",", ":")) + "\n")
                sink.flush()
            if score_seen and process.poll() is not None:
                break
            if process.poll() is not None and not selector.get_map():
                break
    if process.poll() is None:
        process.wait(timeout=5)
    stderr_thread.join(timeout=5)
    result = {"schema": "map01-v39-session-stdout-probe-result-v1",
              "diagnostic_id": "map01-v39-session-stdout-probe-a01",
              "model_calls": 0, "finish_sent_after_initial_observation": finish_sent,
              "post_control_score_seen": score_seen, "stdout_lines": line_number,
              "stdout_json_parse_failures": parse_failures,
              "child_exit_code": process.returncode,
              "source_stdout_sha256": __import__("hashlib").sha256(
                  output_path.read_bytes()).hexdigest(),
              "scope": "bounded session startup diagnostic; no planner or model"}
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n",
                                    encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0 if score_seen and process.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
