#!/usr/bin/env python3
"""One local GPU generation. Refuses to load unless preflight receipt passed."""
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
OUTDIR = HERE / "results" / "candidate-01"
PREFLIGHT = OUTDIR / "PREFLIGHT.json"


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def smi(args):
    return subprocess.run(["nvidia-smi", *args], capture_output=True, text=True,
                          timeout=10, check=True).stdout.strip()


def fail(message):
    payload = {"status": "STOP_BEFORE_OR_DURING_GENERATION", "reason": message,
               "allocation_id": FREEZE["allocation_id"],
               "timestamp_utc": datetime.now(timezone.utc).isoformat()}
    (OUTDIR / "CANDIDATE_STOP.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    raise SystemExit(1)


def main():
    if not PREFLIGHT.is_file():
        raise SystemExit("STOP: missing preflight receipt; no model load")
    preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    if not preflight.get("receipt_written") or not preflight.get("load_authorized") or preflight.get("errors"):
        raise SystemExit("STOP: preflight failed; no model load")
    start = datetime.fromisoformat(FREEZE["window_start_utc"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(FREEZE["window_end_utc"].replace("Z", "+00:00"))
    if not start <= datetime.now(timezone.utc) <= end:
        raise SystemExit("STOP: outside exclusive window; no model load")
    if (OUTDIR / "candidate.json").exists() or (OUTDIR / "CANDIDATE_STOP.json").exists():
        raise SystemExit("STOP: candidate output collision; no model load")

    # Import only the pure protocol before every source/current-main gate passes.
    from protocol import build_prompt, make_report, validate_raw

    expected_sources = json.loads((HERE / "SOURCE_HASHES.json").read_text(encoding="utf-8"))
    if file_sha256(HERE / "SOURCE_HASHES.json") != FREEZE["source_manifest_sha256"]:
        raise SystemExit("STOP: source manifest changed after preflight; no model load")
    if any(file_sha256(HERE / name) != expected
           for name, expected in expected_sources.items()):
        raise SystemExit("STOP: source changed after preflight; no model load")
    current_main = subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=HERE,
                                           text=True, timeout=5).strip()
    merge_base = subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"],
                                         cwd=HERE, text=True, timeout=5).strip()
    if current_main != FREEZE["main_sha_at_run"] or merge_base != FREEZE["main_sha_at_run"]:
        raise SystemExit("STOP: worktree is not based on frozen current main; no model load")
    frozen_files = [".gitattributes", "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/FREEZE.json",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/SOURCE_HASHES.json",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/INPUT.json",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/protocol.py",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/test_protocol.py",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/preflight.py",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/generate_one.py",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/audit.py",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/test_audit_contract.py",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/RUNBOOK.md"]
    subprocess.run(["git", "diff", "--quiet", "HEAD", "--", *frozen_files],
                   cwd=ROOT, check=True, timeout=5)
    subprocess.run(["git", "ls-files", "--error-unmatch", *frozen_files],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL, timeout=5)
    active_apps = smi(["--query-compute-apps=pid,process_name,used_memory",
                       "--format=csv,noheader"])
    if active_apps and "No running processes found" not in active_apps:
        raise SystemExit("STOP: GPU compute process appeared after preflight; no model load")

    input_bytes = (HERE / "INPUT.json").read_bytes()
    report = json.loads(input_bytes.decode("utf-8"))
    if report != make_report(FREEZE["data_seed"]):
        fail("frozen_input_does_not_match_seed_generator")
    prompt = build_prompt(report)
    prompt_hash = sha256_bytes(prompt.encode("utf-8"))
    input_hash = sha256_bytes(input_bytes)
    snapshot = Path(preflight["model_path"])
    local_weight = snapshot / FREEZE["model_file"]
    # Recheck the pinned weight identity before model load.
    model_digest = file_sha256(local_weight)
    if model_digest != FREEZE["model_sha256"]:
        fail("model_hash_changed_after_preflight")
    tokenizer_files = {}
    for path in sorted(p for p in snapshot.rglob("*")
                       if p.is_file() and p.name != FREEZE["model_file"]):
        tokenizer_files[path.relative_to(snapshot).as_posix()] = file_sha256(path)
    tokenizer_manifest = json.dumps(tokenizer_files, sort_keys=True,
                                    separators=(",", ":")).encode("utf-8")
    if sha256_bytes(tokenizer_manifest) != FREEZE["tokenizer_manifest_sha256"]:
        fail("tokenizer_manifest_changed_after_preflight")
    if tokenizer_files != FREEZE["tokenizer_file_hashes"]:
        fail("tokenizer_file_inventory_changed_after_preflight")

    # Import the GPU runtime only after all frozen CPU/source/model checks pass.
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.manual_seed(FREEZE["data_seed"])
    torch.cuda.manual_seed_all(FREEZE["data_seed"])
    run_started_utc = datetime.now(timezone.utc).isoformat()
    gpu_before_load = smi(["--query-gpu=index,name,uuid,memory.used,utilization.gpu",
                           "--format=csv,noheader"])
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            str(snapshot), local_files_only=True, trust_remote_code=False)
        model = AutoModelForCausalLM.from_pretrained(
            str(snapshot), local_files_only=True, trust_remote_code=False,
            torch_dtype=torch.float16, attn_implementation="eager")
        model.to("cuda:0")
        model.eval()
        messages = [{"role": "user", "content": prompt}]
        rendered = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True)
        batch = tokenizer(rendered, return_tensors="pt")
        batch = batch.to("cuda:0")
        model_device = str(next(model.parameters()).device)
        input_device = str(batch["input_ids"].device)
        gpu_before_generate = smi(["--query-gpu=index,name,uuid,memory.used,utilization.gpu",
                                   "--format=csv,noheader"])
        if model_device != "cuda:0" or input_device != "cuda:0":
            fail("model_or_input_not_on_cuda0")
        before_allocated = torch.cuda.memory_allocated(0)
        torch.cuda.reset_peak_memory_stats(0)
        began = time.perf_counter_ns()
        with torch.inference_mode():
            generated = model.generate(
                **batch, do_sample=False,
                max_new_tokens=FREEZE["generation"]["max_new_tokens"],
                pad_token_id=tokenizer.eos_token_id)
        elapsed_ns = time.perf_counter_ns() - began
        new_tokens = generated[0, batch["input_ids"].shape[1]:]
        raw_text = tokenizer.decode(new_tokens, skip_special_tokens=True)
        after_allocated = torch.cuda.memory_allocated(0)
        peak_allocated = torch.cuda.max_memory_allocated(0)
        gpu_after = smi(["--query-gpu=index,name,uuid,memory.used,utilization.gpu",
                         "--format=csv,noheader"])
        valid, reason = validate_raw(raw_text)
        result = {
            "status": "PASS_ONE_CALL_OUTPUT_CONTRACT" if valid else "FAIL_OUTPUT_CONTRACT",
            "allocation_id": FREEZE["allocation_id"],
            "main_sha": FREEZE["main_sha_at_run"],
            "started_utc": run_started_utc,
            "model": FREEZE["model"], "revision": FREEZE["model_revision"],
            "model_sha256": model_digest, "tokenizer_manifest_sha256": preflight["tokenizer_manifest_sha256"],
            "prompt_sha256": prompt_hash, "input_sha256": input_hash,
            "prompt": prompt, "input": report,
            "raw_text": raw_text, "raw_text_sha256": sha256_bytes(raw_text.encode("utf-8")),
            "schema_valid": valid, "schema_reason": reason,
            "model_device": model_device, "input_device": input_device,
            "torch_version": torch.__version__, "cuda_runtime": torch.version.cuda,
            "model_dtype": str(next(model.parameters()).dtype),
            "cuda_allocated_before_bytes": before_allocated,
            "cuda_allocated_after_bytes": after_allocated,
            "cuda_peak_allocated_bytes": peak_allocated,
            "generation_elapsed_ns": elapsed_ns,
            "generated_token_count": int(new_tokens.shape[0]),
            "generated_token_ids": [int(token) for token in new_tokens.detach().cpu().tolist()],
            "nvidia_smi_before_model_load": gpu_before_load,
            "nvidia_smi_before_generate": gpu_before_generate,
            "nvidia_smi_after_generate": gpu_after,
            "exit_code": 0,
            "model_call_count": 1,
            "retry_count": 0,
            "preflight_sha256": sha256_bytes(PREFLIGHT.read_bytes()),
        }
        (OUTDIR / "candidate.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": result["status"], "schema_reason": reason,
                          "device": model_device, "elapsed_ns": elapsed_ns,
                          "tokens": result["generated_token_count"]}, sort_keys=True))
        raise SystemExit(0)
    except SystemExit:
        raise
    except BaseException as exc:
        fail(type(exc).__name__ + ":" + str(exc))


if __name__ == "__main__":
    main()
