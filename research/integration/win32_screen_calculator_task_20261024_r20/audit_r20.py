from pathlib import Path
import hashlib, json, statistics
from PIL import Image

P = Path(__file__).resolve().parent
R = P / "run"

def read(name):
    return json.loads((R / name).read_text(encoding="utf-8"))

def report(value):
    if isinstance(value, dict):
        receipt = value.get("receipt")
        if isinstance(receipt, dict) and isinstance(receipt.get("report"), dict):
            return receipt["report"]
        if isinstance(value.get("report"), dict):
            return value["report"]
    return value

def values_for(value, key):
    if isinstance(value, dict):
        return ([value[key]] if key in value else []) + sum(
            (values_for(child, key) for child in value.values()), []
        )
    if isinstance(value, list):
        return sum((values_for(child, key) for child in value), [])
    return []

conditions = json.loads((P / "conditions.json").read_text(encoding="utf-8"))
frozen = {}
for line in (P / "FROZEN_SHA256SUMS").read_text(encoding="ascii").splitlines():
    digest, name = line.split("  ", 1)
    frozen[name] = hashlib.sha256((P / name).read_bytes()).hexdigest() == digest

observation = report(read("observation-parsed.json"))
dispatch = report(read("dispatch-parsed.json"))
action = dispatch["supervision"]["action"]
custody = action["completion_custody"]
verification = read("task-verification-parsed.json")
retained = read("final-results-parsed.json")
oracle = json.loads((R / "oracle-receipts.json").read_text(encoding="utf-8"))[0]
pre = read("uia-baseline.json")["parsed"]
post_observation = read("uia-after-observe.json")["parsed"]
post = read("uia-post.json")["parsed"]
close = read("close.json")
target = read("FROZEN_TARGET.json")
image = Image.open(R / "observation-image-00.png").convert("RGB")
samples = [json.loads(line) for line in (R / "uia-monitor.jsonl").read_text(encoding="utf-8-sig").splitlines() if line.strip()]
errors = [sample for sample in samples if sample["error"]]
digits = [sample["display_digits"] for sample in samples]
positive_index = next(i for i, sample in enumerate(samples) if sample["display_digits"] == "1046")
last_negative = max(i for i in range(positive_index) if samples[i]["display_digits"] == "1045")
negative, positive = samples[last_negative], samples[positive_index]
frequency = positive["qpc_frequency"]
cadence_ms = [(b["qpc_start"] - a["qpc_start"]) * 1000 / frequency for a, b in zip(samples, samples[1:])]
read_ms = [(s["qpc_end"] - s["qpc_start"]) * 1000 / frequency for s in samples]
dispatch_timing = read("dispatch-timing.json")
release = custody["completion_release_receipt"]
readback = custody["completion_readback"]
generation_values = sorted(set(v for v in values_for(read("observation-parsed.json"), "target_generation") if isinstance(v, str)))
required_receipt_keys = {"call_id", "operation_id", "target_generation", "oracle_id", "outcome", "observed_monotonic_ns", "evidence_ref"}
same_binding = (
    oracle["call_id"] == dispatch["call_id"] == verification["call_id"] == retained["call_id"]
    and oracle["operation_id"] == dispatch["operation_id"] == action["operation_id"]
    and oracle["target_generation"] == dispatch["target_generation"] == observation["target_generation"]
)
manifest_ok = all(frozen.values())
checks = {
    "frozen_manifest": manifest_ok,
    "current_main_source_identity": conditions["source_commit"] == "212c5f1494d0c84f48c6b6ebbe64fb4c77c2bed7" and conditions["source_tree"] == "f9b12ec434ce48c0d084b884bb3bfcc136d035b6",
    "runner_hash_bound": target["runner_sha256"] == hashlib.sha256((P / "run_r20.py").read_bytes()).hexdigest(),
    "attempt_identity_bound": target["attempt_id"] == conditions["attempt_id"],
    "screen_observation": observation["status"] == "returned" and observation["observation"]["frame"] == "screen_physical_px" and image.size == (320, 533) and image.getbbox() is not None,
    "one_target_generation": len(generation_values) == 1 and generation_values[0] == observation["target_generation"] == target["target_generation"],
    "ui_baseline_and_effect": pre["display_digits"] == post_observation["display_digits"] == "1045" and post["display_digits"] == "1046",
    "monitor_baseline_and_exit": read("uia-monitor-pre-dispatch.json")["sample_count"] >= 3 and read("uia-monitor-exit.json")["exit_code"] == 0,
    "monitor_clean_monotone_transition": not errors and set(digits) == {"1045", "1046"} and digits[:positive_index + 1] == ["1045"] * positive_index + ["1046"] and all(d == "1046" for d in digits[positive_index:]),
    "transition_bracket_under_200ms": 0 < (positive["qpc_end"] - negative["qpc_start"]) * 1000 / frequency < 200,
    "one_dispatch_no_replay": dispatch["status"] == "returned" and dispatch["input_dispatched"] is True and action["status"] == "completed" and dispatch["replay_allowed"] is False,
    "verified_release": release["verified"] is True and not any(release[k] for k in ("keys_down", "buttons_down", "keys_unknown", "buttons_unknown")),
    "neutral_same_operation_readback": readback["neutral"] is True and readback["operation_id"] == dispatch["operation_id"] and readback["target_generation"] == dispatch["target_generation"],
    "exact_bound_task_success": set(oracle) == required_receipt_keys and oracle["outcome"] == "success" and same_binding and verification["status"] == "verified" and verification["task_success"] is True and retained["task_success"] is True,
    "clean_close": close["status"] == "closed" and not close["session"]["unresolved_call_ids"],
}
qpc_dispatch_start = dispatch_timing["start_monotonic_ns"] * frequency / 1e9
qpc_dispatch_end = dispatch_timing["end_monotonic_ns"] * frequency / 1e9
timing = {
    "qpc_frequency": frequency,
    "sample_count": len(samples),
    "read_errors": len(errors),
    "requested_poll_ms": conditions["uia_monitor_poll_ms"],
    "observed_start_cadence_ms": {"min": min(cadence_ms), "median": statistics.median(cadence_ms), "max": max(cadence_ms)},
    "uia_read_duration_ms": {"min": min(read_ms), "median": statistics.median(read_ms), "max": max(read_ms)},
    "last_negative_sample": negative,
    "first_positive_sample": positive,
    "display_state_transition_bound_ms": (positive["qpc_end"] - negative["qpc_start"]) * 1000 / frequency,
    "dispatch_start_to_first_positive_read_end_ms": (positive["qpc_end"] - qpc_dispatch_start) * 1000 / frequency,
    "first_positive_before_dispatch_return_ms": (qpc_dispatch_end - positive["qpc_end"]) * 1000 / frequency,
    "interpretation": "UI Automation display-state timing only; not physical key-event-to-screen-pixel latency.",
}
result = {
    "schema": "win32-screen-calculator-r20-audit-v1",
    "attempt_id": conditions["attempt_id"],
    "call_id": dispatch["call_id"],
    "operation_id": dispatch["operation_id"],
    "target_generation": dispatch["target_generation"],
    "checks": checks,
    "all_checks_pass": all(checks.values()),
    "timing": timing,
    "close_release_confirmed": close["release_confirmed"],
    "metadata_correction": {
        "raw_target_schema": target["schema"],
        "expected_target_schema": "win32-screen-calculator-r20-target-v1",
        "raw_oracle_evidence_ref": oracle["evidence_ref"],
        "note": "Two inherited R19 labels remain in raw metadata. Raw is preserved; the R20 attempt ID, frozen conditions, runner hash and call/operation/generation bindings are exact."
    },
    "strict_disposition": "PASS_SCOPED" if all(checks.values()) else "HOLD_NOT_PASS",
    "limits": "One native Calculator sample; no MAP01, WSLc, blocked-I/O release, matched efficiency, or broad reliability conclusion."
}
(R / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"all_checks_pass": result["all_checks_pass"], "checks": checks, "timing_ms": timing}, ensure_ascii=True, indent=2))
assert all(checks.values()), [name for name, passed in checks.items() if not passed]

