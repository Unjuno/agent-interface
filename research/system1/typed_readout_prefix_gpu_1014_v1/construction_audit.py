#!/usr/bin/env python3
"""Independent read-only reconstruction of CONSTRUCTION_002; imports no runner code."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--record", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    with open(args.corpus, encoding="utf-8") as stream:
        corpus = [json.loads(line) for line in stream]
    frozen = json.loads(Path(args.record).read_text(encoding="utf-8"))
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, local_files_only=True, dtype=torch.float16,
        attn_implementation="eager", low_cpu_mem_usage=True,
    ).cuda().eval()
    reconstructed = []
    exact = True
    for index in (0, 17, 63):
        row = corpus[index]
        prefix = tokenizer(row["prefix"], return_tensors="pt", add_special_tokens=False).input_ids.cuda()
        with torch.inference_mode():
            prefix_output = model(input_ids=prefix, use_cache=True, return_dict=True)
        abs_max = rel_max = 0.0
        argmax_changes = 0
        for slot in (0, 7, 15):
            suffix = tokenizer(row["suffixes"][slot], return_tensors="pt", add_special_tokens=False).input_ids.cuda()
            combined = tokenizer(row["prefix"] + row["suffixes"][slot], return_tensors="pt", add_special_tokens=False).input_ids.cuda()
            with torch.inference_mode():
                full = model(input_ids=combined, use_cache=False, return_dict=True).logits[0, -1].float()
                private_cache = copy.deepcopy(prefix_output.past_key_values)
                cache_position = torch.arange(prefix.shape[1], prefix.shape[1] + suffix.shape[1], device="cuda")
                mask = torch.ones((1, prefix.shape[1] + suffix.shape[1]), dtype=torch.long, device="cuda")
                cached = model(input_ids=suffix, past_key_values=private_cache,
                               cache_position=cache_position, attention_mask=mask,
                               use_cache=True, return_dict=True).logits[0, -1].float()
            diff = (full - cached).abs()
            relative = diff / full.abs().clamp_min(1e-4)
            abs_max = max(abs_max, float(diff.max().item()))
            rel_max = max(rel_max, float(relative.max().item()))
            argmax_changes += int(full.argmax().item() != cached.argmax().item())
            if not torch.allclose(full, cached, atol=0.002, rtol=0.002):
                exact = False
        expected = next(x for x in frozen["tested"] if x["bundle"] == row["bundle_id"])
        matched = (
            abs(abs_max - expected["max_abs"]) < 1e-7
            and abs(rel_max - expected["max_rel"]) < 1e-4
            and argmax_changes == expected["argmax_changes"]
        )
        reconstructed.append({"bundle": row["bundle_id"], "max_abs": abs_max,
                              "max_rel": rel_max, "argmax_changes": argmax_changes,
                              "matches_retained_record": matched})
    result = {"kind": "independent_construction_audit", "status": "PASS_RECONSTRUCTION" if all(x["matches_retained_record"] for x in reconstructed) and not exact else "HOLD_AUDIT_MISMATCH",
              "errors": [], "fixed_tolerance_gate": "FAIL" if not exact else "PASS",
              "reconstructed": reconstructed,
              "scope": "Three excluded synthetic bundles, three question slots each. Confirms only the retained construction mismatch and does not substitute for the preregistered 64-bundle formal block.",
              "independent_implementation": True}
    raw = json.dumps(result, sort_keys=True, indent=2) + "\n"
    Path(args.out).write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if result["status"] == "PASS_RECONSTRUCTION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
