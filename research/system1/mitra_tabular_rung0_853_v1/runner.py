#!/usr/bin/env python3
"""Frozen, no-gradient, CPU-only Rung-0 runner for Issue #853."""
from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import resource
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from autogluon.tabular import TabularPredictor
import autogluon.tabular.models.mitra.sklearn_interface as mitra_interface

ROOT = Path(__file__).resolve().parent
MODEL = Path("/model")
OUTPUT = Path("/out")
CLASSES = [f"C{i}" for i in range(6)]
FEATURES = [f"f{i}" for i in range(8)]
EXPECTED_MODEL_SHA256 = "5ffab0e2cf52f61c5b7c7eb1e8542996736d1023a0212190cc09abc2119a1e09"
MODEL_REVISION = "edada0d20759c58ada8c8605c25f22f6e98ea5f0"
EXPECTED_SUPPORT_SHA256 = "bf4d64cf826ea2d727990bd799d7e6d0f813a97a64119751e05d22a819fdf785"
EXPECTED_QUERY_SHA256 = "dc68fe551034d6f961900e0300af8c41fea641e058380d21c904bc4146df7fd1"
optimizer_steps = 0
model_load_samples: list[float] = []


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def instrument_optimizer_steps() -> None:
    """Count any concrete torch optimizer step, without changing its result."""
    seen: set[type] = set()

    def visit(parent: type) -> None:
        global optimizer_steps
        for cls in parent.__subclasses__():
            if cls in seen:
                continue
            seen.add(cls)
            if "step" in cls.__dict__:
                original = cls.__dict__["step"]

                def counted(self, *args, __original=original, **kwargs):
                    global optimizer_steps
                    optimizer_steps += 1
                    return __original(self, *args, **kwargs)

                setattr(cls, "step", counted)
            visit(cls)

    visit(torch.optim.Optimizer)


def instrument_model_load() -> None:
    original = mitra_interface.Tab2D.from_pretrained

    def timed_load(*args, **kwargs):
        start = time.perf_counter()
        model = original(*args, **kwargs)
        model_load_samples.append(time.perf_counter() - start)
        return model

    mitra_interface.Tab2D.from_pretrained = staticmethod(timed_load)


def cpu_identity() -> str:
    try:
        text = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace")
        match = re.search(r"^model name\s*:\s*(.+)$", text, re.MULTILINE)
        return match.group(1).strip() if match else platform.processor()
    except OSError:
        return platform.processor()


def read_cgroup(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="ascii").strip()
    except OSError:
        return None


