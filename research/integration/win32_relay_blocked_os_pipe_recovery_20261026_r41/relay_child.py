"""R41 relay child: real OS stdout pipe and real supervised-Win32 server."""
import argparse
import asyncio
import json
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


class Context:
    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, *_args):
        return False


def append_event(path, lock, row):
    payload = json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
    with lock:
        with open(path, "a", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()


class TrackingBuffer:
    def __init__(self, stream, event_path, lock):
        self.stream = stream
        self.event_path = event_path
        self.lock = lock
        self.sequence = 0

    def write(self, data):
        self.sequence += 1
        sequence = self.sequence
        started = time.perf_counter_ns()
        append_event(self.event_path, self.lock, {
            "event": "write_started", "sequence": sequence,
            "bytes": len(data), "perf_counter_ns": started})
        try:
            count = self.stream.write(data)
            self.stream.flush()
        except BaseException as error:
            append_event(self.event_path, self.lock, {
                "event": "write_error", "sequence": sequence,
                "error": repr(error), "perf_counter_ns": time.perf_counter_ns()})
            raise
        append_event(self.event_path, self.lock, {
            "event": "write_completed", "sequence": sequence,
            "written": count, "perf_counter_ns": time.perf_counter_ns()})
        return count


class TrackingStdout:
    def __init__(self, stream, event_path):
        self.stream = stream
        self.lock = threading.Lock()
        self.buffer = TrackingBuffer(stream.buffer, event_path, self.lock)

    def write(self, value):
        return self.buffer.write(value.encode("utf-8"))

    def flush(self):
        return self.stream.flush()

    def isatty(self):
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", required=True)
    parser.add_argument("--output-directory", required=True)
    parser.add_argument("--events", required=True)
    args = parser.parse_args()
    from runtime.cli_v1 import mcp_relay
    from runtime.cli_v1.mcp_server import create_server
    from runtime.cli_v1.win32_supervisor_helpers import create_native_win32_components

    targets = json.loads(Path(args.targets).read_text(encoding="utf-8"))
    owner_factory = lambda configured, root, _display: create_native_win32_components(configured, root)[0]
    server = create_server(targets, args.output_directory,
        display_name="Agent Interface Win32 R41 Fixture",
        session_mode="supervised-win32",
        _supervised_win32_owner_factory=owner_factory)
    sidecar = Path(args.events).with_name("relay-events.jsonl")
    event_lock = threading.Lock()
    output = TrackingStdout(sys.stdout, args.events)

    class Client:
        async def initialize(self):
            return None

        async def call_tool(self, name, arguments):
            started = time.perf_counter_ns()
            if name in ("interface_dispatch", "interface_cancel"):
                append_event(sidecar, event_lock, {
                    "event": name + "_started", "perf_counter_ns": started,
                    "arguments": dict(arguments)})
            reply = await server.call_tool(name, arguments)
            if name in ("interface_dispatch", "interface_cancel"):
                texts = [part.text for part in reply.content if part.type == "text"]
                append_event(sidecar, event_lock, {
                    "event": name + "_returned", "perf_counter_ns": time.perf_counter_ns(),
                    "body": json.loads(texts[0]) if len(texts) == 1 else None})
            return reply

    client = Client()
    transport = Context((object(), object()))
    session = Context(client)

    async def run():
        with (patch.object(mcp_relay, "stdio_client", return_value=transport),
              patch.object(mcp_relay, "ClientSession", return_value=session),
              patch.object(mcp_relay.sys, "stdout", output)):
            await mcp_relay.serve([
                "--output-directory", args.output_directory,
                "--targets", args.targets,
                "--session-mode", "supervised-win32"])
        await server.call_tool("interface_close", {})

    asyncio.run(run())


if __name__ == "__main__":
    main()
