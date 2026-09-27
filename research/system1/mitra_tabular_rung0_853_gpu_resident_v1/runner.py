#!/usr/bin/env python3
"""Single-invocation resident Mitra-v2 CUDA inference runner for Issue #4745."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
import platform
import resource
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import autogluon.tabular.models.mitra.sklearn_interface as mitra_interface
from autogluon.tabular.models.mitra.sklearn_interface import MitraClassifier

SRC = Path("/src")
INPUT = Path("/inputs")
MODEL = Path("/model")
OUT = Path("/out")
FREEZE = SRC / "FREEZE.json"
CLASSES = [f"C{i}" for i in range(6)]
FEATURES = [f"f{i}" for i in range(8)]
optimizer_step_calls = 0
model_load_seconds: list[float] = []
stage = "preflight"
started_wall_ns = time.time_ns()
query_records: list[dict] = []


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_rchar() -> int:
    try:
        for line in Path("/proc/self/io").read_text(encoding="ascii").splitlines():
            if line.startswith("rchar:"):
                return int(line.split()[1])
    except (OSError, ValueError):
        pass
    return -1


def instrument_optimizer_steps() -> None:
    """Count calls to every currently loaded concrete torch optimizer step."""
    seen: set[type] = set()

    def visit(parent: type) -> None:
        for cls in parent.__subclasses__():
            if cls in seen:
                continue
            seen.add(cls)
            if "step" in cls.__dict__:
                original = cls.__dict__["step"]

                def counted(self, *args, __original=original, **kwargs):
                    global optimizer_step_calls
                    optimizer_step_calls += 1
                    return __original(self, *args, **kwargs)

                setattr(cls, "step", counted)
            visit(cls)

    visit(torch.optim.Optimizer)


def instrument_model_load() -> None:
    original = mitra_interface.Tab2D.from_pretrained

    def timed_load(*args, **kwargs):
        before = time.perf_counter()
        model = original(*args, **kwargs)
        model_load_seconds.append(time.perf_counter() - before)
        return model

    mitra_interface.Tab2D.from_pretrained = staticmethod(timed_load)


def load_contract() -> tuple[dict, Path, Path, np.ndarray, np.ndarray, np.ndarray]:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    model_path = MODEL / "model.safetensors"
    config_path = MODEL / "config.json"
    model_card_path = MODEL / "README.md"
    support_path = INPUT / "support.csv"
    query_path = INPUT / "queries.csv"
    for path_key, path in (
        ("model", model_path),
        ("config", config_path),
        ("model_card", model_card_path),
        ("support", support_path),
        ("queries", query_path),
    ):
        expected = freeze["inputs"][path_key]["sha256"]
        if sha256(path) != expected:
            raise RuntimeError(f"INPUT_SHA256_MISMATCH:{path_key}")
    if json.loads(config_path.read_text(encoding="utf-8")) != freeze["model"]["config"]:
        raise RuntimeError("MODEL_CONFIG_MISMATCH")
    for relative, expected in freeze["source_sha256"].items():
        if sha256(SRC / relative) != expected:
            raise RuntimeError(f"FROZEN_SOURCE_HASH_MISMATCH:{relative}")
    if sha256(SRC / "wheelhouse-manifest.json") != freeze["wheelhouse_manifest_sha256"]:
        raise RuntimeError("WHEELHOUSE_MANIFEST_HASH_MISMATCH")
    support = pd.read_csv(support_path)
    queries = pd.read_csv(query_path)
    if list(support.columns) != FEATURES + ["label"] or list(queries.columns) != FEATURES:
        raise RuntimeError("FIXTURE_SCHEMA_MISMATCH")
    if len(support) != 256 or len(queries) != 1024:
        raise RuntimeError("FIXTURE_ROW_COUNT_MISMATCH")
    labels = support["label"].astype(str).to_numpy()
    if sorted(np.unique(labels).tolist()) != CLASSES:
        raise RuntimeError("CLASS_VOCABULARY_MISMATCH")
    x_support = support.loc[:, FEATURES].to_numpy(dtype=np.float32)
    x_queries = queries.loc[:, FEATURES].to_numpy(dtype=np.float32)
    if not np.isfinite(x_support).all() or not np.isfinite(x_queries).all():
        raise RuntimeError("NONFINITE_FIXTURE")
    return freeze, model_path, support_path, x_support, labels, x_queries


def cuda_identity(classifier: MitraClassifier) -> dict:
    trainers = getattr(classifier, "trainers", None)
    if not isinstance(trainers, list) or len(trainers) != 1:
        raise RuntimeError("EXPECTED_ONE_RESIDENT_TRAINER")
    model = getattr(trainers[0], "model", None)
    if model is None:
        raise RuntimeError("TRAINER_MODEL_MISSING")
    parameters = list(model.parameters())
    if not parameters:
        raise RuntimeError("MODEL_HAS_NO_PARAMETERS")
    devices = sorted({str(parameter.device) for parameter in parameters})
    if devices != ["cuda:0"]:
        raise RuntimeError(f"MODEL_NOT_RESIDENT_ON_CUDA0:{devices}")
    parameter_bytes = sum(parameter.numel() * parameter.element_size() for parameter in parameters)
    allocated = torch.cuda.memory_allocated(0)
    if parameter_bytes <= 0 or allocated <= 0:
        raise RuntimeError("CUDA_RESIDENCY_NOT_OBSERVED")
    return {
        "trainer_count": len(trainers),
        "parameter_devices": devices,
        "parameter_count": sum(parameter.numel() for parameter in parameters),
        "parameter_bytes": parameter_bytes,
        "cuda_memory_allocated_bytes": allocated,
    }


def record_prediction(classifier: MitraClassifier, row: np.ndarray, index: int, phase: str) -> list[float]:
    global query_records
    start_event = torch.cuda.Event(enable_timing=True)
    end_event = torch.cuda.Event(enable_timing=True)
    torch.cuda.synchronize(0)
    read_before = read_rchar()
    wall_start = time.time_ns()
    mono_start = time.perf_counter_ns()
    start_event.record(torch.cuda.current_stream(0))
    probabilities = classifier.predict_proba(row.reshape(1, -1))
    wall_end = time.time_ns()
    elapsed_ns = time.perf_counter_ns() - mono_start
    end_event.record(torch.cuda.current_stream(0))
    end_event.synchronize()
    gpu_ms = float(start_event.elapsed_time(end_event))
    read_after = read_rchar()
    values = np.asarray(probabilities, dtype=np.float64)
    if values.shape != (1, 6) or not np.isfinite(values).all():
        raise RuntimeError(f"PROBABILITY_ABI_FAILURE:{phase}:{index}:{values.shape}")
    vector = values[0].tolist()
    if abs(sum(vector) - 1.0) > 1e-4 or min(vector) < 0:
        raise RuntimeError(f"PROBABILITY_VALUES_INVALID:{phase}:{index}")
    resident = cuda_identity(classifier)
    if not math.isfinite(gpu_ms) or gpu_ms <= 0:
        raise RuntimeError(f"NO_CUDA_KERNEL_INTERVAL:{phase}:{index}:{gpu_ms}")
    record = {
        "phase": phase,
        "index": index,
        "wall_start_unix_ns": wall_start,
        "wall_end_unix_ns": wall_end,
        "wall_latency_ms": elapsed_ns / 1_000_000,
        "cuda_event_ms": gpu_ms,
        "process_rchar_delta": (read_after - read_before) if read_before >= 0 and read_after >= 0 else None,
        "probabilities": vector,
        **resident,
    }
    query_records.append(record)
    return vector


def main() -> int:
    global stage
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        torch.set_num_threads(1)
        torch.manual_seed(853)
        if torch.cuda.is_available() is not True or torch.cuda.device_count() < 1:
            raise RuntimeError("CUDA_DEVICE_UNAVAILABLE")
        if not torch.version.cuda:
            raise RuntimeError("TORCH_BUILD_HAS_NO_CUDA")
        device_name = torch.cuda.get_device_name(0)
        if "RTX 3080" not in device_name:
            raise RuntimeError(f"UNEXPECTED_GPU:{device_name}")
        freeze, model_path, support_path, x_support, labels, x_queries = load_contract()
        model_info = {
            "revision": freeze["model"]["revision"],
            "sha256": sha256(model_path),
            "bytes": model_path.stat().st_size,
            "config": json.loads((MODEL / "config.json").read_text(encoding="utf-8")),
        }
        empty_cuda_bytes = torch.cuda.memory_allocated(0)
        prefit_free, prefit_total = torch.cuda.mem_get_info(0)
        instrument_optimizer_steps()
        instrument_model_load()
        classifier = MitraClassifier(
            model_type="Tab2D",
            n_estimators=1,
            device="cuda",
            fine_tune=False,
            fine_tune_steps=0,
            hf_model=str(MODEL),
            seed=853,
            verbose=False,
        )
        stage = "support_context_setup"
        fit_started = time.perf_counter()
        classifier.fit(x_support, labels)
        fit_seconds = time.perf_counter() - fit_started
        torch.cuda.synchronize(0)
        if len(model_load_seconds) != 1:
            raise RuntimeError(f"EXPECTED_ONE_MODEL_LOAD_GOT_{len(model_load_seconds)}")
        if optimizer_step_calls != 0:
            raise RuntimeError(f"OPTIMIZER_STEP_GATE:{optimizer_step_calls}")
        resident_after_fit = cuda_identity(classifier)
        postfit_free, postfit_total = torch.cuda.mem_get_info(0)
        if postfit_total != prefit_total or postfit_free >= prefit_free:
            raise RuntimeError("CUDA_MEMORY_DELTA_NOT_OBSERVED")

        stage = "warmup"
        warmup_outputs = [record_prediction(classifier, x_queries[i], i, "warmup") for i in range(16)]
        torch.cuda.synchronize(0)
        stage = "formal_queries"
        formal_outputs = [record_prediction(classifier, row, i, "formal") for i, row in enumerate(x_queries)]
        stage = "repeat_queries"
        repeat_outputs = [record_prediction(classifier, x_queries[i], i, "repeat") for i in range(16)]
        if optimizer_step_calls != 0:
            raise RuntimeError(f"OPTIMIZER_STEP_GATE_AFTER_INFERENCE:{optimizer_step_calls}")
        if any(abs(a - b) > 1e-6 for i in range(16) for a, b in zip(formal_outputs[i], repeat_outputs[i])):
            raise RuntimeError("REPEATED_QUERY_NONDETERMINISM")

        latencies = [row["wall_latency_ms"] for row in query_records if row["phase"] == "formal"]
        if len(formal_outputs) != 1024 or len(latencies) != 1024:
            raise RuntimeError("FORMAL_ROW_COUNT_MISMATCH")
        p50, p95, p99 = [float(v) for v in np.quantile(latencies, [0.5, 0.95, 0.99], method="linear")]
        query_read_deltas = [row["process_rchar_delta"] for row in query_records if row["phase"] == "formal"]
        reload_limit = int(model_info["bytes"] * 0.8)
        checkpoint_rereads = sum(1 for value in query_read_deltas if value is not None and value >= reload_limit)
        decision = (
            "REJECT_GPU_HIGH_CADENCE_SHAPE"
            if p95 >= 500.0 or checkpoint_rereads > 0
            else "PASS_GPU_RUNTIME_ABI_SCOPED+REALTIME_10HZ_CANDIDATE"
            if p95 < 100.0
            else "PASS_GPU_RUNTIME_ABI_SCOPED+INTERACTIVE_2HZ"
        )
        result = {
            "schema": "issue-4745-mitra-gpu-result-v1",
            "allocation": freeze["allocation"],
            "protocol_sha256": sha256(SRC / "PROTOCOL.md"),
            "freeze_sha256": sha256(FREEZE),
            "source_sha256": freeze["source_sha256"],
            "model": model_info,
            "inputs": {
                "support_sha256": sha256(support_path),
                "queries_sha256": sha256(INPUT / "queries.csv"),
                "support_rows": len(x_support),
                "query_rows": len(x_queries),
                "class_ids": CLASSES,
                "feature_ids": FEATURES,
            },
            "runtime": {
                "python": platform.python_version(),
                "torch": torch.__version__,
                "torch_cuda": torch.version.cuda,
                "autogluon_tabular": importlib.metadata.version("autogluon.tabular"),
                "transformers": importlib.metadata.version("transformers"),
                "huggingface_hub": importlib.metadata.version("huggingface_hub"),
                "safetensors": importlib.metadata.version("safetensors"),
                "gpu_name": device_name,
                "gpu_total_memory_bytes": prefit_total,
                "gpu_free_before_bytes": prefit_free,
                "gpu_free_after_fit_bytes": postfit_free,
                "torch_threads": torch.get_num_threads(),
                "cuda_visible_devices": os.getenv("CUDA_VISIBLE_DEVICES"),
            },
            "api": {
                "class": "autogluon.tabular.models.mitra.sklearn_interface.MitraClassifier",
                "device": "cuda",
                "fine_tune": False,
                "fine_tune_steps": 0,
                "n_estimators": 1,
                "resident_path": True,
            },
            "fit_wall_s": fit_seconds,
            "cold_model_load_s": model_load_seconds[0],
            "context_setup_excluding_load_s": max(0.0, fit_seconds - model_load_seconds[0]),
            "optimizer_step_calls": optimizer_step_calls,
            "empty_cuda_allocator_bytes": empty_cuda_bytes,
            "resident_after_fit": resident_after_fit,
            "warmup_probabilities": warmup_outputs,
            "formal_probabilities": formal_outputs,
            "repeat_probabilities": repeat_outputs,
            "formal_query_records": [r for r in query_records if r["phase"] == "formal"],
            "warmup_records": [r for r in query_records if r["phase"] == "warmup"],
            "repeat_records": [r for r in query_records if r["phase"] == "repeat"],
            "latency_summary_ms": {"p50": p50, "p95": p95, "p99": p99, "max": max(latencies)},
            "checkpoint_reread_threshold_bytes": reload_limit,
            "checkpoint_scale_reread_count": checkpoint_rereads,
            "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "network_expected": "none",
            "decision": decision,
            "accuracy_claimed": False,
            "formal_started_unix_ns": started_wall_ns,
            "formal_completed_unix_ns": time.time_ns(),
        }
        (OUT / "RESULT.json").write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        (OUT / "QUERY_RECORDS.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in query_records), encoding="utf-8")
        print(json.dumps({k: v for k, v in result.items() if not k.endswith("probabilities") and not k.endswith("records")}, sort_keys=True))
        stage = "complete"
        return 0
    except Exception as exc:  # Preserve a typed STOP instead of losing a consumed run.
        stop = {
            "schema": "issue-4745-mitra-gpu-stop-v1",
            "allocation": "mitra-gpu-rung0-853-successor-local-20260927-01",
            "stage": stage,
            "exception_type": type(exc).__name__,
            "exception": str(exc),
            "optimizer_step_calls": optimizer_step_calls,
            "model_load_count": len(model_load_seconds),
            "partial_query_count": len(query_records),
            "partial_query_records": query_records,
            "start_unix_ns": started_wall_ns,
            "stop_unix_ns": time.time_ns(),
        }
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "STOP.json").write_text(json.dumps(stop, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        print(json.dumps(stop, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

