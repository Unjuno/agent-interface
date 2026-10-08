"""Owned inert JSONL echo peer. No model, GUI, or external effect."""
import argparse
import json
import os
from pathlib import Path
import sys
import time


def write_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
        stream.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    root = args.directory
    events = (root / "peer_events.jsonl").open("x", encoding="utf-8", newline="\n")
    received = (root / "peer_received.bin").open("xb", buffering=0)
    responses = (root / "peer_responses.bin").open("xb", buffering=0)
    sequence = 0

    def event(name, **extra):
        nonlocal sequence
        row = {"seq": sequence, "event": name, "monotonic_ns": time.monotonic_ns(),
               "extra": extra}
        sequence += 1
        events.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        events.flush()
        return row["monotonic_ns"]

    try:
        ready_ns = event("peer_ready", pid=os.getpid(), parent_pid=os.getppid())
        ready_temporary = root / "peer_ready.pending.json"
        write_json(ready_temporary,
                   {"pid": os.getpid(), "parent_pid": os.getppid(), "monotonic_ns": ready_ns})
        ready_temporary.rename(root / "peer_ready.json")
        pending = b""
        while True:
            chunk = os.read(0, 4096)
            if not chunk:
                event("stdin_eof", pending_hex=pending.hex())
                break
            received.write(chunk)
            event("read_chunk", bytes=len(chunk), bytes_hex=chunk.hex())
            pending += chunk
            while b"\n" in pending:
                record, pending = pending.split(b"\n", 1)
                wire = record + b"\n"
                message = json.loads(record.decode("utf-8"))
                event("complete_jsonl", bytes=len(wire), raw_hex=wire.hex(), parsed=message)
                response = {"id": message["id"], "result": message["params"]}
                response_wire = (json.dumps(response, separators=(",", ":")) + "\n").encode("utf-8")
                responses.write(response_wire)
                sys.stdout.buffer.write(response_wire)
                sys.stdout.buffer.flush()
                event("response_written", bytes=len(response_wire), raw_hex=response_wire.hex(),
                      parsed=response)
        event("peer_exit", exit_code=0)
        return 0
    except BaseException as error:
        event("peer_error", exception_type=type(error).__name__, message=str(error))
        raise
    finally:
        received.close()
        responses.close()
        events.close()


if __name__ == "__main__":
    raise SystemExit(main())
