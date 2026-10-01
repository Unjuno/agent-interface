"""Single no-retry offline orchestration for the frozen #5139 allocation."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(document, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def claim_formal_attempt(out: Path, allocation: str, freeze_sha: str) -> None:
    """Permanently consume the one formal attempt before any model/CUDA work."""
    try:
        write_json(out / "FORMAL_ATTEMPT.json", {
            "schema": "qwen5139-formal-attempt-v1",
            "allocation": allocation,
            "freeze_sha256": freeze_sha,
            "claimed_utc": datetime.now(timezone.utc).isoformat(),
            "retry_policy": "none",
        })
    except FileExistsError as exc:
        raise SystemExit("STOP_FORMAL_ATTEMPT_ALREADY_CLAIMED") from exc


def verify_inputs(allocation_dir: Path, candidate_dir: Path, model_dir: Path,
                  data_path: Path, image_digest: str) -> tuple[dict, str, dict]:
    freeze_path = allocation_dir / "FREEZE.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if freeze.get("stage") != "LAUNCH_FROZEN":
        raise SystemExit("STOP_FREEZE_NOT_LAUNCH_FINAL")
    main_sha = freeze.get("current_main_sha", "")
    if len(main_sha) != 40 or any(ch not in "0123456789abcdef" for ch in main_sha):
        raise SystemExit("STOP_CURRENT_MAIN_SHA_FORMAT")
    start = datetime.fromisoformat(freeze["window"]["start_utc"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(freeze["window"]["end_utc"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    if not (start <= now < end):
        raise SystemExit("STOP_OUTSIDE_RESERVED_WINDOW")
    freeze_sha = (allocation_dir / "FREEZE.sha256").read_text(encoding="ascii").split()[0]
    if sha(freeze_path) != freeze_sha:
        raise SystemExit("STOP_FREEZE_HASH")
    for name, expected in freeze["source_sha256"].items():
        path = allocation_dir / name
        if not path.is_file() or sha(path) != expected:
            raise SystemExit("STOP_ALLOCATION_SOURCE_HASH:" + name)
    for entry in freeze["external_sources"]:
        path = candidate_dir / entry["container_path"]
        if not path.is_file() or sha(path) != entry["sha256"]:
            raise SystemExit("STOP_CURRENT_MAIN_SOURCE_HASH:" + entry["repo_path"])
    data_bytes = data_path.read_bytes()
    if hashlib.sha256(data_bytes).hexdigest() != freeze["data"]["formal_input_sha256"]:
        raise SystemExit("STOP_DATA_HASH")
    coverage_path = allocation_dir / "COVERAGE_SUMMARY.json"
    if not coverage_path.is_file() or sha(coverage_path) != freeze["data"]["coverage_summary_sha256"]:
        raise SystemExit("STOP_COVERAGE_SUMMARY_HASH")
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    if coverage.get("formal_input_sha256") != freeze["data"]["formal_input_sha256"]:
        raise SystemExit("STOP_COVERAGE_SUMMARY_BINDING")
    data = json.loads(data_bytes.decode("utf-8"))
    if data.get("allocation") != freeze["allocation"]:
        raise SystemExit("STOP_DATA_ALLOCATION")
    for key, value in freeze["seeds"].items():
        actual_key = {"heldout_seed": "heldout_seed"}.get(key, key)
        if data.get(actual_key) != value:
            raise SystemExit("STOP_DATA_SEED:" + key)
    if len(set(freeze["seeds"].values())) != 3:
        raise SystemExit("STOP_SEED_COLLISION")
    if (len(data.get("support_pool", [])) != 128 or
            len(data.get("heldout_pool", [])) != 256 or
            data.get("classes") != freeze["data"]["classes"]):
        raise SystemExit("STOP_POOL_OR_CLASS_SHAPE")
    all_pool_rows = data["support_pool"] + data["heldout_pool"]
    ids = [row["case_id"] for row in all_pool_rows]
    scopes = [row["state"]["scope_id"] for row in all_pool_rows]
    if len(ids) != len(set(ids)) or len(scopes) != len(set(scopes)):
        raise SystemExit("STOP_POOL_ID_OR_SCOPE_COLLISION")
    if ({row["task"] for row in data["support_pool"]} &
            {row["task"] for row in data["heldout_pool"]}):
        raise SystemExit("STOP_POOL_TASK_LEAKAGE")
    if os.environ.get("FROZEN_IMAGE_DIGEST") != image_digest:
        raise SystemExit("STOP_IMAGE_DIGEST")
    if image_digest != freeze["image"]["digest"]:
        raise SystemExit("STOP_FROZEN_IMAGE_DIGEST")
    for name, expected in freeze["model"]["files"].items():
        path = model_dir / name
        if not path.is_file() or sha(path) != expected:
            raise SystemExit("STOP_MODEL_FILE_HASH:" + name)
    counts = {
        arm: {cls: sum(row["class"] == cls for row in rows)
              for cls in freeze["data"]["classes"]}
        for arm, rows in data["supports"].items()
    }
    if counts != freeze["data"]["support_counts"]:
        raise SystemExit("STOP_SUPPORT_COUNTS")
    for arm, rows in data["supports"].items():
        if len(rows) != 32:
            raise SystemExit("STOP_SUPPORT_ROWS:" + arm)
        order_sha = hashlib.sha256("\n".join(row["case_id"] for row in rows).encode()).hexdigest()
        if order_sha != freeze["data"]["training_case_order_sha256"][arm]:
            raise SystemExit("STOP_SUPPORT_ORDER:" + arm)
    if len(data["heldout"]) != 64 or any(
        sum(row["class"] == cls for row in data["heldout"]) != 8
        for cls in freeze["data"]["classes"]):
        raise SystemExit("STOP_HELDOUT_COUNT")
    support_ids = {row["case_id"] for rows in data["supports"].values() for row in rows}
    heldout_ids = {row["case_id"] for row in data["heldout"]}
    if support_ids & heldout_ids:
        raise SystemExit("STOP_TRAIN_HELDOUT_OVERLAP")
    return freeze, freeze_sha, data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allocation-dir", required=True)
    parser.add_argument("--candidate-dir", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    allocation_dir, candidate_dir, model_dir, data_path, out = map(
        Path, (args.allocation_dir, args.candidate_dir, args.model, args.data, args.out))
    if out.exists() and any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    out.mkdir(parents=True, exist_ok=True)
    image_digest = os.environ.get("FROZEN_IMAGE_DIGEST", "")
    freeze, freeze_sha, data = verify_inputs(
        allocation_dir, candidate_dir, model_dir, data_path, image_digest)
    if args.preflight_only:
        write_json(out / "FIT_COUNTER.json", {
            "schema": "formal-fit-counter-v1", "allocation": freeze["allocation"],
            "formal_seed_fit_invocations": 0, "stages": ["cpu_preflight_passed"]})
        write_json(out / "PREFLIGHT.json", {
            "disposition": "PREFLIGHT_OK", "allocation": freeze["allocation"],
            "current_main_sha": freeze["current_main_sha"], "freeze_sha256": freeze_sha,
            "formal_input_sha256": freeze["data"]["formal_input_sha256"],
            "model_files": freeze["model"]["files"], "image_digest": image_digest,
            "model_loaded": False, "cuda_called": False, "fit_invocations": 0})
        print(json.dumps({"disposition": "PREFLIGHT_OK", "fit_invocations": 0,
                          "allocation": freeze["allocation"], "freeze_sha256": freeze_sha}))
        return

    # Persist an exclusive one-shot marker before importing torch or asking CUDA.
    # A failed availability/model/runtime gate therefore cannot be retried in-place.
    claim_formal_attempt(out, freeze["allocation"], freeze_sha)
    import torch
    if not torch.cuda.is_available():
        raise SystemExit("STOP_GPU_UNAVAILABLE")
    gpu_name = torch.cuda.get_device_name(0)
    if "RTX 3080" not in gpu_name:
        raise SystemExit("STOP_WRONG_GPU:" + gpu_name)
    orchestration = {
        "schema": "qwen05b-abstention-balance-execution-v1",
        "allocation": freeze["allocation"], "seed": freeze["seeds"]["formal_seed"],
        "data_sha256": freeze["data"]["formal_input_sha256"],
        "model_safetensors_sha256": freeze["model"]["model_safetensors_sha256"],
        "model_files": freeze["model"]["files"], "freeze_sha256": freeze_sha,
        "image_digest": image_digest, "gpu": gpu_name, "torch": torch.__version__,
        "commands": [], "formal_seed_fit_invocations": 0,
        "formal_base_evaluations": 0, "formal_adapter_evaluations": 0,
        "disposition": "RUNNING", "out_dir": str(out),
    }
    receipt = out / "ORCHESTRATION.json"
    counter = {"schema": "formal-fit-counter-v1", "allocation": freeze["allocation"],
               "formal_seed_fit_invocations": 0, "stages": ["formal_gate_passed"]}

    def persist():
        path = receipt.with_suffix(".tmp")
        path.write_text(json.dumps(orchestration, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        with path.open("rb") as stream:
            os.fsync(stream.fileno())
        path.replace(receipt)

    def invoke(label: str, argv: list[str], kind: str, timeout_s: int) -> None:
        if kind == "fit":
            counter["formal_seed_fit_invocations"] += 1
            counter["stages"].append("fit_invoked:" + label)
            counter_path = out / "FIT_COUNTER.json"
            tmp = counter_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(counter, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            with tmp.open("rb") as stream:
                os.fsync(stream.fileno())
            tmp.replace(counter_path)
            orchestration["formal_seed_fit_invocations"] = counter["formal_seed_fit_invocations"]
            persist()
        start = time.perf_counter()
        try:
            proc = subprocess.run(argv, text=True, capture_output=True, check=False, timeout=timeout_s,
                                  env={**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
                                       "TOKENIZERS_PARALLELISM": "false", "PYTHONDONTWRITEBYTECODE": "1"})
            code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as exc:
            def decode(value):
                return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else (value or "")
            code, stdout, stderr = 124, decode(exc.stdout), decode(exc.stderr)
            orchestration["disposition"] = "STOP_TIMEOUT_" + label
        (out / (label + ".stdout.txt")).write_text(stdout, encoding="utf-8")
        (out / (label + ".stderr.txt")).write_text(stderr, encoding="utf-8")
        orchestration["commands"].append({
            "label": label, "argv": argv, "exit_code": code,
            "wall_seconds": time.perf_counter() - start,
            "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest()})
        if kind == "base":
            orchestration["formal_base_evaluations"] += 1
        elif kind == "adapter":
            orchestration["formal_adapter_evaluations"] += 1
        persist()
        if code:
            if not orchestration["disposition"].startswith("STOP_TIMEOUT_"):
                orchestration["disposition"] = "STOP_SUBPROCESS_" + label
                persist()
            raise SystemExit(code)

    seed = str(freeze["seeds"]["formal_seed"])
    common = ["--model", str(model_dir), "--data", str(data_path), "--seed", seed]
    python = sys.executable
    fit_script = candidate_dir / "train_arm.py"
    eval_script = candidate_dir / "evaluate_arm.py"
    for arm in ("imbalanced", "balanced"):
        invoke("fit_" + arm, [python, str(fit_script), *common, "--arm", arm,
                              "--out", str(out / ("adapter-" + arm))], "fit", 300)
    fit_a = json.loads((out / "adapter-imbalanced" / "fit.json").read_text(encoding="utf-8"))
    fit_b = json.loads((out / "adapter-balanced" / "fit.json").read_text(encoding="utf-8"))
    order_ok = all(
        hashlib.sha256("\n".join(fit["case_ids_in_training_order"]).encode()).hexdigest() ==
        freeze["data"]["training_case_order_sha256"][arm]
        for arm, fit in (("imbalanced", fit_a), ("balanced", fit_b)))
    if fit_a["initial_lora_sha256"] != fit_b["initial_lora_sha256"] or not order_ok:
        orchestration["disposition"] = "STOP_INITIAL_ADAPTER_OR_ORDER_MISMATCH"
        persist()
        raise SystemExit(orchestration["disposition"])
    invoke("eval_base", [python, str(eval_script), *common, "--arm", "base",
                         "--out", str(out / "base-raw.json")], "base", 1800)
    for arm in ("imbalanced", "balanced"):
        invoke("eval_" + arm, [python, str(eval_script), *common,
                               "--adapter", str(out / ("adapter-" + arm)), "--arm", arm,
                               "--out", str(out / (arm + "-raw.json"))], "adapter", 1800)
    orchestration["disposition"] = "RAW_COMPLETE_PENDING_CPU_AUDIT"
    orchestration["formal_fit_seconds"] = {
        "imbalanced": fit_a["fit_seconds"], "balanced": fit_b["fit_seconds"]}
    orchestration["peak_cuda_bytes"] = max(fit_a["peak_cuda_bytes"], fit_b["peak_cuda_bytes"])
    persist()
    print(json.dumps(orchestration, sort_keys=True))


if __name__ == "__main__":
    main()
