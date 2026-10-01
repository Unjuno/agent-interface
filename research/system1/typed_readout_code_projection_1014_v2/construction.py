#!/usr/bin/env python3
"""Excluded GPU construction for answer-code-only equivalence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from cache_mechanics import CacheHandle, cached_logits, full_logits

MODEL_SHA = "fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe"
ANSWERS = [str(i) for i in range(8)]
ANSWER_IDS = [15, 16, 17, 18, 19, 20, 21, 22]
ATOL = RTOL = 0.002


def prefix_digest(ids: torch.Tensor) -> str:
    return hashlib.sha256(ids.detach().cpu().numpy().tobytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable")
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, local_files_only=True, dtype=torch.float16,
        attn_implementation="eager", low_cpu_mem_usage=True,
    ).cuda().eval()
    if torch.cuda.get_device_name(0) != "NVIDIA GeForce RTX 3080 Laptop GPU":
        raise RuntimeError("unexpected construction GPU")
    encoded = [tokenizer.encode(answer, add_special_tokens=False) for answer in ANSWERS]
    if encoded != [[x] for x in ANSWER_IDS] or len(set(ANSWER_IDS)) != 8:
        raise RuntimeError(f"answer_token_ids_changed:{encoded}")

    rows = [json.loads(line) for line in Path(args.corpus).read_text(encoding="utf-8").splitlines()]
    if len(rows) != 64 or any(len(row["suffixes"]) != 16 for row in rows):
        raise ValueError("predecessor corpus shape mismatch")
    tested = []
    for row_index in (0, 17, 63):
        row = rows[row_index]
        prefix = tokenizer(row["prefix"], return_tensors="pt", add_special_tokens=False).input_ids.cuda()
        digest = prefix_digest(prefix)
        generation = 1000 + row_index
        with torch.inference_mode():
            prefill = model(input_ids=prefix, use_cache=True, return_dict=True)
        handle = CacheHandle(prefill.past_key_values, row["bundle_id"], generation, digest, prefix.shape[1])
        deltas = []
        winner_matches = []
        vectors = []
        for slot in (0, 7, 15):
            suffix = tokenizer(row["suffixes"][slot], return_tensors="pt", add_special_tokens=False).input_ids.cuda()
            combined = tokenizer(row["prefix"] + row["suffixes"][slot], return_tensors="pt", add_special_tokens=False).input_ids.cuda()
            if not torch.equal(combined, torch.cat((prefix, suffix), dim=1)):
                raise ValueError("effective token sequence changed across boundary")
            full = full_logits(model, prefix, suffix)[ANSWER_IDS]
            cached = cached_logits(model, handle, bundle_id=row["bundle_id"], generation=generation,
                                   prefix_sha256=digest, suffix_ids=suffix)[ANSWER_IDS]
            delta = (full - cached).abs()
            relative = delta / full.abs().clamp_min(1e-4)
            deltas.append({"slot": slot, "max_abs": float(delta.max().item()),
                           "max_rel": float(relative.max().item()),
                           "within_tolerance": bool(torch.allclose(full, cached, atol=ATOL, rtol=RTOL)),
                           "winner_equal": int(full.argmax().item()) == int(cached.argmax().item()),
                           "full_scores": [float(x) for x in full.cpu().tolist()],
                           "cached_scores": [float(x) for x in cached.cpu().tolist()]})
            vectors.append(cached)
        # A suffix cannot change the next independent suffix's prefix state.
        s0 = tokenizer(row["suffixes"][0], return_tensors="pt", add_special_tokens=False).input_ids.cuda()
        s1 = tokenizer(row["suffixes"][1], return_tensors="pt", add_special_tokens=False).input_ids.cuda()
        first = cached_logits(model, handle, bundle_id=row["bundle_id"], generation=generation,
                              prefix_sha256=digest, suffix_ids=s0)
        _ = cached_logits(model, handle, bundle_id=row["bundle_id"], generation=generation,
                          prefix_sha256=digest, suffix_ids=s1)
        again = cached_logits(model, handle, bundle_id=row["bundle_id"], generation=generation,
                              prefix_sha256=digest, suffix_ids=s0)
        if not torch.equal(first, again):
            raise ValueError("per_suffix_isolation_failed")

        rejected = []
        for bundle_id, gen, prefix_hash in (
            (row["bundle_id"], generation + 1, digest),
            (f"foreign-{row_index}", generation, digest),
            (row["bundle_id"], generation, digest[::-1]),
        ):
            try:
                handle.private_copy(bundle_id=bundle_id, generation=gen, prefix_sha256=prefix_hash)
            except ValueError as exc:
                rejected.append(str(exc) == "stale_or_foreign_prefix_cache")
            else:
                rejected.append(False)
        if tokenizer.encode("NOT_A_SINGLE_CODE", add_special_tokens=False).__len__() == 1:
            raise ValueError("unsupported_text_accidentally_single_token")
        if not all(rejected):
            raise ValueError("cache_binding_negative_control_accepted")
        tested.append({"bundle": row["bundle_id"], "prefix_tokens": prefix.shape[1],
                       "selected_code_tests": deltas, "cache_isolation": True,
                       "stale_generation_rejected": rejected[0],
                       "foreign_bundle_rejected": rejected[1],
                       "changed_prefix_rejected": rejected[2],
                       "unsupported_multi_token_is_not_a_code": True})
    status = "PASS_CONSTRUCTION" if all(
        item["within_tolerance"] and item["winner_equal"]
        for row in tested for item in row["selected_code_tests"]
    ) else "STOP_SELECTED_CODE_TOLERANCE"
    result = {"kind": "excluded_construction", "status": status,
              "model_revision": "7ae557604adf67be50417f59c2c2f167def9a775",
              "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(0),
              "answer_token_ids": ANSWER_IDS, "tested": tested,
              "controls": {"effective_token_concat": True, "single_token_vocabulary": True,
                           "cache_isolation": True, "stale_foreign_prefix_rejected": True,
                           "unsupported_multi_token_not_admitted": True}}
    raw = json.dumps(result, sort_keys=True, indent=2) + "\n"
    Path(args.out).write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if status == "PASS_CONSTRUCTION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
