"""Independent stdlib-only raw audit for the host/runtime boundary result."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULT = HERE / "results/clock-domain-integration-20260927-01/result.json"
EXPECTED_MONITOR_BLOB = "c0955f976e3a0af6ce926f22cee4a5ddf70ef543"
EXPECTED_GATE_BLOB = "2b3875c5c885fac0a78db2e70cbaba30ca834c67"
EXPECTED_TRANSLATOR_SHA256 = "99ca937e911b89c1613f5be504ea64b416d98fe685a27f796900e44df887dfb0"
EXPECTED_HARNESS_SHA256 = "5430ca99d15d3de63650ecf3c12bf447d58315a8d6146c93e6555550a325e37a"


def audit(row):
    assert row["classification"] == "PASS_SCOPED"
    assert row["monitor_source_sha1"] == EXPECTED_MONITOR_BLOB
    receipt = row["monitor_receipt"]
    assert receipt["outcome"]["status"] == "HARD_INVALIDATED"
    assert "timestamp_domain" not in receipt
    assert row["monitor_receipt_fields"] == sorted(receipt)
    assert receipt["outcome_evaluated_ns"] >= receipt["signal_extracted_ns"] >= receipt["monitor_received_ns"]
    host = row["adapter_host_receipt"]
    assert host["timestamp_domain"] == "host_monotonic_ns"
    assert {k: v for k, v in host.items() if k != "timestamp_domain"} == receipt

    probes = row["clock_probes"]
    assert len(probes) == 3
    lowers, uppers, receives = [], [], []
    for sample in probes:
        send, receive, runtime = (sample["host_send_ns"], sample["host_receive_ns"],
                                  sample["runtime_ns"])
        assert 0 <= send <= receive and runtime >= 0
        lowers.append(runtime - receive)
        uppers.append(runtime - send)
        receives.append(receive)
    lower, upper = min(lowers), max(uppers)
    translation = row["translation"]
    assert translation["offset_lower_ns"] == lower
    assert translation["offset_upper_ns"] == upper
    assert upper - lower <= 1_000_000_000
    assert translation["host_timestamp_ns"] == receipt["outcome_evaluated_ns"]
    assert translation["runtime_timestamp_ns"] == receipt["outcome_evaluated_ns"] + lower
    assert translation["calibrated_host_ns"] == max(receives)
    age = max(receives) - receipt["outcome_evaluated_ns"]
    assert translation["calibration_age_ns"] == age and 0 <= age <= 5_000_000_000
    assert translation["source_receipt"] == host
    runtime_receipt = translation["runtime_receipt"]
    assert runtime_receipt["timestamp_domain"] == "runtime_monotonic_ns"
    assert runtime_receipt["outcome_evaluated_ns"] == translation["runtime_timestamp_ns"]
    assert {k: v for k, v in runtime_receipt.items()
            if k not in ("timestamp_domain", "outcome_evaluated_ns")} == {
                k: v for k, v in host.items()
                if k not in ("timestamp_domain", "outcome_evaluated_ns")}

    gate = row["runtime_gate"]
    assert gate["status"] == "REJECTED_POLICY_INVALIDATED"
    assert gate["policy_invalidation"] == runtime_receipt
    assert gate["input_authority_admitted"] is False
    assert gate["executor_admission"] is None
    assert row["untranslated_mixed_domain_error"] == "controller decision precedes observed boundary"
    assert row["late_controller_boundary_rejected"] is True
    return True


def main():
    row = json.loads(RESULT.read_text())
    audit(row)
    raw = RESULT.read_bytes()
    monitor_bytes = (HERE.parents[2] / "research/live_control/observable_signal_guard_v2.py").read_bytes()
    gate_bytes = (HERE.parents[2] / "research/live_control/final_action_admission_v1.py").read_bytes()
    monitor_blob = hashlib.sha1(f"blob {len(monitor_bytes)}\0".encode() + monitor_bytes).hexdigest()
    gate_blob = hashlib.sha1(f"blob {len(gate_bytes)}\0".encode() + gate_bytes).hexdigest()
    translator_sha = hashlib.sha256((HERE / "clock_translation_v2.py").read_bytes()).hexdigest()
    harness_sha = hashlib.sha256((HERE / "clock_domain_integration_experiment.py").read_bytes()).hexdigest()
    assert monitor_blob == EXPECTED_MONITOR_BLOB
    assert gate_blob == EXPECTED_GATE_BLOB
    assert translator_sha == EXPECTED_TRANSLATOR_SHA256
    assert harness_sha == EXPECTED_HARNESS_SHA256
    mutations = []

    def rejected(name, mutate):
        changed = copy.deepcopy(row)
        mutate(changed)
        try:
            audit(changed)
        except (AssertionError, KeyError, TypeError):
            mutations.append(name)
        else:
            raise AssertionError(f"mutation was not rejected: {name}")

    rejected("receipt-domain-injected", lambda r: r["monitor_receipt"].update(timestamp_domain="runtime_monotonic_ns"))
    rejected("host-adapter-domain", lambda r: r["adapter_host_receipt"].update(timestamp_domain="runtime_monotonic_ns"))
    rejected("missing-probe", lambda r: r["clock_probes"].pop())
    rejected("reversed-probe-bracket", lambda r: r["clock_probes"][0].update(host_receive_ns=0))
    rejected("forged-lower-offset", lambda r: r["translation"].update(offset_lower_ns=0))
    rejected("forged-translated-time", lambda r: r["translation"].update(runtime_timestamp_ns=0))
    rejected("wrong-gate-disposition", lambda r: r["runtime_gate"].update(status="READY_FOR_FRESH_EXECUTOR_ADMISSION"))
    rejected("authority-escalation", lambda r: r["runtime_gate"].update(input_authority_admitted=True))
    rejected("fabricated-executor-admission", lambda r: r["runtime_gate"].update(executor_admission={"event": "accepted"}))
    rejected("mixed-domain-control-erased", lambda r: r.update(untranslated_mixed_domain_error=None))
    print(json.dumps({"result": "PASS_RAW_AUDIT", "corruption_controls": len(mutations),
                      "rejected_mutations": mutations,
                      "result_sha256": hashlib.sha256(raw).hexdigest(),
                      "audit_inputs": {
                          "monitor_blob": EXPECTED_MONITOR_BLOB,
                          "final_admission_blob": EXPECTED_GATE_BLOB,
                          "translator_sha256": EXPECTED_TRANSLATOR_SHA256,
                          "harness_sha256": EXPECTED_HARNESS_SHA256}}, sort_keys=True))


if __name__ == "__main__":
    main()
