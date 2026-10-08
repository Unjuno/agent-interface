#!/usr/bin/env python3
"""One-call, local-only Transformers RTX 3080 smoke test for Issue #5478."""
import hashlib, json, random, subprocess, time, sys
from pathlib import Path
from huggingface_hub import constants
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

SEED = 901733
REV = "7ae557604adf67be50417f59c2c2f167def9a775"
MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
CACHE = Path(constants.HF_HUB_CACHE) / "models--Qwen--Qwen2.5-0.5B-Instruct" / "snapshots" / REV
REQUIRED = {"prediction", "confidence", "unknown_probability", "evidence_source", "missing_evidence", "audit_recommendation"}

def smi():
    p = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10, check=True)
    return p.stdout.strip()

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def main():
    start = time.perf_counter()
    record = {"issue": 5478, "seed": SEED, "model": MODEL_ID, "revision": REV, "script_sha256": "verified against FREEZE.json before launch", "python": sys.version, "torch": torch.__version__, "transformers": __import__("transformers").__version__, "cuda_available": torch.cuda.is_available(), "gpu_before": smi()}
    if not torch.cuda.is_available():
        record["status"] = "STOP_NO_CUDA"
        print(json.dumps(record, sort_keys=True))
        return 2
    if not CACHE.is_dir():
        record["status"] = "STOP_MODEL_CACHE_MISSING"
        print(json.dumps(record, sort_keys=True))
        return 2
    weights = CACHE / "model.safetensors"
    record["model_file_bytes"] = weights.stat().st_size
    record["model_file_sha256"] = sha256_file(weights)
    tok = AutoTokenizer.from_pretrained(str(CACHE), local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(str(CACHE), local_files_only=True, torch_dtype=torch.float16).to("cuda:0").eval()
    record["model_device"] = str(next(model.parameters()).device)
    record["gpu_name"] = torch.cuda.get_device_name(0)
    rng = random.Random(SEED)
    counts = rng.sample(range(13, 89), 4)
    observations = [f"source-{chr(65+i)} reported {counts[i]} successes in 100 historical checks" for i in range(4)]
    rng.shuffle(observations)
    prompt = ("Return exactly one JSON object with keys prediction, confidence, unknown_probability, evidence_source, missing_evidence, audit_recommendation. Do not use markdown. Scenario: four synthetic local reports state: " + "; ".join(observations) + ". They share a renderer failure domain despite reporting separately. The next case has no verified outcome. Give a cautious advisory forecast, preserve uncertainty, state the shared-dependency limitation, and recommend one audit.")
    messages = [{"role":"system","content":"You produce cautious, machine-readable advisory reports. Never treat confidence as authority."},{"role":"user","content":prompt}]
    encoded = tok.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt", return_dict=True)
    tokens = encoded["input_ids"].to("cuda:0")
    record["input_tokens"] = int(tokens.shape[-1])
    record["gpu_before_call"] = smi()
    record["cuda_allocated_before_call_bytes"] = torch.cuda.memory_allocated(0)
    if record["model_device"] != "cuda:0" or tokens.device.type != "cuda":
        record["status"] = "STOP_CPU_PLACEMENT"
        print(json.dumps(record, sort_keys=True))
        return 2
    torch.cuda.reset_peak_memory_stats(0)
    torch.cuda.synchronize(0)
    call_start = time.perf_counter()
    with torch.inference_mode():
        generated = model.generate(input_ids=tokens, do_sample=False, max_new_tokens=160, pad_token_id=tok.eos_token_id, eos_token_id=tok.eos_token_id)
    torch.cuda.synchronize(0)
    record["generation_elapsed_ms"] = round((time.perf_counter()-call_start)*1000, 3)
    record["output_tokens"] = int(generated.shape[-1]-tokens.shape[-1])
    output = tok.decode(generated[0, tokens.shape[-1]:], skip_special_tokens=True).strip()
    record["generated_text"] = output
    record["cuda_allocated_after_call_bytes"] = torch.cuda.memory_allocated(0)
    record["cuda_peak_allocated_during_call_bytes"] = torch.cuda.max_memory_allocated(0)
    record["gpu_after_call"] = smi()
    record["elapsed_total_ms"] = round((time.perf_counter()-start)*1000, 3)
    try:
        obj = json.loads(output)
        record["json_keys"] = sorted(obj.keys())
        record["output_contract_pass"] = (REQUIRED.issubset(obj) and isinstance(obj["prediction"],str) and isinstance(obj["confidence"],(int,float)) and isinstance(obj["unknown_probability"],(int,float)) and isinstance(obj["evidence_source"],str) and isinstance(obj["missing_evidence"],(str,list)) and isinstance(obj["audit_recommendation"],str) and 0 <= float(obj["confidence"]) <= 1 and 0 <= float(obj["unknown_probability"]) <= 1)
    except Exception as e:
        record["json_parse_error"] = str(e)
        record["output_contract_pass"] = False
    same_gpu = all("NVIDIA GeForce RTX 3080 Laptop GPU" in record[k] for k in ["gpu_before","gpu_before_call","gpu_after_call"]) and "NVIDIA GeForce RTX 3080 Laptop GPU" in record["gpu_name"]
    record["gpu_placement_pass"] = record["cuda_allocated_after_call_bytes"] > 0 and record["cuda_peak_allocated_during_call_bytes"] > 0 and record["model_device"] == "cuda:0" and same_gpu
    record["status"] = "PASS_RUNTIME_SMOKE" if record["gpu_placement_pass"] and record["output_contract_pass"] and record["output_tokens"] > 0 else "STOP_GATE_FAILED"
    print(json.dumps(record, sort_keys=True))
    return 0 if record["status"] == "PASS_RUNTIME_SMOKE" else 1

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        import traceback
        print(json.dumps({"issue":5478,"seed":SEED,"status":"STOP_EXCEPTION","error_type":type(e).__name__,"error":str(e),"traceback":traceback.format_exc()},sort_keys=True))
        raise SystemExit(2)
