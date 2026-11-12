"""Qualify the actual spawn bootstrap; no backend or native input is opened."""
from __future__ import annotations
import json
import multiprocessing
import os
from pathlib import Path
from .recovery_stage_trace import install
from runtime.cli_v1 import win32_supervisor_helpers as helpers

OUTPUT = Path(os.environ["AI_RECOVERY_TRACE_OUTPUT"]).resolve()
TRACE = install(OUTPUT)

def main():
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe(duplex=True)
    process = context.Process(target=helpers._helper_main,
        args=("observer", {"inert-fixture": 1}, child))
    process.start()
    child.close()
    if not parent.poll(10) or parent.recv() != {"status": "ready", "helper": "observer"}:
        raise RuntimeError("inert helper startup failed")
    parent.send(None)
    process.join(5)
    if process.is_alive() or process.exitcode != 0:
        raise RuntimeError("inert helper did not stop normally")
    child_pid = process.pid
    parent.close()
    process.close()
    TRACE.flush()
    files = list(OUTPUT.glob("stage-trace-*.json"))
    rows = [json.loads(p.read_text()) for p in files]
    child_rows = [r for r in rows if r["pid"] == child_pid]
    child_span = (len(child_rows) == 1 and any(s["stage"] == "helper.lifecycle"
                  for s in child_rows[0]["spans"]))
    if len(rows) != 2 or not child_span:
        raise RuntimeError("spawned helper trace missing")
    print(json.dumps({"child_exit_code": 0, "trace_files": len(files),
        "child_lifecycle_span_retained": child_span, "backend_opened": False}))

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
