"""One-shot real-pipe scorer-during-command-wait construction probe."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
DOOM = HERE.parents[1]
sys.path.insert(0, str(DOOM))

from independent_progress_clock_v2 import ProgressSample  # noqa: E402
from map01_scorer_stdio_adapter_v1 import MainThreadScorerStdin, ScorerFileSink  # noqa: E402


OUTPUT = HERE / "results" / "formal-01"
FREEZE = HERE / "FREEZE.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if OUTPUT.exists():
        raise SystemExit(f"STOP_OUTPUT_EXISTS:{OUTPUT}")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    expected = freeze["pinned_sha256"]
    for relative, digest in expected.items():
        path = (DOOM / relative.removeprefix("components/")) if relative.startswith("components/") else HERE / relative
        actual = sha256(path)
        if actual != digest:
            raise SystemExit(f"STOP_SOURCE_DRIFT:{relative}:{actual}")

    OUTPUT.mkdir(parents=True, exist_ok=False)
    read_fd, write_fd = os.pipe()
    stream = os.fdopen(read_fd, "r", encoding="utf-8", newline="")
    sink = ScorerFileSink(OUTPUT / "scorer")
    experiment_start_ns = time.perf_counter_ns()
    command_sent_ns: list[int] = []
    writer_error: list[str] = []
    command = '{"op":"finish"}'

    def sample_fn() -> ProgressSample:
        elapsed = time.perf_counter_ns() - experiment_start_ns
        kills = int(elapsed >= 60_000_000)
        deaths = int(elapsed >= 140_000_000)
        return ProgressSample(
            sample_ns=time.perf_counter_ns(),
            kill_count=kills,
            death_count=deaths,
            episode_finished=False,
            player_dead=False,
            map_exit=False,
        )

    adapter = MainThreadScorerStdin(stream, sample_fn, sink, sample_hz=35.0)
    wait_started_ns = time.perf_counter_ns()

    def delayed_writer() -> None:
        try:
            time.sleep(0.350)
            command_sent_ns.append(time.perf_counter_ns())
            os.write(write_fd, (command + "\n").encode("utf-8"))
        except BaseException as exc:  # preserved into raw, including harness faults
            writer_error.append(repr(exc))
        finally:
            os.close(write_fd)

    writer = threading.Thread(target=delayed_writer, name="delayed-command-writer")
    writer.start()
    try:
        returned_line = next(adapter)
        command_received_ns = time.perf_counter_ns()
    finally:
        writer.join(timeout=2)
        stream.close()
    if writer.is_alive():
        writer_error.append("writer_thread_join_timeout")

    scheduler = adapter.stats()
    sink_summary = sink.finalize(scheduler)
    sample_rows = [
        json.loads(line)
        for line in (OUTPUT / "scorer" / "scorer-samples.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    event_rows = [
        json.loads(line)
        for line in (OUTPUT / "scorer" / "scorer-events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    raw = {
        "schema": "map01-scorer-command-wait-construction-raw-v1",
        "freeze_sha256": sha256(FREEZE),
        "candidate_sha256": sha256(Path(__file__)),
        "pinned_sha256": expected,
        "runtime": freeze["runtime"],
        "wait_started_ns": wait_started_ns,
        "command_sent_ns": command_sent_ns[0] if command_sent_ns else None,
        "command_received_ns": command_received_ns,
        "requested_command": command,
        "returned_line": returned_line,
        "writer_errors": writer_error,
        "scheduler": scheduler,
        "sink_summary": sink_summary,
        "samples": sample_rows,
        "events": event_rows,
        "candidate_exit_code": 0,
    }
    raw_path = OUTPUT / "RAW.json"
    raw_bytes = (json.dumps(raw, sort_keys=True, indent=2) + "\n").encode("utf-8")
    raw_path.write_bytes(raw_bytes)
    receipt = {"status": "CANDIDATE_EXIT_0", "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
               "raw_bytes": len(raw_bytes), "candidate_pid": os.getpid()}
    (OUTPUT / "RUN.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
