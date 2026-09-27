"""One-shot in-container driver for the live producer/passive-reader probe."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import time


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class JsonLineReader:
    def __init__(self, stream) -> None:
        self.stream = stream
        self.selector = selectors.DefaultSelector()
        self.selector.register(stream, selectors.EVENT_READ)
        self.buffer = bytearray()
        self.raw = bytearray()

    def next_line(self, timeout: float) -> bytes | None:
        deadline = time.monotonic() + timeout
        while True:
            end = self.buffer.find(b"\n")
            if end >= 0:
                line = bytes(self.buffer[:end + 1])
                del self.buffer[:end + 1]
                return line
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("producer stdout line timeout")
            if not self.selector.select(remaining):
                raise TimeoutError("producer stdout line timeout")
            chunk = os.read(self.stream.fileno(), 65536)
            if not chunk:
                return None
            self.raw.extend(chunk)
            self.buffer.extend(chunk)


def verify_freeze(repo: Path, freeze: dict, image_id: str) -> None:
    if freeze.get("image_id") != image_id:
        raise ValueError("IMAGE_ID_MISMATCH")
    for name, expected in freeze["inputs"].items():
        actual = sha256((repo / name).read_bytes())
        if actual != expected:
            raise ValueError(f"SOURCE_HASH_MISMATCH:{name}")


def invoke_reader(repo: Path, stream: Path, stream_id: str,
                  cursor: Path | None, out: Path, label: str) -> dict:
    command = [sys.executable, "-m", "research.integration.event_inbox_reader_v1",
               "--stream", str(stream), "--stream-id", stream_id]
    if cursor is not None:
        command.extend(["--cursor", str(cursor)])
    completed = subprocess.run(command, cwd=repo, capture_output=True, timeout=10, check=False)
    (out / f"{label}_stdout.bin").write_bytes(completed.stdout)
    (out / f"{label}_stderr.bin").write_bytes(completed.stderr)
    response = json.loads(completed.stdout)
    response_bytes = completed.stdout
    write_json(out / f"{label}_meta.json", {
        "argv": command, "returncode": completed.returncode,
        "stdout_sha256": sha256(response_bytes), "stderr_sha256": sha256(completed.stderr),
        "stdout_bytes": len(response_bytes),
    })
    return response


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--image-id", required=True)
    parser.add_argument("--stream-id")
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    stream_id = args.stream_id or freeze["stream_id"]
    started_ns = time.time_ns()
    proc = None
    stdout = None
    producer_stderr = out / "producer_stderr.bin"
    command_lines: list[bytes] = []
    result: dict = {
        "schema": "issue-3876-live-reader-result-v1",
        "allocation": freeze.get("allocation"),
        "stream_id": stream_id,
        "image_id": args.image_id,
        "status": "STOP_RUNNER_NOT_COMPLETED",
        "input_commands_sent": [],
        "reader_passes": [],
        "errors": [],
    }
    try:
        verify_freeze(repo, freeze, args.image_id)
        (out / "freeze.json").write_bytes(args.freeze.read_bytes())
        producer_dir = out / "producer"
        producer_cmd = [
            sys.executable, "research/live_control/interactive_v17.py", "--app", "calc",
            "--seed", "387601", "--out", str(producer_dir), "--presentation", "full",
        ]
        with producer_stderr.open("wb") as err:
            proc = subprocess.Popen(producer_cmd, cwd=repo, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=err, bufsize=0)
            stdout = JsonLineReader(proc.stdout)

            events = []
            saw_ready = saw_initial = False
            while not (saw_ready and saw_initial):
                line = stdout.next_line(30)
                if line is None:
                    raise RuntimeError("PRODUCER_EOF_BEFORE_INITIAL_OBSERVATION")
                command_lines.append(line)
                row = json.loads(line)
                events.append(row)
                saw_ready |= row.get("event") == "ready"
                saw_initial |= row.get("event") == "observation" and row.get("id") == "initial"
            if proc.poll() is not None:
                raise RuntimeError("PRODUCER_NOT_LIVE_AT_FIRST_READ")

            clock_command = {"op": "clock"}
            proc.stdin.write((json.dumps(clock_command, separators=(",", ":")) + "\n").encode())
            proc.stdin.flush()
            result["input_commands_sent"].append(clock_command)
            while True:
                line = stdout.next_line(10)
                if line is None:
                    raise RuntimeError("PRODUCER_EOF_BEFORE_CLOCK_RESPONSE")
                command_lines.append(line)
                row = json.loads(line)
                events.append(row)
                if row.get("event") == "clock":
                    break
            if proc.poll() is not None:
                raise RuntimeError("PRODUCER_EXITED_BEFORE_LIVE_READER")

            stream = producer_dir / "delivered.jsonl"
            first = invoke_reader(repo, stream, stream_id, None, out, "reader1")
            result["reader_passes"].append({"name": "live-prefix-before-finish",
                                            "producer_alive_before": proc.poll() is None,
                                            "record_count": len(first.get("records", [])),
                                            "tail_state": first.get("tail_state"),
                                            "returncode": json.loads((out / "reader1_meta.json").read_text())["returncode"]})
            if proc.poll() is not None:
                raise RuntimeError("PRODUCER_EXITED_DURING_LIVE_READER")
            if not first.get("records") or first.get("tail_state") != "end":
                raise RuntimeError("LIVE_READER_PREFIX_NOT_COMPLETE")
            cursor1 = out / "reader1_cursor.json"
            write_json(cursor1, first["next_cursor"])

            finish_command = {"op": "finish"}
            proc.stdin.write((json.dumps(finish_command, separators=(",", ":")) + "\n").encode())
            proc.stdin.flush()
            result["input_commands_sent"].append(finish_command)
            while True:
                line = stdout.next_line(30)
                if line is None:
                    break
                command_lines.append(line)
                events.append(json.loads(line))
            if stdout.buffer:
                raise RuntimeError("PRODUCER_STDOUT_INCOMPLETE_LINE")
            proc.stdin.close()
            returncode = proc.wait(timeout=10)

            second = invoke_reader(repo, stream, stream_id, cursor1, out, "reader2")
            cursor2 = out / "reader2_cursor.json"
            write_json(cursor2, second["next_cursor"])
            third = invoke_reader(repo, stream, stream_id, cursor2, out, "reader3")
            cursor3 = out / "reader3_cursor.json"
            write_json(cursor3, third["next_cursor"])

            (out / "producer_stdout.jsonl").write_bytes(bytes(stdout.raw))
            run_record = {
                "argv": producer_cmd, "returncode": returncode,
                "image_id": args.image_id,
                "stream_id": stream_id,
                "stdout_line_count": len(command_lines),
                "stdout_sha256": sha256(bytes(stdout.raw)),
                "producer_stderr_sha256": sha256(producer_stderr.read_bytes()),
                "source_manifest": json.loads((producer_dir / "sources.json").read_text()),
                "live_reader_producer_alive": result["reader_passes"][0]["producer_alive_before"],
                "reader1": first, "reader2": second, "reader3": third,
                "event_names_stdout": [row.get("event") for row in events],
                "reader_cursor_files": ["reader1_cursor.json", "reader2_cursor.json", "reader3_cursor.json"],
                "input_commands_sent": result["input_commands_sent"],
                "runtime": {"python": sys.version, "executable": sys.executable,
                             "platform": sys.platform, "started_ns": started_ns,
                             "finished_ns": time.time_ns()},
            }
            write_json(out / "run.json", run_record)
            result.update({"status": "RUN_COMPLETED", "producer_returncode": returncode,
                           "stdout_line_count": len(command_lines),
                           "reader_passes": result["reader_passes"] + [
                               {"name": "terminal-suffix", "record_count": len(second.get("records", [])),
                                "tail_state": second.get("tail_state"),
                                "returncode": json.loads((out / "reader2_meta.json").read_text())["returncode"]},
                               {"name": "final-empty", "record_count": len(third.get("records", [])),
                                "tail_state": third.get("tail_state"),
                                "returncode": json.loads((out / "reader3_meta.json").read_text())["returncode"]}],
                           "event_names_stdout": run_record["event_names_stdout"],
                           "input_commands_sent": result["input_commands_sent"],
                           "source_manifest": run_record["source_manifest"]})
    except Exception as exc:
        result["errors"].append(f"{type(exc).__name__}:{exc}")
        if stdout is not None:
            (out / "producer_stdout.jsonl").write_bytes(bytes(stdout.raw))
        result["status"] = "STOP_RUNNER_EXCEPTION"
    finally:
        if proc is not None and proc.poll() is None:
            try:
                proc.stdin.write(b'{"op":"finish"}\n')
                proc.stdin.flush()
                proc.wait(timeout=8)
            except Exception:
                proc.kill()
                proc.wait()
        if stdout is not None:
            stdout.selector.close()
            if proc and proc.stdout:
                proc.stdout.close()
        if proc and proc.stdin and not proc.stdin.closed:
            proc.stdin.close()

    result["finished_ns"] = time.time_ns()
    write_json(out / "runner_result.json", result)
    manifest_lines = []
    for path in sorted(p for p in out.rglob("*") if p.is_file() and p.name != "SHA256SUMS"):
        rel = path.relative_to(out).as_posix()
        manifest_lines.append(f"{sha256(path.read_bytes())}  {rel}\n")
    (out / "SHA256SUMS").write_text("".join(manifest_lines), encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
