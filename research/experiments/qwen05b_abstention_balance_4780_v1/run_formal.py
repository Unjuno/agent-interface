"""Single no-retry Docker orchestration for the two frozen CUDA fits and evaluations."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def id_list_sha256(values):
    return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    source, model, data, out = map(Path, (args.source, args.model, args.data, args.out))
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    freeze = json.loads((source / "FREEZE.json").read_text(encoding="utf-8"))
    freeze_sha = (source / "FREEZE.sha256").read_text(encoding="ascii").strip().split()[0]
    if sha256(source / "FREEZE.json") != freeze_sha:
        raise SystemExit("STOP_FREEZE_HASH")
    manifest = (source / "SHA256SUMS.txt").read_text(encoding="ascii")
    expected = {}
    for line in manifest.splitlines():
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        expected[name] = digest
    source_names = freeze["source_files"]
    for name in source_names:
        if sha256(source / name) != expected.get(name):
            raise SystemExit("STOP_SOURCE_HASH:" + name)
    if sha256(data) != freeze["formal_input_sha256"]:
        raise SystemExit("STOP_INPUT_HASH")
    model_file = model / "model.safetensors"
    if sha256(model_file) != freeze["model_safetensors_sha256"]:
        raise SystemExit("STOP_MODEL_HASH")
    if args.seed != freeze["formal_seed"]:
        raise SystemExit("STOP_FORMAL_SEED")
    if not __import__("torch").cuda.is_available():
        raise SystemExit("STOP_GPU_UNAVAILABLE")
    if "RTX 3080" not in __import__("torch").cuda.get_device_name(0):
        raise SystemExit("STOP_WRONG_GPU")

    orchestration = {
        "schema": "qwen05b-abstention-balance-execution-v1",
        "allocation": freeze["allocation"],
        "seed": args.seed,
        "data_sha256": sha256(data),
        "model_safetensors_sha256": sha256(model_file),
        "freeze_sha256": freeze_sha,
        "gpu": __import__("torch").cuda.get_device_name(0),
        "torch": __import__("torch").__version__,
        "commands": [],
        "formal_seed_fit_invocations": 0,
        "formal_base_evaluations": 0,
        "formal_adapter_evaluations": 0,
        "disposition": "RUNNING",
    }
    receipt = out / "ORCHESTRATION.json"

    def persist():
        receipt.write_text(json.dumps(orchestration, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    def invoke(label, argv, kind):
        start = time.perf_counter()
        proc = subprocess.run(argv, text=True, capture_output=True, check=False,
                              env={**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
                                   "TOKENIZERS_PARALLELISM": "false"})
        elapsed = time.perf_counter() - start
        (out / (label + ".stdout.txt")).write_text(proc.stdout, encoding="utf-8")
        (out / (label + ".stderr.txt")).write_text(proc.stderr, encoding="utf-8")
        orchestration["commands"].append({
            "label": label, "argv": argv, "exit_code": proc.returncode,
            "wall_seconds": elapsed, "stdout_sha256": hashlib.sha256(proc.stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(proc.stderr.encode()).hexdigest(),
        })
        if kind == "fit":
            orchestration["formal_seed_fit_invocations"] += 1
        elif kind == "base":
            orchestration["formal_base_evaluations"] += 1
        else:
            orchestration["formal_adapter_evaluations"] += 1
        persist()
        if proc.returncode:
            orchestration["disposition"] = "STOP_SUBPROCESS_" + label
            persist()
            raise SystemExit(proc.returncode)

    py = sys.executable
    common = ["--model", str(model), "--data", str(data), "--seed", str(args.seed)]
    invoke("fit_imbalanced", [py, str(source / "train_arm.py"), *common,
                             "--arm", "imbalanced", "--out", str(out / "adapter-imbalanced")], "fit")
    invoke("fit_balanced", [py, str(source / "train_arm.py"), *common,
                            "--arm", "balanced", "--out", str(out / "adapter-balanced")], "fit")
    fit_a = json.loads((out / "adapter-imbalanced" / "fit.json").read_text(encoding="utf-8"))
    fit_b = json.loads((out / "adapter-balanced" / "fit.json").read_text(encoding="utf-8"))
    orchestration["initial_lora_match"] = (
        fit_a["initial_lora_sha256"] == fit_b["initial_lora_sha256"])
    orchestration["fit_arm_order_matches_freeze"] = (
        id_list_sha256(fit_a["case_ids_in_training_order"]) == freeze["training_case_order_sha256"]["imbalanced"] and
        id_list_sha256(fit_b["case_ids_in_training_order"]) == freeze["training_case_order_sha256"]["balanced"])
    if not orchestration["initial_lora_match"] or not orchestration["fit_arm_order_matches_freeze"]:
        orchestration["disposition"] = "STOP_INITIAL_STATE_OR_ORDER_MISMATCH"
        persist()
        raise SystemExit(orchestration["disposition"])

    invoke("eval_base", [py, str(source / "evaluate_arm.py"), *common,
                         "--arm", "base", "--out", str(out / "base-raw.json")], "base")
    invoke("eval_imbalanced", [py, str(source / "evaluate_arm.py"), *common,
                              "--adapter", str(out / "adapter-imbalanced"),
                              "--arm", "imbalanced", "--out", str(out / "imbalanced-raw.json")], "adapter")
    invoke("eval_balanced", [py, str(source / "evaluate_arm.py"), *common,
                             "--adapter", str(out / "adapter-balanced"),
                             "--arm", "balanced", "--out", str(out / "balanced-raw.json")], "adapter")
    orchestration["disposition"] = "RAW_COMPLETE_PENDING_CPU_AUDIT"
    orchestration["formal_fit_seconds"] = {
        "imbalanced": fit_a["fit_seconds"], "balanced": fit_b["fit_seconds"]}
    orchestration["peak_cuda_bytes"] = max(fit_a["peak_cuda_bytes"], fit_b["peak_cuda_bytes"])
    persist()
    print(json.dumps(orchestration, sort_keys=True))


if __name__ == "__main__":
    main()
