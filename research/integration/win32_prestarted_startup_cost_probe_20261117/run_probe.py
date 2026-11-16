from __future__ import annotations

import json
import platform
import statistics
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from runtime.cli_v1.win32_standard_producer import NativeWin32StandardProducerFactory


def action():
    return {
        "call_id": uuid.uuid4().hex,
        "operation_id": uuid.uuid4().hex,
        "target_generation": "a" * 64,
        "program": {
            "source": {"observation_seq": 1, "binding_revision": 1},
            "ops": [{"op": "verify"}],
        },
    }


def ordinary_trial(index):
    with tempfile.TemporaryDirectory(prefix="ai-ordinary-") as root:
        started = time.perf_counter_ns()
        factory = NativeWin32StandardProducerFactory(
            {"fixture": 1}, root, prestarted=False)
        constructed = time.perf_counter_ns()
        process, _identity, _authorize = factory(action())
        before_start = time.perf_counter_ns()
        process.start()
        after_start = time.perf_counter_ns()
        process.terminate()
        process.join(2.0)
        retired = not process.is_alive()
        factory.close()
        return {
            "route": "ordinary",
            "index": index,
            "factory_construction_ms": (constructed - started) / 1e6,
            "process_start_ms": (after_start - before_start) / 1e6,
            "startup_total_ms": (after_start - started) / 1e6,
            "cleanup_retired": retired,
            "gate_opened": False,
        }


def prestarted_trial(index):
    with tempfile.TemporaryDirectory(prefix="ai-prestarted-") as root:
        started = time.perf_counter_ns()
        factory = NativeWin32StandardProducerFactory(
            {"fixture": 1}, root, prestarted=True,
            worker_startup_timeout_s=30.0)
        ready = time.perf_counter_ns()
        result = {
            "route": "prestarted",
            "index": index,
            "factory_ready_ms": (ready - started) / 1e6,
            "startup_total_ms": (ready - started) / 1e6,
            "ready_receipt": factory.ensure_ready(),
            "gate_opened": False,
        }
        result["cleanup"] = factory.close()
        return result


def main():
    if sys.platform != "win32":
        raise SystemExit("This probe requires the native Windows host.")
    trials = []
    for index in range(1, 6):
        order = (ordinary_trial, prestarted_trial) if index % 2 else (
            prestarted_trial, ordinary_trial)
        for trial in order:
            try:
                trials.append(trial(index))
            except Exception as error:
                trials.append({
                    "route": trial.__name__.removesuffix("_trial"),
                    "index": index,
                    "error_type": type(error).__name__,
                    "error": str(error),
                })
    summary = {}
    for route in ("ordinary", "prestarted"):
        values = [row["startup_total_ms"] for row in trials
                  if row.get("route") == route and "startup_total_ms" in row]
        summary[route] = {
            "n": len(values),
            "median_startup_total_ms": statistics.median(values) if values else None,
            "values_ms": values,
        }
    raw = {
        "schema": "win32-producer-startup-cost-probe-v1",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "host_platform": platform.platform(),
        "python": sys.version,
        "executable": sys.executable,
        "source_commit": "8846fa3fd67c6b74a50cdcfa3589ca82071e0daa",
        "repetitions_per_route": 5,
        "trials": trials,
        "summary": summary,
    }
    out = Path(__file__).with_name("raw-results.json")
    out.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(out)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