def main() -> None:
    process_start_unix = time.time()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    np.random.seed(853)
    if torch.cuda.is_available():
        raise RuntimeError("CPU_ONLY_GATE_FAILED: torch reports CUDA available")

    model_path = MODEL / "model.safetensors"
    config_path = MODEL / "config.json"
    freeze_path = ROOT / "FREEZE.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if sha256(model_path) != EXPECTED_MODEL_SHA256:
        raise RuntimeError("MODEL_SHA256_MISMATCH")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config != {"dim": 512, "dim_output": 10, "n_layers": 12, "n_heads": 4, "task": "CLASSIFICATION"}:
        raise RuntimeError("MODEL_CONFIG_MISMATCH")
    for relative, expected in freeze["source_sha256"].items():
        if sha256(ROOT / relative) != expected:
            raise RuntimeError(f"FROZEN_SOURCE_HASH_MISMATCH:{relative}")

    with (ROOT / "support.csv").open(newline="", encoding="utf-8") as stream:
        support = pd.read_csv(stream)
    with (ROOT / "queries.csv").open(newline="", encoding="utf-8") as stream:
        queries = pd.read_csv(stream)
    if list(support.columns) != FEATURES + ["label"] or list(queries.columns) != FEATURES:
        raise RuntimeError("FIXTURE_SCHEMA_MISMATCH")
    if sha256(ROOT / "support.csv") != EXPECTED_SUPPORT_SHA256 or sha256(ROOT / "queries.csv") != EXPECTED_QUERY_SHA256:
        raise RuntimeError("FIXTURE_SHA256_MISMATCH")
    if len(support) != 256 or len(queries) != 1024:
        raise RuntimeError("FIXTURE_ROW_COUNT_MISMATCH")
    if set(support["label"].astype(str)) != set(CLASSES):
        raise RuntimeError("FIXTURE_CLASS_COVERAGE_MISMATCH")

    instrument_optimizer_steps()
    instrument_model_load()
    predictor_path = "/tmp/mitra-predictor"
    start_fit = time.perf_counter()
    predictor = TabularPredictor(
        label="label",
        problem_type="multiclass",
        path=predictor_path,
        verbosity=0,
    ).fit(
        train_data=support,
        hyperparameters={
            "MITRA": {
                "hf_model": str(MODEL),
                "fine_tune": False,
                "fine_tune_steps": 0,
                "device": "cpu",
                "n_estimators": 1,
                "seed": 853,
                "verbose": False,
            }
        },
        num_cpus=1,
        num_gpus=0,
        num_bag_folds=0,
        num_stack_levels=0,
        fit_weighted_ensemble=False,
        fit_full_last_level_weighted_ensemble=False,
        full_weighted_ensemble_additionally=False,
        dynamic_stacking=False,
        calibrate_decision_threshold=False,
        verbosity=0,
    )
    fit_elapsed = time.perf_counter() - start_fit
    load_elapsed = sum(model_load_samples)
    if len(model_load_samples) != 1:
        raise RuntimeError(f"EXPECTED_ONE_MODEL_LOAD_GOT_{len(model_load_samples)}")

    warm_rows: list[list[float]] = []
    latencies_ms: list[float] = []
    for i in range(len(queries)):
        row = queries.iloc[[i]]
        started = time.perf_counter()
        probabilities = predictor.predict_proba(row)
        latencies_ms.append((time.perf_counter() - started) * 1000.0)
        if list(map(str, probabilities.columns)) != CLASSES:
            raise RuntimeError(f"CLASS_MAPPING_MISMATCH:{list(map(str, probabilities.columns))}")
        values = probabilities.loc[:, CLASSES].iloc[0].to_numpy(dtype=np.float64)
        if values.shape != (6,) or not np.isfinite(values).all():
            raise RuntimeError("INVALID_PROBABILITY_VECTOR")
        if abs(float(values.sum()) - 1.0) > 1e-4:
            raise RuntimeError("PROBABILITIES_DO_NOT_SUM_TO_ONE")
        warm_rows.append(values.tolist())

    repeat_rows: list[list[float]] = []
    repeat_latencies_ms: list[float] = []
    for i in range(16):
        started = time.perf_counter()
        probabilities = predictor.predict_proba(queries.iloc[[i]])
        repeat_latencies_ms.append((time.perf_counter() - started) * 1000.0)
        repeat_rows.append(probabilities.loc[:, CLASSES].iloc[0].to_numpy(dtype=np.float64).tolist())

    p50_ms, p95_ms, p99_ms = map(float, np.quantile(latencies_ms, [0.50, 0.95, 0.99], method="linear"))
    if p95_ms >= 500.0:
        decision = "REJECT_CPU_HIGH_CADENCE_SHAPE"
    elif p95_ms < 100.0:
        decision = "PASS_GENERAL_LOCAL_SYSTEM1_RUNTIME_SCOPED+REALTIME_10HZ_CANDIDATE"
    else:
        decision = "PASS_GENERAL_LOCAL_SYSTEM1_RUNTIME_SCOPED+INTERACTIVE_2HZ"

    result = {
        "schema": "issue-853-mitra-rung0-result-v1",
        "allocation": "mitra-cpu-rung0-853-local-20260927-01",
        "model_revision": MODEL_REVISION,
        "model_sha256": sha256(model_path),
        "model_bytes": model_path.stat().st_size,
        "model_config": config,
        "freeze_file_sha256": sha256(freeze_path),
        "source_sha256": freeze["source_sha256"],
        "support_csv_sha256": sha256(ROOT / "support.csv"),
        "query_csv_sha256": sha256(ROOT / "queries.csv"),
        "class_ids": CLASSES,
        "feature_ids": FEATURES,
        "support_rows": len(support),
        "query_rows": len(queries),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "autogluon_tabular": importlib.metadata.version("autogluon.tabular"),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "device": "cpu",
        "cuda_available": torch.cuda.is_available(),
        "torch_threads": torch.get_num_threads(),
        "cpu_identity": cpu_identity(),
        "cgroup_cpu_max": read_cgroup("/sys/fs/cgroup/cpu.max"),
        "cgroup_memory_max": read_cgroup("/sys/fs/cgroup/memory.max"),
        "fit_wall_s": fit_elapsed,
        "cold_model_load_s": load_elapsed,
        "context_setup_excluding_load_s": max(0.0, fit_elapsed - load_elapsed),
        "optimizer_step_calls": optimizer_steps,
        "warm_single_query_latency_ms": latencies_ms,
        "warm_probabilities": warm_rows,
        "repeat_query_indices": list(range(16)),
        "repeat_query_latency_ms": repeat_latencies_ms,
        "repeat_probabilities": repeat_rows,
        "latency_summary_ms": {"p50": p50_ms, "p95": p95_ms, "p99": p99_ms, "max": max(latencies_ms)},
        "decision": decision,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        "process_start_unix_s": process_start_unix,
        "network_expected": "none",
        "fine_tune": False,
        "accuracy_claimed": False,
    }
    (OUTPUT / "RESULT.json").write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in result.items() if k not in {"warm_single_query_latency_ms", "warm_probabilities", "repeat_probabilities"}}, sort_keys=True))


if __name__ == "__main__":
    main()
