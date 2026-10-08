"""One frozen GPU LoRA fit; writes adapter plus execution receipt to /out."""
import argparse
import hashlib
import json
import random
import time
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer


def encode_row(tokenizer, row):
    prompt_ids = tokenizer.apply_chat_template(
        [{"role": "system", "content": "Return only a compact intent JSON object; do not emit scope_id or generation."},
         {"role": "user", "content": row["prompt"]}], tokenize=True, add_generation_prompt=True)
    target_ids = tokenizer.encode(row["target"] + tokenizer.eos_token, add_special_tokens=False)
    return prompt_ids, target_ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=4790127)
    args = ap.parse_args()
    if not torch.cuda.is_available():
        raise SystemExit("STOP_GPU_UNAVAILABLE")
    torch.manual_seed(args.seed)
    random.seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(args.model, local_files_only=True, trust_remote_code=False,
                                                   torch_dtype=torch.float16, low_cpu_mem_usage=True)
    model.config.use_cache = False
    model.to("cuda")
    model = get_peft_model(model, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.0,
                                             target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM"))
    model.train()
    doc = json.loads(Path(args.data).read_text(encoding="utf-8"))
    rows = doc["support"]
    if len(rows) != 32:
        raise SystemExit("STOP_SUPPORT_ROWS")
    encoded = [encode_row(tokenizer, row) for row in rows]
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=2e-4)
    torch.cuda.reset_peak_memory_stats()
    start = time.perf_counter()
    losses = []
    for step in range(16):
        batch = encoded[step * 2: step * 2 + 2]
        max_len = max(len(p) + len(t) for p, t in batch)
        input_ids, attention, labels = [], [], []
        for p, t in batch:
            seq = p + t
            pad = max_len - len(seq)
            input_ids.append(seq + [tokenizer.pad_token_id] * pad)
            attention.append([1] * len(seq) + [0] * pad)
            labels.append([-100] * len(p) + t + [-100] * pad)
        ids = torch.tensor(input_ids, dtype=torch.long, device="cuda")
        mask = torch.tensor(attention, dtype=torch.long, device="cuda")
        lab = torch.tensor(labels, dtype=torch.long, device="cuda")
        optimizer.zero_grad(set_to_none=True)
        loss = model(input_ids=ids, attention_mask=mask, labels=lab).loss
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - start
    Path(args.out).mkdir(parents=True, exist_ok=True)
    model.save_pretrained(args.out)
    tokenizer.save_pretrained(args.out)
    adapter_hashes = {}
    for name in ("adapter_model.safetensors", "adapter_config.json"):
        payload = Path(args.out, name).read_bytes()
        adapter_hashes[name] = hashlib.sha256(payload).hexdigest()
    receipt = {"seed": args.seed, "rows": len(rows), "epochs": 1, "optimizer_steps": 16,
               "batch_size": 2, "rank": 8, "learning_rate": 2e-4, "fit_seconds": elapsed,
               "loss_first": losses[0], "loss_last": losses[-1],
               "peak_cuda_bytes": torch.cuda.max_memory_allocated(),
               "adapter_sha256": adapter_hashes,
               "gpu": torch.cuda.get_device_name(0), "torch": torch.__version__}
    Path(args.out, "fit.json").write_text(json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
