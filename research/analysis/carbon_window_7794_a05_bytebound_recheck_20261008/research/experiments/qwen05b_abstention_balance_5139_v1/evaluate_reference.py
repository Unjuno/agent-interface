"""Greedy base/adapter inference on the frozen held-out set."""
import argparse
import json
import math
import time
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from protocol import bind_intent, simulate_bound


def load_json(text):
    try:
        value = json.loads(text.strip())
        return value, None
    except Exception:
        return None, "invalid_json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--adapter")
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    if not torch.cuda.is_available():
        raise SystemExit("STOP_GPU_UNAVAILABLE")
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(args.model, local_files_only=True, trust_remote_code=False,
                                                   torch_dtype=torch.float16, low_cpu_mem_usage=True).to("cuda")
    if args.adapter:
        model = PeftModel.from_pretrained(model, args.adapter, is_trainable=False)
    model.generation_config.do_sample = False
    model.generation_config.temperature = None
    model.generation_config.top_p = None
    model.generation_config.top_k = None
    model.eval()
    doc = json.loads(Path(args.data).read_text(encoding="utf-8"))
    rows = doc["heldout"][:args.limit] if args.limit else doc["heldout"]
    results = []
    for row in rows:
        messages = [{"role": "system", "content": "Return only a compact intent JSON object; do not emit scope_id or generation."},
                    {"role": "user", "content": row["prompt"]}]
        ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt").to("cuda")
        attention_mask = torch.ones_like(ids)
        torch.cuda.synchronize()
        start = time.perf_counter_ns()
        with torch.inference_mode():
            output = model.generate(ids, attention_mask=attention_mask, max_new_tokens=48, do_sample=False,
                                    pad_token_id=tokenizer.eos_token_id)
        torch.cuda.synchronize()
        elapsed = time.perf_counter_ns() - start
        raw_text = tokenizer.decode(output[0, ids.shape[1]:], skip_special_tokens=True).strip()
        output_token_ids = output[0, ids.shape[1]:].detach().cpu().tolist()
        parsed, parse_error = load_json(raw_text)
        bound = bind_intent(parsed, row["state"], row["requested_generation"])
        effect = simulate_bound(bound, row["state"])
        results.append({"case_id": row["case_id"], "raw_text": raw_text, "parsed": parsed,
                        "parse_error": parse_error, "bound": bound, "effect": effect, "latency_ns": elapsed,
                        "input_tokens": int(ids.shape[1]), "output_token_ids": output_token_ids,
                        "output_tokens": len(output_token_ids)})
    payload = {"arm": "adapter" if args.adapter else "base", "results": results}
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"arm": payload["arm"], "n": len(results),
                      "p95_ns": sorted(x["latency_ns"] for x in results)[math.ceil(len(results)*0.95)-1],
                      "mean_output_tokens": sum(x["output_tokens"] for x in results)/len(results)}))


if __name__ == "__main__":
    main()

