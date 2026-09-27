#!/usr/bin/env python3
"""Independent stdlib-only auditor for the Issue #4745 raw result."""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

SRC = Path("/src")
INPUT = Path("/inputs")
MODEL = Path("/model")
OUT = Path("/out")
ERRORS: list[str] = []


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def quantile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * p
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (index - low)


def check(errors: list[str], condition: bool, name: str) -> None:
    if not condition:
        errors.append(name)


def validate(result: dict, freeze: dict, src: Path, inputs: Path, model: Path) -> dict:
    errors: list[str] = []
    expected_classes = [f"C{i}" for i in range(6)]
    expected_features = [f"f{i}" for i in range(8)]
    model_file = model / "model.safetensors"
    config_file = model / "config.json"
    model_card_file = model / "README.md"
    support_file = inputs / "support.csv"
    queries_file = inputs / "queries.csv"
    check(errors, result.get("schema") == "issue-4745-mitra-gpu-result-v1", "schema")
    check(errors, result.get("allocation") == freeze.get("allocation"), "allocation")
    check(errors, result.get("freeze_sha256") == digest(src / "FREEZE.json"), "freeze_hash")
    check(errors, result.get("protocol_sha256") == digest(src / "PROTOCOL.md"), "protocol_hash")
    check(errors, result.get("source_sha256") == freeze.get("source_sha256"), "source_map_binding")
    for relative, expected in freeze.get("source_sha256", {}).items():
        check(errors, digest(src / relative) == expected, f"source_hash:{relative}")
    wheel_manifest = freeze.get("wheelhouse_manifest_sha256")
    check(errors, bool(wheel_manifest) and digest(src / "wheelhouse-manifest.json") == wheel_manifest, "wheelhouse_manifest_hash")
    for key, path in (("model", model_file), ("config", config_file), ("model_card", model_card_file), ("support", support_file), ("queries", queries_file)):
        expected = freeze.get("inputs", {}).get(key, {}).get("sha256")
        check(errors, bool(expected) and digest(path) == expected, f"input_hash:{key}")

    model_desc = result.get("model", {})
    check(errors, model_desc.get("revision") == freeze.get("model", {}).get("revision"), "model_revision")
    check(errors, model_desc.get("sha256") == digest(model_file) == freeze.get("inputs", {}).get("model", {}).get("sha256"), "model_sha256")
    check(errors, model_desc.get("bytes") == model_file.stat().st_size == freeze.get("model", {}).get("bytes"), "model_bytes")
    try:
        config = json.loads(config_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        config = None
    check(errors, config == freeze.get("model", {}).get("config") == model_desc.get("config"), "model_config")

    inputs_desc = result.get("inputs", {})
    check(errors, inputs_desc.get("support_sha256") == digest(support_file), "support_hash_result")
    check(errors, inputs_desc.get("queries_sha256") == digest(queries_file), "queries_hash_result")
    check(errors, inputs_desc.get("support_rows") == 256 and inputs_desc.get("query_rows") == 1024, "fixture_row_counts")
    check(errors, inputs_desc.get("class_ids") == expected_classes, "class_ids")
    check(errors, inputs_desc.get("feature_ids") == expected_features, "feature_ids")

    api = result.get("api", {})
    check(errors, api.get("class") == "autogluon.tabular.models.mitra.sklearn_interface.MitraClassifier", "api_class")
    check(errors, api.get("device") == "cuda", "api_device")
    check(errors, api.get("fine_tune") is False and api.get("fine_tune_steps") == 0, "fine_tuning_disabled")
    check(errors, api.get("n_estimators") == 1 and api.get("resident_path") is True, "resident_single_estimator")
    check(errors, result.get("optimizer_step_calls") == 0, "optimizer_steps")
    check(errors, result.get("network_expected") == "none", "network_policy")

    runtime = result.get("runtime", {})
    check(errors, runtime.get("gpu_name", "").find("RTX 3080") >= 0, "gpu_identity")
    check(errors, runtime.get("torch_cuda") == freeze.get("runtime", {}).get("torch_cuda"), "cuda_runtime")
    check(errors, runtime.get("torch") == freeze.get("runtime", {}).get("torch"), "torch_version")
    check(errors, runtime.get("autogluon_tabular") == "1.6.3", "autogluon_version")
    check(errors, runtime.get("transformers") == "5.17.0", "transformers_version")
    check(errors, runtime.get("huggingface_hub") == "1.33.0", "huggingface_hub_version")
    check(errors, runtime.get("safetensors") == "0.8.0", "safetensors_version")
    check(errors, runtime.get("torch_threads") == 1, "torch_threads")
    check(errors, isinstance(runtime.get("gpu_total_memory_bytes"), int) and runtime["gpu_total_memory_bytes"] > 0, "gpu_memory_total")
    check(errors, isinstance(runtime.get("gpu_free_before_bytes"), int) and runtime["gpu_free_before_bytes"] > 0, "gpu_preflight_free_memory")

    resident = result.get("resident_after_fit", {})
    check(errors, resident.get("trainer_count") == 1, "trainer_count")
    check(errors, resident.get("parameter_devices") == ["cuda:0"], "resident_device")
    check(errors, isinstance(resident.get("parameter_bytes"), int) and resident["parameter_bytes"] > 0, "resident_parameter_bytes")
    check(errors, isinstance(resident.get("cuda_memory_allocated_bytes"), int) and resident["cuda_memory_allocated_bytes"] > 0, "resident_memory")
    check(errors, runtime.get("gpu_free_after_fit_bytes", 0) < runtime.get("gpu_free_before_bytes", 0), "gpu_placement_delta")
    check(errors, isinstance(result.get("cold_model_load_s"), (float, int)) and result["cold_model_load_s"] > 0, "cold_load_time")
    check(errors, isinstance(result.get("fit_wall_s"), (float, int)) and result["fit_wall_s"] > 0, "fit_time")
    check(errors, isinstance(result.get("context_setup_excluding_load_s"), (float, int)) and result["context_setup_excluding_load_s"] >= 0, "setup_time")
    check(errors, isinstance(result.get("peak_rss_bytes"), int) and result["peak_rss_bytes"] > 0, "peak_rss")

    warmup = result.get("warmup_probabilities", [])
    formal = result.get("formal_probabilities", [])
    repeats = result.get("repeat_probabilities", [])
    warm_records = result.get("warmup_records", [])
    formal_records = result.get("formal_query_records", [])
    repeat_records = result.get("repeat_records", [])
    check(errors, len(warmup) == len(warm_records) == 16, "warmup_count")
    check(errors, len(formal) == len(formal_records) == 1024, "formal_count")
    check(errors, len(repeats) == len(repeat_records) == 16, "repeat_count")

    def valid_probability(row: list) -> bool:
        return len(row) == 6 and all(isinstance(v, (int, float)) and math.isfinite(v) and v >= 0 for v in row) and abs(sum(row) - 1.0) <= 1e-4

    check(errors, all(valid_probability(row) for row in warmup + formal + repeats), "probability_abi")
    if len(formal) == 1024 and len(repeats) == 16 and all(valid_probability(r) for r in formal[:16] + repeats):
        check(errors, all(abs(a - b) <= 1e-6 for i in range(16) for a, b in zip(formal[i], repeats[i])), "repeat_determinism")

    for phase, records, expected_count in (("warmup", warm_records, 16), ("formal", formal_records, 1024), ("repeat", repeat_records, 16)):
        check(errors, [r.get("index") for r in records] == list(range(expected_count)), f"index_order:{phase}")
        check(errors, all(r.get("phase") == phase for r in records), f"phase_binding:{phase}")
        for i, record in enumerate(records):
            check(errors, record.get("parameter_devices") == ["cuda:0"], f"per_call_device:{phase}:{i}")
            check(errors, isinstance(record.get("parameter_bytes"), int) and record["parameter_bytes"] > 0, f"per_call_parameters:{phase}:{i}")
            check(errors, isinstance(record.get("cuda_memory_allocated_bytes"), int) and record["cuda_memory_allocated_bytes"] > 0, f"per_call_memory:{phase}:{i}")
            check(errors, isinstance(record.get("cuda_event_ms"), (float, int)) and record["cuda_event_ms"] > 0, f"per_call_cuda_event:{phase}:{i}")
            check(errors, isinstance(record.get("wall_start_unix_ns"), int) and record.get("wall_end_unix_ns", 0) > record.get("wall_start_unix_ns", 0), f"per_call_wall_interval:{phase}:{i}")
            check(errors, isinstance(record.get("wall_latency_ms"), (float, int)) and record["wall_latency_ms"] > 0, f"per_call_latency:{phase}:{i}")
            check(errors, isinstance(record.get("process_rchar_delta"), int) and record["process_rchar_delta"] >= 0, f"per_call_read_counter:{phase}:{i}")
            check(errors, valid_probability(record.get("probabilities", [])), f"per_call_probability:{phase}:{i}")

    latencies = [r.get("wall_latency_ms") for r in formal_records if isinstance(r.get("wall_latency_ms"), (float, int))]
    p50 = quantile(latencies, 0.50) if len(latencies) == 1024 else None
    p95 = quantile(latencies, 0.95) if len(latencies) == 1024 else None
    p99 = quantile(latencies, 0.99) if len(latencies) == 1024 else None
    threshold = result.get("checkpoint_reread_threshold_bytes")
    check(errors, isinstance(threshold, int) and threshold == int(model_file.stat().st_size * 0.8), "checkpoint_threshold")
    rereads = sum(1 for r in formal_records if isinstance(r.get("process_rchar_delta"), int) and r["process_rchar_delta"] >= (threshold or math.inf))
    check(errors, result.get("checkpoint_scale_reread_count") == rereads, "checkpoint_reread_count")
    check(errors, rereads == 0, "checkpoint_scale_reread_absent")
    summary = result.get("latency_summary_ms", {})
    if p95 is not None:
        check(errors, abs(summary.get("p50", math.inf) - p50) < 1e-9, "p50_summary")
        check(errors, abs(summary.get("p95", math.inf) - p95) < 1e-9, "p95_summary")
        check(errors, abs(summary.get("p99", math.inf) - p99) < 1e-9, "p99_summary")
        expected = (
            "REJECT_GPU_HIGH_CADENCE_SHAPE"
            if p95 >= 500.0 or rereads > 0
            else "PASS_GPU_RUNTIME_ABI_SCOPED+REALTIME_10HZ_CANDIDATE"
            if p95 < 100.0
            else "PASS_GPU_RUNTIME_ABI_SCOPED+INTERACTIVE_2HZ"
        )
        check(errors, result.get("decision") == expected, "decision_gate")
    return {"errors": errors, "pass": not errors, "formal_rows": len(formal), "p50_ms": p50, "p95_ms": p95, "p99_ms": p99, "decision": result.get("decision")}


def main() -> int:
    result_path = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT / "RESULT.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    freeze = json.loads((SRC / "FREEZE.json").read_text(encoding="utf-8"))
    audit = validate(result, freeze, SRC, INPUT, MODEL)
    (OUT / "AUDIT.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))
    return 0 if audit["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

