#!/usr/bin/env python3
"""Excluded GPU identity, token-boundary, and cache-isolation controls."""

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

from cache_mechanics import CacheHandle, cached_logits

ANSWERS = [str(i) for i in range(8)]
ANSWER_IDS = list(range(15, 23))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def token_sha(tensor):
    return hashlib.sha256(tensor.detach().cpu().numpy().tobytes()).hexdigest()


def verify_model_manifest(model_path, manifest_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    actual = {}
    for path in Path(model_path).rglob("*"):
        if path.is_file():
            actual[path.relative_to(model_path).as_posix()] = {
                "size": path.stat().st_size, "sha256": sha(path)
            }
    expected = {item["path"]: {"size": item["size"], "sha256": item["sha256"]}
                for item in manifest["files"]}
    return actual == expected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--study", required=True)
    args = ap.parse_args()
    study = Path(args.study)
    freeze = json.loads((study / "FREEZE.json").read_text(encoding="utf-8"))
    errors = []
    if not verify_model_manifest(args.model, study / "MODEL_MANIFEST.json"):
        errors.append("model_manifest_inventory")
    if sha(args.corpus) != freeze["corpus_sha256"]:
        errors.append("corpus_sha256")
    if torch.__version__ != "2.5.1+cu121" or torch.version.cuda != "12.1":
        errors.append("torch_cuda_version")
    if transformers.__version__ != "5.16.1":
        errors.append("transformers_version")
    if not torch.cuda.is_available():
        errors.append("cuda_unavailable")
    else:
        gpu = torch.cuda.get_device_name(0)
        if gpu != "NVIDIA GeForce RTX 3080 Laptop GPU":
            errors.append("gpu_identity")
    rows = [json.loads(line) for line in Path(args.corpus).read_text(encoding="utf-8").splitlines()]
    if len(rows) != 64 or any(len(row.get("suffixes", [])) != 16 for row in rows):
        errors.append("corpus_dimensions")
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, use_fast=True)
    answer_tokens = [tokenizer.encode(value, add_special_tokens=False) for value in ANSWERS]
    if answer_tokens != [[value] for value in ANSWER_IDS]:
        errors.append("answer_token_ids")
    model = AutoModelForCausalLM.from_pretrained(
        args.model, local_files_only=True, dtype=torch.float16,
        attn_implementation="eager", low_cpu_mem_usage=True,
    ).cuda().eval()

    concat_count = 0
    tokenized = {}
    for row in rows:
        prefix = tokenizer(row["prefix"], return_tensors="pt", add_special_tokens=False).input_ids
        for slot, suffix_text in enumerate(row["suffixes"]):
            suffix = tokenizer(suffix_text, return_tensors="pt", add_special_tokens=False).input_ids
            combined = tokenizer(row["prefix"] + suffix_text, return_tensors="pt", add_special_tokens=False).input_ids
            if not torch.equal(combined, torch.cat((prefix, suffix), dim=1)):
                errors.append(f"token_boundary:{row['bundle_id']}:{slot}")
            tokenized[(row["bundle_id"], slot)] = (prefix, suffix)
            concat_count += 1

    tested = []
    if not errors:
        for row in (rows[0], rows[17], rows[63]):
            prefix, suffix0 = tokenized[(row["bundle_id"], 0)]
            suffix1 = tokenized[(row["bundle_id"], 1)][1]
            prefix_gpu = prefix.cuda()
            prefix_digest = token_sha(prefix_gpu)
            generation = 1000 + int(row["bundle_id"][1:])
            with torch.inference_mode():
                pref = model(input_ids=prefix_gpu, use_cache=True, return_dict=True)
            handle = CacheHandle(pref.past_key_values, row["bundle_id"], generation, prefix_digest, prefix.shape[1])
            first = cached_logits(model, handle, bundle_id=row["bundle_id"], generation=generation,
                                  prefix_sha256=prefix_digest, suffix_ids=suffix0.cuda())[ANSWER_IDS]
            _ = cached_logits(model, handle, bundle_id=row["bundle_id"], generation=generation,
                              prefix_sha256=prefix_digest, suffix_ids=suffix1.cuda())
            again = cached_logits(model, handle, bundle_id=row["bundle_id"], generation=generation,
                                  prefix_sha256=prefix_digest, suffix_ids=suffix0.cuda())[ANSWER_IDS]
            isolation = torch.equal(first, again)
            if not isolation:
                errors.append("cache_isolation:" + row["bundle_id"])
            rejected = 0
            for bundle, gen, digest in ((row["bundle_id"], generation + 1, prefix_digest),
                                        ("foreign", generation, prefix_digest),
                                        (row["bundle_id"], generation, prefix_digest[::-1])):
                try:
                    handle.private_copy(bundle_id=bundle, generation=gen, prefix_sha256=digest)
                except ValueError as exc:
                    rejected += int(str(exc) == "stale_or_foreign_prefix_cache")
            if rejected != 3:
                errors.append("stale_or_foreign_cache_rejection:" + row["bundle_id"])
            tested.append({"bundle_id": row["bundle_id"], "prefix_sha256": prefix_digest,
                           "prefix_tokens": int(prefix.shape[1]), "cache_isolation": isolation,
                           "stale_foreign_prefix_rejections": rejected})
    result = {
        "schema": "typed-decision-equivalence-construction-v1",
        "status": "PASS_CONSTRUCTION" if not errors else "STOP_CONSTRUCTION",
        "errors": errors,
        "model_sha256": sha(Path(args.model) / "model.safetensors"),
        "corpus_sha256": sha(args.corpus),
        "torch": torch.__version__, "cuda": torch.version.cuda,
        "transformers": transformers.__version__,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "answer_token_ids": [entry[0] if len(entry) == 1 else entry for entry in answer_tokens],
        "token_boundary_pairs_checked": concat_count,
        "tested_cache_bundles": tested,
        "formal_invocations": 0,
    }
    raw = json.dumps(result, sort_keys=True, indent=2) + "\n"
    Path(args.out).write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
