#!/usr/bin/env python3
"""Excluded construction checks against one local pinned model snapshot."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from cache_mechanics import load_corpus, run_cached, run_full

ANSWERS = [str(i) for i in range(8)]
ATOL = 0.002
RTOL = 0.002


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    device = torch.device("cuda")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable")
    torch.manual_seed(0)
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, local_files_only=True, torch_dtype=torch.float16,
        attn_implementation="eager", low_cpu_mem_usage=True,
    ).to(device).eval()
    rows = load_corpus(args.corpus)
    answer_ids = []
    for answer in ANSWERS:
        # Suffixes end with a newline and assistant header, so the candidate
        # label itself is the next token (no synthetic leading-space token).
        ids = tokenizer.encode(answer, add_special_tokens=False)
        if len(ids) != 1:
            raise ValueError(f"answer code is not one token: {answer}: {ids}")
        answer_ids.append(ids[0])

    result = {"kind": "excluded_construction", "status": "PASS", "answer_token_ids": answer_ids,
              "tested": [], "controls": {}, "torch": torch.__version__,
              "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(0)}
    for row in (rows[0], rows[17], rows[63]):
        prefix = tokenizer(row["prefix"], return_tensors="pt", add_special_tokens=False).input_ids
        if len(prefix[0]) < 8:
            raise ValueError("unexpectedly short prefix")
        with torch.inference_mode():
            base = model(input_ids=prefix.to(device), use_cache=True, return_dict=True)
        max_abs = 0.0
        max_rel = 0.0
        argmax_changes = 0
        for suffix in (row["suffixes"][0], row["suffixes"][7], row["suffixes"][15]):
            suffix_ids = tokenizer(suffix, return_tensors="pt", add_special_tokens=False).input_ids
            full_ids = tokenizer(row["prefix"] + suffix, return_tensors="pt", add_special_tokens=False).input_ids
            if not torch.equal(full_ids, torch.cat((prefix, suffix_ids), dim=1)):
                raise ValueError("prefix+suffix tokenization is not concatenative")
            a = run_full(model, prefix.to(device), suffix_ids.to(device))
            b = run_cached(model, base.past_key_values, prefix.shape[1], suffix_ids.to(device))
            diff = (a - b).abs()
            rel = diff / a.abs().clamp_min(1e-4)
            max_abs = max(max_abs, float(diff.max().item()))
            max_rel = max(max_rel, float(rel.max().item()))
            argmax_changes += int(a.argmax().item() != b.argmax().item())
            if not torch.allclose(a, b, atol=ATOL, rtol=RTOL):
                result["status"] = "STOP_CONSTRUCTION_LOGIT_TOLERANCE"
            if a.argmax().item() != b.argmax().item():
                result["status"] = "STOP_CONSTRUCTION_ARGMAX_CHANGE"
        # A prior suffix must not mutate the cache used by a later independent
        # suffix; re-evaluate from the original prefix cache.
        s0 = tokenizer(row["suffixes"][0], return_tensors="pt", add_special_tokens=False).input_ids.to(device)
        s1 = tokenizer(row["suffixes"][1], return_tensors="pt", add_special_tokens=False).input_ids.to(device)
        first = run_cached(model, base.past_key_values, prefix.shape[1], s0)
        _ = run_cached(model, base.past_key_values, prefix.shape[1], s1)
        again = run_cached(model, base.past_key_values, prefix.shape[1], s0)
        result["tested"].append({"bundle": row["bundle_id"], "prefix_tokens": prefix.shape[1],
                                 "max_abs": max_abs, "max_rel": max_rel,
                                 "argmax_changes": argmax_changes,
                                 "cross_suffix_isolation": bool(torch.equal(first, again))})
    result["controls"]["single_token_answer_vocab"] = len(answer_ids) == len(set(answer_ids)) == 8
    result["controls"]["cross_suffix_isolation"] = all(x["cross_suffix_isolation"] for x in result["tested"])
    if not result["controls"]["single_token_answer_vocab"] or not result["controls"]["cross_suffix_isolation"]:
        result["status"] = "STOP_CONSTRUCTION_CONTROL"
    raw = json.dumps(result, sort_keys=True, indent=2) + "\n"
    Path(args.out).write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
