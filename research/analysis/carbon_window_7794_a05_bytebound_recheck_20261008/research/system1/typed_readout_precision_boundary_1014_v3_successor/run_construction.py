#!/usr/bin/env python3
"""One-shot precision-boundary construction for Issue #4875; no generation or training."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from cache_mechanics import load_corpus, run_cached, run_full

EXPECTED_CORPUS_SHA256 = "85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c"
EXPECTED_WEIGHT_SHA256 = "fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe"
MODEL_FILES = {
    ".gitattributes": "11ad7efa24975ee4b0c3c3a38ed18737f0658a5f75a0a96787b576a78a023361",
    "config.json": "18e18afcaccafade98daf13a54092927904649e1dd4eba8299ab717d5d94ff45",
    "generation_config.json": "e558847a8b4402616f1273797b015104dc266fe4b520056fca88823ba8f8ebe6",
    "LICENSE": "832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e",
    "merges.txt": "599bab54075088774b1733fde865d5bd747cbcc7a547c5bc12610e874e26f5e3",
    "model.safetensors": EXPECTED_WEIGHT_SHA256,
    "README.md": "b19c806a904db6dc878a0462e70b551f6b7ac78dfbb88c2eb966ca2b9109ae15",
    "tokenizer.json": "c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539",
    "tokenizer_config.json": "5b5d4f65d0acd3b2d56a35b56d374a36cbc1c8fa5cf3b3febbbfabf22f359583",
    "vocab.json": "ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910",
}
ANSWERS = [str(i) for i in range(8)]
ANSWER_IDS = list(range(15, 23))
MODES = {"fp16": torch.float16, "bf16": torch.bfloat16, "fp32": torch.float32}
ROW_SPECS = [("B00", 0), ("B00", 7), ("B00", 15),
             ("B17", 0), ("B17", 7), ("B17", 15),
             ("B63", 0), ("B63", 7), ("B63", 15)]
ATOL = 0.002
RTOL = 0.002


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_inputs(model_dir: Path, corpus_path: Path) -> None:
    if sha(corpus_path) != EXPECTED_CORPUS_SHA256:
        raise RuntimeError("STOP_CORPUS_HASH_MISMATCH")
    for name, expected in MODEL_FILES.items():
        path = model_dir / name
        if not path.is_file() or sha(path) != expected:
            raise RuntimeError(f"STOP_MODEL_ASSET_HASH_MISMATCH:{name}")


def selected_logits(logits: torch.Tensor) -> list[float]:
    return [float(x) for x in logits[ANSWER_IDS].detach().to("cpu", dtype=torch.float32).tolist()]


def compare(a: list[float], b: list[float]) -> dict:
    abs_d = [abs(x - y) for x, y in zip(a, b, strict=True)]
    rel_d = [d / max(abs(x), 1e-4) for d, x in zip(abs_d, a, strict=True)]
    return {
        "max_abs": max(abs_d), "max_rel": max(rel_d),
        "argmax_equal": max(range(8), key=lambda i: (a[i], -i)) == max(range(8), key=lambda i: (b[i], -i)),
        "within_tolerance": max(abs_d) <= ATOL and max(rel_d) <= RTOL,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("STOP_CUDA_UNAVAILABLE")
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("STOP_BF16_UNSUPPORTED")
    if args.out.exists() and any(args.out.iterdir()):
        raise RuntimeError("STOP_OUTPUT_NOT_EMPTY")
    args.out.mkdir(parents=True, exist_ok=True)
    verify_inputs(args.model, args.corpus)
    rows = load_corpus(str(args.corpus))
    by_id = {row["bundle_id"]: row for row in rows}
    if set(by_id) != {f"B{i:02d}" for i in range(64)}:
        raise RuntimeError("STOP_CORPUS_ROWS_INVALID")

    tokenizer = AutoTokenizer.from_pretrained(str(args.model), local_files_only=True, use_fast=True)
    actual_answer_ids = [tokenizer.encode(s, add_special_tokens=False) for s in ANSWERS]
    if actual_answer_ids != [[i] for i in ANSWER_IDS]:
        raise RuntimeError(f"STOP_ANSWER_TOKEN_IDS:{actual_answer_ids}")

    result = {
        "allocation": "typed-readout-precision-boundary-1014-v3-successor-20260927-01",
        "status": "RUNNING", "corpus_sha256": sha(args.corpus),
        "weights_sha256": sha(args.model / "model.safetensors"),
        "answer_ids": ANSWER_IDS, "answer_strings": ANSWERS,
        "answer_token_ids_verified": True, "torch": torch.__version__,
        "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(0),
        "rows": [], "modes": {},
    }
    started = time.time()
    for mode_name, dtype in MODES.items():
        torch.cuda.reset_peak_memory_stats()
        model = AutoModelForCausalLM.from_pretrained(
            str(args.model), local_files_only=True, torch_dtype=dtype,
            attn_implementation="eager", low_cpu_mem_usage=True,
        ).to("cuda").eval()
        mode_rows = []
        for bundle_id, slot in ROW_SPECS:
            row = by_id[bundle_id]
            prefix_ids = tokenizer(row["prefix"], return_tensors="pt", add_special_tokens=False).input_ids.to("cuda")
            suffix_ids = tokenizer(row["suffixes"][slot], return_tensors="pt", add_special_tokens=False).input_ids.to("cuda")
            joined_ids = tokenizer(row["prefix"] + row["suffixes"][slot], return_tensors="pt", add_special_tokens=False).input_ids.to("cuda")
            if not torch.equal(joined_ids, torch.cat((prefix_ids, suffix_ids), dim=1)):
                raise RuntimeError(f"STOP_TOKENIZATION_NOT_CONCATENATIVE:{bundle_id}:{slot}")
            with torch.inference_mode():
                prefix_out = model(input_ids=prefix_ids, use_cache=True, return_dict=True)
            base_cache = prefix_out.past_key_values
            full = selected_logits(run_full(model, prefix_ids, suffix_ids))
            cached = selected_logits(run_cached(model, base_cache, prefix_ids.shape[1], suffix_ids))
            # Verify suffix independence against intervening use of other suffixes.
            first = selected_logits(run_cached(model, base_cache, prefix_ids.shape[1], suffix_ids))
            other_slot = (slot + 1) % 16
            other_ids = tokenizer(row["suffixes"][other_slot], return_tensors="pt", add_special_tokens=False).input_ids.to("cuda")
            _ = run_cached(model, base_cache, prefix_ids.shape[1], other_ids)
            again = selected_logits(run_cached(model, base_cache, prefix_ids.shape[1], suffix_ids))
            comparison = compare(full, cached)
            record = {"mode": mode_name, "bundle_id": bundle_id, "slot": slot,
                      "suffix_tokens": int(suffix_ids.shape[1]), "full_logits": full,
                      "cached_logits": cached, "comparison": comparison,
                      "cache_isolation": first == again}
            mode_rows.append(record)
            result["rows"].append(record)
            del base_cache, prefix_out, prefix_ids, suffix_ids, joined_ids, full, cached, first, again, other_ids
        torch.cuda.synchronize()
        result["modes"][mode_name] = {
            "dtype": str(dtype), "rows": len(mode_rows),
            "all_within_tolerance": all(x["comparison"]["within_tolerance"] for x in mode_rows),
            "all_winners_equal": all(x["comparison"]["argmax_equal"] for x in mode_rows),
            "all_cache_isolation": all(x["cache_isolation"] for x in mode_rows),
            "peak_cuda_bytes": torch.cuda.max_memory_allocated(),
        }
        del model
        gc.collect()
        torch.cuda.empty_cache()
    result["elapsed_seconds_descriptive_only"] = time.time() - started
    result["status"] = "CONSTRUCTION_COMPLETE"
    raw = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    (args.out / "result.json").write_bytes(raw)
    print(json.dumps({"status": result["status"], "rows": len(result["rows"]),
                      "modes": result["modes"], "result_sha256": hashlib.sha256(raw).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
