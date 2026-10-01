#!/usr/bin/env python3
"""Excluded categorical-readout mechanics checks; emits no winner comparisons."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from cache_ops import PrefixCache, cached_scores, full_scores

ANSWER_IDS = list(range(15, 23))
MODEL_REVISION = "7ae557604adf67be50417f59c2c2f167def9a775"


def sha(ids: torch.Tensor) -> str:
    return hashlib.sha256(ids.detach().cpu().numpy().tobytes()).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if not torch.cuda.is_available() or torch.cuda.get_device_name(0) != "NVIDIA GeForce RTX 3080 Laptop GPU":
        raise RuntimeError("frozen RTX 3080 CUDA device unavailable")
    if sha_file(Path(a.model) / "model.safetensors") != "fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe":
        raise RuntimeError("frozen model weight digest mismatch")
    tok = AutoTokenizer.from_pretrained(a.model, local_files_only=True, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(a.model, local_files_only=True, dtype=torch.float16,
                                                  attn_implementation="eager", low_cpu_mem_usage=True).cuda().eval()
    ids = [tok.encode(str(i), add_special_tokens=False) for i in range(8)]
    if ids != [[i] for i in ANSWER_IDS]:
        raise RuntimeError(f"answer_ids_changed:{ids}")
    rows = [json.loads(s) for s in Path(a.corpus).read_text(encoding="utf-8").splitlines()]
    if len(rows) != 64 or any(len(x["suffixes"]) != 16 for x in rows):
        raise RuntimeError("frozen corpus dimensions changed")
    checks = []
    for ri in (0, 17, 63):
        row = rows[ri]
        prefix = tok(row["prefix"], return_tensors="pt", add_special_tokens=False).input_ids.cuda()
        generation = 1000 + ri
        digest = sha(prefix)
        with torch.inference_mode():
            prefill = model(input_ids=prefix, use_cache=True, return_dict=True)
        handle = PrefixCache(prefill.past_key_values, row["bundle_id"], generation, digest, prefix.shape[1])
        suffix_ids = [tok(row["suffixes"][s], return_tensors="pt", add_special_tokens=False).input_ids.cuda()
                      for s in (0, 7, 15)]
        for si, suffix in zip((0, 7, 15), suffix_ids):
            combined = tok(row["prefix"] + row["suffixes"][si], return_tensors="pt",
                           add_special_tokens=False).input_ids.cuda()
            if not torch.equal(combined, torch.cat((prefix, suffix), dim=1)):
                raise RuntimeError("effective_token_concat_mismatch")
        first = cached_scores(model, handle, bundle_id=row["bundle_id"], generation=generation,
                              digest=digest, suffix=suffix_ids[0])[ANSWER_IDS]
        full_probe = full_scores(model, prefix, suffix_ids[0])[ANSWER_IDS]
        _ = cached_scores(model, handle, bundle_id=row["bundle_id"], generation=generation,
                           digest=digest, suffix=suffix_ids[1])
        again = cached_scores(model, handle, bundle_id=row["bundle_id"], generation=generation,
                              digest=digest, suffix=suffix_ids[0])[ANSWER_IDS]
        if (not torch.equal(first, again) or not torch.isfinite(first).all()
                or not torch.isfinite(full_probe).all()):
            raise RuntimeError("cache_isolation_or_finite_scores_failed")
        rejected = []
        for bundle, gen, d in ((row["bundle_id"], generation + 1, digest),
                               ("foreign-" + row["bundle_id"], generation, digest),
                               (row["bundle_id"], generation, digest[::-1])):
            try:
                handle.clone(bundle_id=bundle, generation=gen, digest=d)
            except ValueError as exc:
                rejected.append(str(exc) == "stale_or_foreign_prefix_cache")
            else:
                rejected.append(False)
        if not all(rejected):
            raise RuntimeError("cache_binding_negative_control_failed")
        checks.append({"bundle": row["bundle_id"], "prefix_sha256": digest,
                       "suffixes": 3, "token_concatenation": True,
                       "finite_eight_scores_both_modes": True, "cache_isolation": True,
                       "stale_foreign_prefix_rejections": rejected})
    result = {"kind": "excluded_construction", "status": "PASS_CONSTRUCTION",
              "model_revision": MODEL_REVISION, "gpu": torch.cuda.get_device_name(0),
              "cuda": torch.version.cuda, "answer_token_ids": ANSWER_IDS,
              "corpus_bundles": 64, "suffixes_per_bundle": 16,
              "winner_comparisons_performed": 0, "checks": checks}
    Path(a.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
