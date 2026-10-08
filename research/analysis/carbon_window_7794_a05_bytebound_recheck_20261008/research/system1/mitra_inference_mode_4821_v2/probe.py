#!/usr/bin/env python3
"""Bounded one-shot train/eval-mode diagnostic for Issue #4947."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import platform
import random
import time
from pathlib import Path

import numpy as np
import torch
import runner as base

OUT = Path("/out")


def module_state(model):
    return [{"name": name, "type": type(module).__name__, "training": bool(module.training)}
            for name, module in model.named_modules()]


def restore_module_state(model, frozen):
    modules = dict(model.named_modules())
    if set(modules) != {row["name"] for row in frozen}:
        raise RuntimeError("MODULE_TREE_CHANGED")
    for row in frozen:
        modules[row["name"]].training = bool(row["training"])


def rng_state():
    return {"python": random.getstate(), "numpy": copy.deepcopy(np.random.get_state()),
            "torch_cpu": torch.get_rng_state().clone(), "torch_cuda": [x.clone() for x in torch.cuda.get_rng_state_all()]}


def set_rng_state(state):
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch_cpu"])
    torch.cuda.set_rng_state_all(state["torch_cuda"])


def four_distinct_rng_states(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    states = []
    for _ in range(4):
        states.append(rng_state())
        random.random()
        np.random.random()
        torch.rand(16)
        torch.rand(16, device="cuda")
    return states


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    stage = "preflight"
    started = time.time_ns()
    try:
        torch.set_num_threads(1)
        if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
            raise RuntimeError("CUDA_DEVICE_UNAVAILABLE_OR_UNEXPECTED_COUNT")
        if "RTX 3080" not in torch.cuda.get_device_name(0):
            raise RuntimeError("UNEXPECTED_GPU:" + torch.cuda.get_device_name(0))
        freeze, model_path, support_path, x_support, labels, x_queries = base.load_contract()
        base.instrument_optimizer_steps()
        base.instrument_model_load()
        classifier = base.MitraClassifier(model_type="Tab2D", n_estimators=1, device="cuda",
            fine_tune=False, fine_tune_steps=0, hf_model=str(base.MODEL), seed=853, verbose=False)
        stage = "context_setup"
        fit_start = time.perf_counter_ns()
        classifier.fit(x_support, labels)
        fit_ns = time.perf_counter_ns() - fit_start
        torch.cuda.synchronize(0)
        if len(base.model_load_seconds) != 1:
            raise RuntimeError(f"EXPECTED_ONE_MODEL_LOAD_GOT_{len(base.model_load_seconds)}")
        if base.optimizer_step_calls != 0:
            raise RuntimeError("OPTIMIZER_STEP_DURING_CONTEXT_SETUP")
        model = classifier.trainers[0].model
        natural = module_state(model)
        if not natural:
            raise RuntimeError("EMPTY_MODULE_TREE")
        natural_stochastic = [x["name"] for x in natural if x["training"] and "dropout" in x["type"].lower()]
        mode_rows = []
        column_ids = tuple(range(6))
        stage = "paired_mode_probe"
        for row_index in range(16):
            states = four_distinct_rng_states(493500 + row_index)
            order = ["A", "B"] if row_index % 2 == 0 else ["B", "A"]
            for repeat_index, state in enumerate(states):
                for arm in order:
                    restore_module_state(model, natural)
                    if arm == "B":
                        model.eval()
                    before = module_state(model)
                    set_rng_state(state)
                    probs = base.record_prediction(classifier, x_queries[row_index], row_index,
                        f"{arm}_{repeat_index}", column_ids)
                    after = module_state(model)
                    mode_rows.append({"row_index": row_index, "repeat_index": repeat_index, "arm": arm,
                        "order": order, "probabilities": probs, "modules_before": before, "modules_after": after})
                    if base.optimizer_step_calls != 0:
                        raise RuntimeError("OPTIMIZER_STEP_OBSERVED")
        stage = "finalize"
        if base.optimizer_step_calls != 0:
            raise RuntimeError("OPTIMIZER_STEP_TOTAL_NONZERO")
        raw = {"schema": "mitra-inference-mode-diagnostic-4947-v2", "allocation": freeze["allocation"],
            "issue": 4947, "parent": 4935, "started_unix_ns": started, "finished_unix_ns": time.time_ns(),
            "main_intake_sha": freeze["main_intake_sha"], "image_id": freeze["execution"]["image_id"],
            "freeze_sha256": sha256(FREEZE), "expected_input_sha256": {k: freeze["inputs"][k]["sha256"] for k in ("support", "queries")},
            "source_sha256": freeze["source_sha256"],
            "runtime": {"python": platform.python_version(), "torch": torch.__version__,
                "torch_cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(0),
                "model_sha256": sha256(model_path), "support_sha256": sha256(support_path),
                "queries_sha256": sha256(Path("/inputs/queries.csv")),
                "fit_context_setup_ns": fit_ns, "optimizer_step_calls": base.optimizer_step_calls,
                "model_load_seconds": base.model_load_seconds},
            "natural_module_state": natural, "natural_active_dropout_modules": natural_stochastic,
            "predictions": mode_rows}
        (OUT / "RAW.json").write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        return 0
    except Exception as exc:
        receipt = {"schema": "mitra-inference-mode-stop-4947-v2", "allocation": "mitra-inference-mode-diagnostic-4821-v2-20260928-01",
            "issue": 4947, "stage": stage, "exception_type": type(exc).__name__, "message": str(exc),
            "optimizer_step_calls": getattr(base, "optimizer_step_calls", None), "started_unix_ns": started,
            "finished_unix_ns": time.time_ns()}
        (OUT / "STOP.json").write_text(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        raise


if __name__ == "__main__":
    raise SystemExit(main())

