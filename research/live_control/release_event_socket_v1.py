"""Private Unix JSON delivery for release/terminal cursor comparisons."""
import json
from pathlib import Path
import socketserver
import tempfile
import threading
import time

from release_event_cursor_v1 import EventCursor


class ReleaseEventSocket:
    def __init__(self):
        self.cursor = EventCursor(); self.requests = []; self._condition = threading.Condition()
        self._private = tempfile.TemporaryDirectory(prefix="agent-interface-release-")
        self.path = Path(self._private.name) / "events.sock"
        owner = self
        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                received_ns = time.perf_counter_ns()
                request = json.loads(self.rfile.readline(16385))
                if set(request) != {"after", "events", "timeout", "action_id", "request_id"}:
                    raise ValueError("exact release read request required")
                with owner._condition:
                    owner.requests.append({"request_id": request["request_id"],
                                           "received_ns": received_ns,
                                           "request": request})
                    owner._condition.notify_all()
                result = owner.cursor.read_until(
                    request["after"], request["events"], request["timeout"],
                    request["action_id"])
                result["request_id"] = request["request_id"]
                result["server_response_ns"] = time.perf_counter_ns()
                self.wfile.write((json.dumps(result) + "\n").encode()); self.wfile.flush()
        class Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
            daemon_threads = True
        self.server = Server(str(self.path), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def append(self, event): return self.cursor.append(event)

    def wait_requests(self, count, timeout=2):
        deadline = time.monotonic() + timeout
        with self._condition:
            while len(self.requests) < count:
                remaining = deadline - time.monotonic()
                if remaining <= 0: return False
                self._condition.wait(remaining)
            return True

    def close(self):
        self.cursor.close(); self.server.shutdown(); self.thread.join()
        self.server.server_close(); self._private.cleanup()
