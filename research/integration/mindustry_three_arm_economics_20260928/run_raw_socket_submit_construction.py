"""Retain a three-arm synthetic capture through the real socket submit adapter.

The bridge exchange is injected and synthetic. This command does not connect to
Mindustry, a Unix socket, or a model, and does not authorize physical input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from audit_target_dispatch_capture import audit as audit_dispatch  # noqa: E402
from raw_allocation_audit_v2 import audit as audit_raw  # noqa: E402
from target_socket_submit_v1 import JsonlTraceSink, TargetSocketSubmitter  # noqa: E402
from test_private_benchmark_channel import assemble_raw_from_private_channels  # noqa: E402


ARMS = ("plain", "ephemeral", "persistent")


def synthetic_bridge_exchange(request: dict) -> dict:
    """Return one complete synthetic v2 receipt for this action only."""
    action_id = request["action_id"]
    return {
        "status": "boundary",
        "records": [{"event": "terminal", "id": action_id,
                     "status": "completed", "release": {"verified": True,
                                             "keys_down": [], "buttons_down": []}}],
        "cursor": request["after"] + 1,
        "authority": "none",
        "acknowledgement": "not implied",
        "command_receipt": {"request_id": action_id, "replayed": False,
                            "state": "stdin_flushed"},
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_name",
        help="new immutable capture directory name under construction/")
    name = parser.parse_args(argv).capture_name
    if not name or Path(name).name != name:
        parser.error("capture_name must be a directory basename")

    output = HERE / "construction" / name
    output.mkdir(parents=True, exist_ok=False)
    trace_dir = output / "socket-traces"
    trace_dir.mkdir()
    dispatch_path = output / "target-dispatch-events.json"
    sinks: list[JsonlTraceSink] = []
    submitters: dict[str, TargetSocketSubmitter] = {}

    def make_submitter(arm: str) -> TargetSocketSubmitter:
        sink = JsonlTraceSink(trace_dir / f"{arm}.jsonl")
        sinks.append(sink)
        submitter = TargetSocketSubmitter(
            f"/synthetic/{arm}.sock", trace_sink=sink)
        submitter._exchange = synthetic_bridge_exchange
        submitters[arm] = submitter
        return submitter

    try:
        with tempfile.TemporaryDirectory() as temporary:
            raw = assemble_raw_from_private_channels(
                Path(temporary), dispatch_path,
                submitter_factory=make_submitter)
    finally:
        for sink in sinks:
            sink.close()

    dispatch_capture = json.loads(dispatch_path.read_bytes())
    dispatch_result = audit_dispatch(raw, dispatch_capture)
    raw_bytes = (json.dumps(raw, sort_keys=True, indent=2) + "\n").encode("utf-8")
    raw_result = audit_raw(raw_bytes)
    (output / "raw-events.json").write_bytes(raw_bytes)
    (output / "dispatch-audit.json").write_text(
        json.dumps(dispatch_result, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    (output / "audit.json").write_text(
        json.dumps(raw_result, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")

    for arm in ARMS:
        if submitters[arm].cursor != 12:
            raise AssertionError(f"{arm} cursor did not advance through 12 actions")
        trace_path = trace_dir / f"{arm}.jsonl"
        trace = [json.loads(line) for line in
                 trace_path.read_text(encoding="utf-8").splitlines()]
        if len(trace) != 24 or [row["event"] for row in trace] != [
                event for _ in range(12)
                for event in ("submit_prepared", "socket_response")]:
            raise AssertionError(f"{arm} durable trace is incomplete or unordered")

    files = sorted(path for path in output.rglob("*")
                   if path.is_file() and path.name != "SHA256SUMS")
    manifest = "".join(f"{sha256(path)}  {path.relative_to(output).as_posix()}\n"
                       for path in files)
    (output / "SHA256SUMS").write_text(manifest, encoding="utf-8")

    print(json.dumps({
        "output": str(output),
        "raw_sha256": raw_result["raw_sha256"],
        "raw_audit": raw_result["audit"],
        "source_identity_verified": raw_result["source_identity_verified"],
        "dispatch_audit": dispatch_result,
        "actions_per_arm": 12,
        "trace_records_per_arm": 24,
        "trace_mode": "synthetic v2 bridge exchange; no socket opened",
    }, sort_keys=True))
    return (0 if raw_result["audit"] == "PASS_CONSTRUCTION_ONLY"
            and dispatch_result["audit"] == "PASS_SYNTHETIC_DISPATCH_JOIN"
            else 1)


if __name__ == "__main__":
    raise SystemExit(main())
