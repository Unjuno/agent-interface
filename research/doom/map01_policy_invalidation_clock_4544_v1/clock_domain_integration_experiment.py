"""One host-monitor to Docker-runtime invalidation boundary experiment.

No model, game input, or formal MAP01 allocation is used. Run from repository
root with the pinned runtime image already present locally.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "research" / "live_control"))
sys.path.insert(0, str(HERE))

from observable_signal_guard_v2 import ObservableSignalGuard, ObservableSignalPolicyMonitor
from clock_translation_v2 import SCHEMA, translate_invalidation
from final_action_admission_v1 import decide_final_admission

IMAGE = "issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e"
EXPECTED_MONITOR_SHA256 = "c0955f976e3a0af6ce926f22cee4a5ddf70ef543"


class FixedHealthReader:
    def read(self, _observation):
        return {"status": "observed", "signal_id": "health", "value": 68,
                "sequence": 2, "capture_ns": self.capture_ns,
                "binding": {"session": "clock-boundary-experiment"}}


def runtime_clock_process():
    code = "import sys,time\nfor line in sys.stdin:\n print(time.perf_counter_ns(), flush=True)\n"
    return subprocess.Popen(
        ["docker", "run", "--rm", "-i", "--pull=never", "--platform", "linux/arm64",
         "--network", "none", "--read-only", "--entrypoint", "python3", IMAGE,
         "-u", "-c", code],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1)


def main():
    binding = {"session": "clock-boundary-experiment"}
    host_source_capture = time.perf_counter_ns() - 1_000_000_000
    source = {"status": "observed", "signal_id": "health", "value": 91,
              "sequence": 1, "capture_ns": host_source_capture, "binding": binding}
    spec = {"op": "observable_signal_guard", "guard_id": "cover-health",
            "source_sequence": 1, "signal_id": "health", "source_value": 91,
            "hard_minimum": 78, "max_source_age_ms": 30000,
            "on_soft_change": "preserve_existing_policy",
            "on_hard_change": "needs_decision", "on_unknown": "needs_decision"}
    guard = ObservableSignalGuard(spec, source, binding)
    reader = FixedHealthReader()
    reader.capture_ns = time.perf_counter_ns() - 100_000_000
    monitor = ObservableSignalPolicyMonitor(guard, reader)

    runtime = runtime_clock_process()
    try:
        observation = {"sequence": 2}
        raw_receipt = monitor.observe(observation)
        if raw_receipt is None:
            raise RuntimeError("expected one HARD_INVALIDATED monitor receipt")
        monitor_fields = sorted(raw_receipt)
        probes = []
        for _ in range(3):
            h_send = time.perf_counter_ns()
            runtime.stdin.write("sample\n")
            runtime.stdin.flush()
            r_ns = int(runtime.stdout.readline())
            h_receive = time.perf_counter_ns()
            probes.append({"host_send_ns": h_send, "runtime_ns": r_ns,
                           "host_receive_ns": h_receive})
        # This is the exact adapter contract in adapter_v2.py: the monitor
        # timestamps itself with the controller process monotonic clock, then
        # the adapter attaches that known source domain before translation.
        host_receipt = dict(raw_receipt)
        host_receipt["timestamp_domain"] = "host_monotonic_ns"
        calibration = {"schema": SCHEMA, "same_session": True,
                       "host_domain": "host_monotonic_ns",
                       "runtime_domain": "runtime_monotonic_ns", "samples": probes}
        translation, runtime_receipt = translate_invalidation(host_receipt, calibration)

        h_decided = time.perf_counter_ns()
        r_decided = h_decided + translation["offset_lower_ns"]
        translated_gate = decide_final_admission(
            {"turn_id": "interrupted-stale", "status": "interrupted",
             "answer_eligible": False,
             "terminal_observed_ns": r_decided - 1_000_000},
            runtime_receipt, r_decided)

        raw_domain_gate_error = None
        try:
            decide_final_admission(
                {"turn_id": "interrupted-stale", "status": "interrupted",
                 "answer_eligible": False,
                 "terminal_observed_ns": r_decided - 1_000_000},
                host_receipt, r_decided)
        except ValueError as exc:
            raw_domain_gate_error = str(exc)

        late_gate_rejected = False
        try:
            decide_final_admission(
                {"turn_id": "interrupted-stale", "status": "interrupted",
                 "answer_eligible": False,
                 "terminal_observed_ns": r_decided - 1_000_000},
                runtime_receipt, translation["runtime_timestamp_ns"] - 1)
        except ValueError as exc:
            late_gate_rejected = str(exc) == "controller decision precedes observed boundary"

        result = {
            "experiment": "observable-monitor-host-to-docker-runtime-clock-v1",
            "classification": "PASS_SCOPED" if (
                raw_receipt["outcome"]["status"] == "HARD_INVALIDATED" and
                "timestamp_domain" not in monitor_fields and
                runtime_receipt["timestamp_domain"] == "runtime_monotonic_ns" and
                translated_gate["status"] == "REJECTED_POLICY_INVALIDATED" and
                translated_gate["input_authority_admitted"] is False and
                translated_gate["executor_admission"] is None and late_gate_rejected
            ) else "FAIL_OR_HOLD",
            "scope": "one real host monitor receipt, three same-session Docker clock probes, pure final-admission gate; no game/model/input",
            "monitor_source_sha1": EXPECTED_MONITOR_SHA256,
            "pinned_image": IMAGE,
            "monitor_receipt_fields": monitor_fields,
            "monitor_receipt": raw_receipt,
            "adapter_host_receipt": host_receipt,
            "clock_probes": probes,
            "translation": translation,
            "runtime_gate": translated_gate,
            "untranslated_mixed_domain_error": raw_domain_gate_error,
            "late_controller_boundary_rejected": late_gate_rejected,
            "limitations": [
                "single local allocation; no statistical timing claim",
                "does not diagnose seed 990641 running-action freshness operands",
                "monitor source identity is bound by the current-main Git blob SHA1"
            ]
        }
        out = HERE / "results" / "clock-domain-integration-20260927-01"
        out.mkdir(parents=True, exist_ok=False)
        (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"classification": result["classification"],
                          "output": str(out / "result.json"),
                          "clock_offset_lower_ns": translation["offset_lower_ns"],
                          "clock_offset_upper_ns": translation["offset_upper_ns"],
                          "raw_domain_gate_error": raw_domain_gate_error,
                          "gate": translated_gate["status"]}, sort_keys=True))
    finally:
        if runtime.stdin:
            runtime.stdin.close()
        runtime.wait(timeout=10)
        stderr = runtime.stderr.read() if runtime.stderr else ""
        if runtime.returncode != 0:
            raise RuntimeError(f"runtime clock process exited {runtime.returncode}: {stderr}")


if __name__ == "__main__":
    main()
