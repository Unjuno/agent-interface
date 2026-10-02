"""One deterministic rank-8 LoRA fit for one frozen support-sampling arm."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

SYSTEM = "Return only a compact intent JSON object; do not emit scope_id or generation."


def encode_row(tokenizer, row):
    prompt_ids = tokenizer.apply_chat_template(
        [{"role": "system", "content": SYSTEM}, {"role": "user", "content": row["prompt"]}],
        tokenize=True, add_generation_prompt=True)
    target_ids = tokenizer.encode(row["target"] + tokenizer.eos_token, add_special_tokens=False)
    return prompt_ids, target_ids


def lora_state_hash(model):
    digest = hashlib.sha256()
    for name, parameter in sorted(model.named_parameters()):
        if "lora_" in name:
            digest.update(name.encode("utf-8") + b"\0")
            digest.update(parameter.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--arm", choices=("imbalanced", "balanced"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise SystemExit("STOP_GPU_UNAVAILABLE")
    torch.manual_seed(args.seed)
    random.seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model, local_files_only=True, trust_remote_code=False,
        torch_dtype=torch.float16, low_cpu_mem_usage=True)
    model.config.use_cache = False
    model.to("cuda")
    model = get_peft_model(model, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.0,
                                             target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM",
                                             init_lora_weights=True))
    initial_lora_sha256 = lora_state_hash(model)
    model.train()
    doc = json.loads(Path(args.data).read_text(encoding="utf-8"))
    rows = doc["supports"][args.arm]
    if len(rows) != 32:
        raise SystemExit("STOP_SUPPORT_ROWS")
    encoded = [encode_row(tokenizer, row) for row in rows]
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad),
                                  lr=2e-4, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.01)
    torch.cuda.reset_peak_memory_stats()
    start = time.perf_counter()
    losses = []
    for step in range(16):
        batch = encoded[step * 2: step * 2 + 2]
        max_len = max(len(prompt) + len(target) for prompt, target in batch)
        input_ids, attention, labels = [], [], []
        for prompt, target in batch:
            sequence = prompt + target
            padding = max_len - len(sequence)
            input_ids.append(sequence + [tokenizer.pad_token_id] * padding)
            attention.append([1] * len(sequence) + [0] * padding)
            labels.append([-100] * len(prompt) + target + [-100] * padding)
        ids = torch.tensor(input_ids, dtype=torch.long, device="cuda")
        mask = torch.tensor(attention, dtype=torch.long, device="cuda")
        labels = torch.tensor(labels, dtype=torch.long, device="cuda")
        optimizer.zero_grad(set_to_none=True)
        loss = model(input_ids=ids, attention_mask=mask, labels=labels).loss
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - start
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=False)
    model.save_pretrained(output)
    adapter_hashes = {}
    for name in ("adapter_model.safetensors", "adapter_config.json"):
        adapter_hashes[name] = hashlib.sha256((output / name).read_bytes()).hexdigest()
    receipt = {
        "arm": args.arm, "seed": args.seed, "case_ids_in_training_order": [r["case_id"] for r in rows],
        "rows": len(rows), "epochs": 1, "optimizer_steps": 16, "batch_size": 2,
        "rank": 8, "lora_alpha": 16, "lora_dropout": 0.0, "learning_rate": 2e-4,
        "optimizer": "AdamW", "betas": [0.9, 0.999], "eps": 1e-8,
        "weight_decay": 0.01, "initial_optimizer_state": "empty",
        "torch_seed": args.seed, "python_random_seed": args.seed,
        "initial_lora_sha256": initial_lora_sha256, "fit_seconds": elapsed,
        "loss_first": losses[0], "loss_last": losses[-1],
        "peak_cuda_bytes": torch.cuda.max_memory_allocated(),
        "adapter_sha256": adapter_hashes, "gpu": torch.cuda.get_device_name(0),
        "torch": torch.__version__,
    }
    (output / "fit.json").write_text(json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
