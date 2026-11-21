"""One synthetic late-usage path through the current caller and comparator."""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
INTEGRATION_ROOT = REPO_ROOT / "research" / "integration" / "standard_mcp_task_ledger_57_v1"
if str(INTEGRATION_ROOT) not in sys.path:
    sys.path.insert(0, str(INTEGRATION_ROOT))

from comparison_measurement_v1 import validate_measured_run
from provider_attempt_recorder import ProviderAttemptRecorder
from recorded_comparison_adapter_v1 import build_measured_run
from recorded_public_mcp_caller_v1 import RecordedPublicMcpCaller


SOURCE_REVISION = "d08596ee0590ba6a9531075a5769c0ac4abc1ec1"
UNAVAILABLE = {"status": "unavailable", "input_tokens": None,
               "output_tokens": None}
LATE_USAGE = {"status": "reported", "input_tokens": 18,
              "output_tokens": 3}


class SyntheticLateUsageSource:
    def __init__(self, available: bool):
        self.available = available
        self.captured = False
        self.read_count = 0
        self.usage_bytes = json.dumps(
            LATE_USAGE, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.source_bytes = (json.dumps({
            "direction": "received",
            "message": {
                "method": "thread/tokenUsage/updated",
                "params": {
                    "threadId": "synthetic-thread-57",
                    "turnId": "synthetic-turn-57",
                    "tokenUsage": {"last": {
                        "inputTokens": 18, "outputTokens": 3,
                    }},
                },
            },
        }, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n")

    def capture_terminal(self):
        self.captured = True

    def read(self, _timeout):
        self.read_count += 1
        if not self.available or self.read_count > 1:
            return None
        return {
            "usage": dict(LATE_USAGE),
            "usage_bytes": self.usage_bytes,
            "source_bytes": self.source_bytes,
            "observed_ns": time.monotonic_ns(),
        }


class ForbiddenRelay:
    next_id = 1

    def __init__(self):
        self.calls = 0

    async def request(self, _request_bytes):
        self.calls += 1
        raise RuntimeError("timeout arm must not issue a public Relay request")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def run_case(output_root: Path, *, late_usage_available: bool) -> dict:
    output_root = Path(output_root)
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"refusing to overwrite case evidence: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    recorder_root = output_root / "recorder"
    recorder = ProviderAttemptRecorder(recorder_root)
    relay = ForbiddenRelay()
    caller = RecordedPublicMcpCaller(
        relay, recorder, allowed_methods={"interface_guarded_compiled"})
    source = SyntheticLateUsageSource(late_usage_available)
    attempt_id = "attempt-late-usage" if late_usage_available else "attempt-no-usage"

    async def provider_call():
        return {"status": "timeout", "usage": dict(UNAVAILABLE),
                "late_usage_source": source}

    outcome = asyncio.run(caller.invoke_generation_to_tool(
        attempt_id, b'{"prompt":"synthetic-only"}\n', provider_call,
        "late-answer-must-not-dispatch", "interface_guarded_compiled",
        json.loads))
    generation = outcome["generation"]
    if generation.get("status") != "timeout" or outcome["tool_call_submitted"]:
        raise RuntimeError("timeout must remain terminal and non-dispatching")
    if not source.captured:
        raise RuntimeError("timeout boundary did not capture the source cursor")

    recorder.record_task_score(
        "synthetic-no-effect-oracle-v1", None,
        b'{"task_effect":"unknown; no target was used"}\n')
    observed = asyncio.run(caller.observe_late_usage(
        attempt_id, generation, timeout=0))
    receipt = recorder.reconcile()
    if not receipt["complete"] or receipt["unresolved_attempt_ids"]:
        raise RuntimeError("caller receipt is incomplete")

    events = receipt["events"]
    if len(events) != 2 or events[-1]["kind"] != "task_score":
        raise RuntimeError("one timeout and one terminal UNKNOWN score are required")
    attempt = events[0]
    if (attempt["kind"] != "model_attempt" or
            attempt["status"] != "timeout" or
            attempt["attempt_id"] != attempt_id):
        raise RuntimeError("the first event is not the frozen timeout attempt")

    start_ns = min(event["started_ns"] for event in events)
    end_ns = max(event["ended_ns"] for event in events) + 1
    if end_ns <= start_ns:
        raise RuntimeError("monotonic lifecycle interval is not positive")
    tag = "with-late-usage" if late_usage_available else "without-late-usage"
    metadata = {
        "schema": "agent-interface/standard-mcp-task-ledger-v1",
        "run_id": f"run-{tag}",
        "comparison": {"arm": "A", "block": 1, "order": 1,
                       "task_seed": "synthetic-late-usage-57"},
        "task": {"task_id": f"accounting-{tag}",
                 "fixture_sha256": hashlib.sha256(b"synthetic-state").hexdigest(),
                 "scorer_sha256": hashlib.sha256(b"synthetic-scorer").hexdigest()},
        "source": {"commit": SOURCE_REVISION,
                   "route_sha256": hashlib.sha256(tag.encode()).hexdigest()},
        "environment_sha256": hashlib.sha256(b"offline-python-only").hexdigest(),
        "model": {"id": "synthetic-provider-boundary", "effort": "low",
                  "request_config_sha256": hashlib.sha256(
                      b"synthetic-request-config").hexdigest()},
    }
    measurement = {
        "started_ns": start_ns,
        "ended_ns": end_ns,
        "elapsed_ns": end_ns - start_ns,
        "phases": [{"name": "other", "started_ns": start_ns,
                    "ended_ns": end_ns,
                    "reason": "synthetic accounting composition; no target action"}],
        "model_delivered_images": [],
        "local_observations": [],
    }
    measured = build_measured_run(
        receipt, recorder_root=recorder_root,
        ledger_metadata=metadata, measurement=measurement)
    summary = validate_measured_run(measured)
    result = {
        "condition": tag,
        "late_usage_observed": observed["observed"],
        "late_usage_observation_count": observed.get("observations", 0),
        "relay_calls": relay.calls,
        "usage_status": summary["usage_status"],
        "input_tokens": summary["input_tokens"],
        "output_tokens": summary["output_tokens"],
        "model_attempt_count": summary["model_attempt_count"],
        "task_success": summary["task_success"],
        "independent_score_status": summary["independent_score_status"],
        "raw_ref_count": summary["raw_ref_count"],
    }
    _write_json(output_root / "receipt.json", receipt)
    _write_json(output_root / "measured_run.json", measured)
    _write_json(output_root / "summary.json", result)
    return result
