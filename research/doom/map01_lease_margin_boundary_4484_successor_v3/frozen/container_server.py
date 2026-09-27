#!/usr/bin/env python3
"""Private AF_UNIX JSON server around the production Lease class."""
import argparse
import importlib.util
import json
from pathlib import Path
import socket
import signal
import platform
import sys
import time
import traceback


def load_lease(path):
    spec = importlib.util.spec_from_file_location("pinned_production_lease", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Lease, module.Expired


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--socket", required=True, type=Path)
    ap.add_argument("--ready", required=True, type=Path)
    ap.add_argument("--journal", required=True, type=Path)
    ap.add_argument("--lease-source", required=True, type=Path)
    args = ap.parse_args()
    Lease, Expired = load_lease(args.lease_source)
    stopping = False
    def stop_handler(_signum, _frame):
        nonlocal stopping
        stopping = True
        try:
            server.close()
        except Exception:
            pass
    signal.signal(signal.SIGTERM, stop_handler)
    args.socket.unlink(missing_ok=True)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(args.socket))
    server.listen(8)
    args.ready.write_text(json.dumps({"ready": True,
                                      "container_pid": __import__("os").getpid(),
                                      "container_clock_ns": time.perf_counter_ns(),
                                      "platform": platform.platform(),
                                      "python": sys.version,
                                      "perf_counter": str(time.get_clock_info("perf_counter")),
                                      "uid": __import__("os").getuid()})+"\n")
    try:
        while True:
            try:
                connection, _ = server.accept()
            except OSError:
                if stopping:
                    break
                raise
            with connection:
                stream = connection.makefile("rb")
                payload = stream.readline(16385)
                c2 = time.perf_counter_ns()
                if not payload or len(payload) > 16384:
                    continue
                request = json.loads(payload)
                response = {"request_id": request.get("request_id"),
                            "container_receive_ns": c2,
                            "container_clock_ns": time.perf_counter_ns()}
                if request.get("kind") == "lease":
                    delay_ns = int(request.get("delay_ns", 0))
                    if delay_ns:
                        time.sleep(delay_ns / 1e9)
                    response["validation_start_ns"] = time.perf_counter_ns()
                    try:
                        lease = Lease(request["deadline_ns"])
                        lease.check()
                        sample_ns = time.perf_counter_ns()
                        response.update({"decision": "accepted",
                                         "lease_deadline_ns": lease.deadline,
                                         "remaining_sample_ns": sample_ns,
                                         "remaining_ns": lease.deadline-sample_ns})
                    except Expired:
                        response["decision"] = "expired"
                    except ValueError as exc:
                        response.update({"decision": "rejected",
                                         "reason": str(exc)})
                    response["validation_end_ns"] = time.perf_counter_ns()
                c3 = time.perf_counter_ns()
                response["container_send_ns"] = c3
                encoded = (json.dumps(response, sort_keys=True,
                                      separators=(",", ":"))+"\n").encode("utf-8")
                connection.sendall(encoded)
                with args.journal.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({"request": request,
                                        "response": response}, sort_keys=True)+"\n")
                    f.flush()
                if request.get("kind") == "shutdown":
                    break
    except KeyboardInterrupt:
        pass
    except Exception:
        args.journal.with_suffix(".error.txt").write_text(traceback.format_exc())
        raise
    finally:
        server.close()
        args.socket.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
