#!/usr/bin/env python3
"""Independent reconstruction; imports no trainer or cache helper."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def sha_tokens(tensor: torch.Tensor) -> str:
    return hashlib.sha256(tensor.detach().cpu().numpy().tobytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--record", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    source = json.loads(Path(args.record).read_text(encoding="utf-8"))
    corpus = [json.loads(line) for line in Path(args.corpus).read_text(encoding="utf-8").splitlines()]
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, local_files_only=True, dtype=torch.float16,
        attn_implementation="eager", low_cpu_mem_usage=True,
    ).cuda().eval()
    answer_ids = [tokenizer.encode(str(i), add_special_tokens=False) for i in range(8)]
    expected_ids = [[i] for i in range(15, 23)]
    errors: list[str] = []
    reconstructed = []
    for row_number in (0, 17, 63):
        row = corpus[row_number]
        previous = next(x for x in source["tested"] if x["bundle"] == row["bundle_id"])
        prefix_cpu = tokenizer(row["prefix"], return_tensors="pt", add_special_tokens=False).input_ids
        prefix = prefix_cpu.cuda()
        digest = sha_tokens(prefix)
        with torch.inference_mode():
            prefix_out = model(input_ids=prefix, use_cache=True, return_dict=True)
        observed = []
        for slot in (0, 7, 15):
            suffix_cpu = tokenizer(row["suffixes"][slot], return_tensors="pt", add_special_tokens=False).input_ids
            full_cpu = tokenizer(row["prefix"] + row["suffixes"][slot], return_tensors="pt", add_special_tokens=False).input_ids
            if not torch.equal(full_cpu, torch.cat((prefix_cpu, suffix_cpu), dim=1)):
                errors.append(f"{row['bundle_id']}/{slot}:concat")
            suffix = suffix_cpu.cuda()
            with torch.inference_mode():
                all_scores = model(input_ids=full_cpu.cuda(), use_cache=False, return_dict=True).logits[0, -1].float()
                private = copy.deepcopy(prefix_out.past_key_values)
                positions = torch.arange(prefix.shape[1], prefix.shape[1] + suffix.shape[1], device="cuda")
                mask = torch.ones((1, prefix.shape[1] + suffix.shape[1]), dtype=torch.long, device="cuda")
                incremental = model(input_ids=suffix, past_key_values=private,
                                    cache_position=positions, attention_mask=mask,
                                    use_cache=True, return_dict=True).logits[0, -1].float()
            full_scores = all_scores[[15, 16, 17, 18, 19, 20, 21, 22]]
            cache_scores = incremental[[15, 16, 17, 18, 19, 20, 21, 22]]
            delta = (full_scores - cache_scores).abs()
            relative = delta / full_scores.abs().clamp_min(1e-4)
            reconstructed_row = {
                "slot": slot,
                "max_abs": float(delta.max().item()),
                "max_rel": float(relative.max().item()),
                "winner_equal": int(full_scores.argmax().item()) == int(cache_scores.argmax().item()),
                "full_scores": [float(x) for x in full_scores.cpu().tolist()],
                "cached_scores": [float(x) for x in cache_scores.cpu().tolist()],
            }
            saved = next(x for x in previous["selected_code_tests"] if x["slot"] == slot)
            if (abs(reconstructed_row["max_abs"] - saved["max_abs"]) > 1e-7
                    or abs(reconstructed_row["max_rel"] - saved["max_rel"]) > 1e-4
                    or reconstructed_row["winner_equal"] != saved["winner_equal"]):
                errors.append(f"{row['bundle_id']}/{slot}:score_record_mismatch")
            observed.append(reconstructed_row)
        if answer_ids != expected_ids:
            errors.append("answer_vocabulary_changed")
        if sha_tokens(prefix) != digest:
            errors.append(f"{row['bundle_id']}:prefix_digest_changed")
        if not all(previous[key] for key in ("cache_isolation", "stale_generation_rejected",
                                             "foreign_bundle_rejected", "changed_prefix_rejected",
                                             "unsupported_multi_token_is_not_a_code")):
            errors.append(f"{row['bundle_id']}:control_receipt_false")
        reconstructed.append({"bundle": row["bundle_id"], "prefix_sha256": digest,
                              "selected_code_tests": observed,
                              "recorded_controls_revalidated": True})
    gate_pass = all(
        x["max_abs"] <= 0.002 and x["max_rel"] <= 0.002 and x["winner_equal"]
        for row in reconstructed for x in row["selected_code_tests"]
    )
    audit_status = "PASS_RECONSTRUCTION" if not errors else "HOLD_AUDIT_MISMATCH"
    result = {"kind": "independent_construction_audit", "status": audit_status,
              "errors": errors, "fixed_selected_score_gate": "PASS" if gate_pass else "FAIL",
              "independent_implementation": True, "reconstructed": reconstructed,
              "scope": "Three excluded bundles × three suffixes; not a formal latency or semantic-quality result."}
    raw = json.dumps(result, sort_keys=True, indent=2) + "\n"
    Path(args.out).write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if audit_status == "PASS_RECONSTRUCTION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
