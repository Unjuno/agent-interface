"""Greedy held-out evaluation of the frozen base or one sampled-support adapter."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from protocol import bind_intent, simulate_bound

SYSTEM = "Return only a compact intent JSON object; do not emit scope_id or generation."


def parse_json(text):
    try:
        value = json.loads(text.strip())
        return value, None
    except Exception:
        return None, "invalid_json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--adapter")
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--arm", choices=("base", "imbalanced", "balanced"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise SystemExit("STOP_GPU_UNAVAILABLE")
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, local_files_only=True, trust_remote_code=False,
        torch_dtype=torch.float16, low_cpu_mem_usage=True).to("cuda")
    if args.adapter:
        model = PeftModel.from_pretrained(model, args.adapter, is_trainable=False)
    model.generation_config.do_sample = False
    model.generation_config.temperature = None
    model.generation_config.top_p = None
    model.generation_config.top_k = None
    model.eval()
    data_bytes = Path(args.data).read_bytes()
    doc = json.loads(data_bytes.decode("utf-8"))
    results = []
    for row in doc["heldout"]:
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": row["prompt"]}]
        ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                            return_tensors="pt").to("cuda")
        attention_mask = torch.ones_like(ids)
        torch.cuda.synchronize()
        start = time.perf_counter_ns()
        with torch.inference_mode():
            output = model.generate(ids, attention_mask=attention_mask, max_new_tokens=48, do_sample=False,
                                    pad_token_id=tokenizer.eos_token_id)
        torch.cuda.synchronize()
        elapsed = time.perf_counter_ns() - start
        raw_text = tokenizer.decode(output[0, ids.shape[1]:], skip_special_tokens=True).strip()
        output_ids = output[0, ids.shape[1]:].detach().cpu().tolist()
        parsed, parse_error = parse_json(raw_text)
        bound = bind_intent(parsed, row["state"], row["requested_generation"])
        effect = simulate_bound(bound, row["state"])
        results.append({
            "case_id": row["case_id"], "class": row["class"], "raw_text": raw_text,
            "parsed": parsed, "parse_error": parse_error, "truth_intent": row["intent"],
            "bound": bound, "effect": effect, "latency_ns": elapsed,
            "input_tokens": int(ids.shape[1]), "output_token_ids": output_ids,
            "output_tokens": len(output_ids),
        })
    payload = {
        "schema": "qwen05b-abstention-balance-raw-arm-v1",
        "arm": args.arm, "adapter": bool(args.adapter), "seed": args.seed,
        "dataset_sha256": hashlib.sha256(data_bytes).hexdigest(),
        "results": results,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"arm": args.arm, "rows": len(results),
                      "peak_cuda_bytes": torch.cuda.max_memory_allocated()}, sort_keys=True))


if __name__ == "__main__":
    main()
