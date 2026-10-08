"""Disposable scope-key transport study. No runtime, OS input or effect authority."""
import argparse
import concurrent.futures
import hashlib
import json
import platform
import socket
import threading
import time
from pathlib import Path

FIELDS = {"verifier", "source", "source_instance", "target", "generation", "dependency",
          "predicate", "parameter", "window_start", "window_end", "role"}
MODES = ("independent", "predicate_inflight", "scope_inflight", "scope_cache")


def wire(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def receive(sock):
    data = b""
    while not data.endswith(b"\n"):
        block = sock.recv(8192)
        if not block:
            raise EOFError("incomplete socket message")
        data += block
        if len(data) > 8192:
            raise ValueError("message bound")
    return data


class Transport:
    def __init__(self):
        self.gate = threading.Event()
        self.rows = []
        self.lock = threading.Lock()
        self.errors = []
        self.active_server_threads = 0

    def emit(self, event, **fields):
        with self.lock:
            self.rows.append(dict(index=len(self.rows), event=event, monotonic_ns=time.monotonic_ns(), **fields))

    def read(self, call_id, scope):
        client, server = socket.socketpair()
        client.settimeout(2.0)
        server.settimeout(2.0)

        def serve():
            with self.lock:
                self.active_server_threads += 1
            try:
                request_bytes = receive(server)
                request = json.loads(request_bytes)
                self.emit("server_received", call_id=call_id, request=request,
                          wire_hex=request_bytes.hex(), sha256=hashlib.sha256(request_bytes).hexdigest())
                if not self.gate.wait(2.0):
                    raise TimeoutError("construction barrier")
                response = dict(call_id=call_id, scope=request["scope"],
                                role="read_only_descriptive", answer=True)
                response_bytes = wire(response)
                server.sendall(response_bytes)
                self.emit("server_sent", call_id=call_id, response=response,
                          wire_hex=response_bytes.hex(), sha256=hashlib.sha256(response_bytes).hexdigest())
            except Exception as exc:
                with self.lock:
                    self.errors.append(type(exc).__name__)
            finally:
                server.close()
                with self.lock:
                    self.active_server_threads -= 1

        worker = threading.Thread(target=serve, name="study-owned-socket", daemon=False)
        worker.start()
        try:
            request_bytes = wire(dict(call_id=call_id, scope=scope))
            client.sendall(request_bytes)
            response_bytes = receive(client)
            response = json.loads(response_bytes)
            self.emit("client_received", call_id=call_id, response=response,
                      wire_hex=response_bytes.hex(), sha256=hashlib.sha256(response_bytes).hexdigest())
            return response
        finally:
            client.close()
            worker.join(3.0)
            if worker.is_alive():
                raise RuntimeError("owned server thread did not terminate")


class Broker:
    def __init__(self, mode, transport):
        if mode not in MODES:
            raise ValueError("mode")
        self.mode = mode
        self.transport = transport
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.pending = {}
        self.next_id = 0

    def request(self, scope):
        if type(scope) is not dict or set(scope) != FIELDS or any(type(x) is not str or not x for x in scope.values()):
            raise ValueError("scope")
        if scope["role"] != "read_only_descriptive":
            raise ValueError("read-only role")
        if self.mode == "independent":
            key = str(self.next_id)
        elif self.mode == "predicate_inflight":
            key = scope["predicate"]
        else:
            key = json.dumps(scope, sort_keys=True, separators=(",", ":"))
        if self.mode != "scope_cache" and key in self.pending and self.pending[key][1].done():
            del self.pending[key]
        if key not in self.pending:
            call_id = f"rpc-{self.next_id}"
            self.next_id += 1
            self.pending[key] = (call_id, self.pool.submit(self.transport.read, call_id, dict(scope)))
        return self.pending[key]

    def close(self):
        self.transport.gate.set()
        self.pool.shutdown(wait=True, cancel_futures=False)


def run_case(case, mode):
    transport = Transport()
    broker = Broker(mode, transport)
    callers = []
    try:
        for wave_index, wave in enumerate(case["waves"]):
            transport.gate.clear()
            submitted = [(request, *broker.request(request["scope"])) for request in wave]
            # All waiter registrations precede release of the owned transport barrier.
            # This admits no truth/oracle information into the broker.
            transport.gate.set()
            for request, call_id, future in submitted:
                response = future.result(timeout=4.0)
                callers.append(dict(id=request["id"], wave=wave_index,
                                    required_scope=request["scope"], call_id=call_id,
                                    response=response,
                                    descriptive_match=response["scope"] == request["scope"],
                                    role=response["role"]))
        result = dict(case_id=case["id"], mode=mode, callers=callers,
                      server_events=transport.rows, transport_errors=transport.errors)
    finally:
        broker.close()
    result["active_server_threads_after_cleanup"] = transport.active_server_threads
    result["producer_threads_joined"] = True
    return result


def run(fixtures):
    return dict(schema="socket-scope-transfer-v1",
                environment=dict(python=platform.python_version(), system=platform.system(), machine=platform.machine()),
                trials=[run_case(case, mode) for case in fixtures["cases"] for mode in MODES])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("fixtures", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    fixtures = json.loads(args.fixtures.read_text())
    result = run(fixtures)
    with args.output.open("x") as out:
        json.dump(result, out, indent=2, sort_keys=True)
        out.write("\n")
    print(json.dumps(dict(trials=len(result["trials"]), callers=sum(len(x["callers"]) for x in result["trials"]))))
