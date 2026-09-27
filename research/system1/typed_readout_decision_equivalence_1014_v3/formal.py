#!/usr/bin/env python3
"""One paired full-corpus categorical decision run for Issue #4652."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from cache_ops import PrefixCache, cached_scores, full_scores

ANSWER_IDS = list(range(15, 23))
MODEL_REVISION = "7ae557604adf67be50417f59c2c2f167def9a775"
CORPUS_SHA256 = "85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c"
WEIGHT_SHA256 = "fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe"


def digest(ids: torch.Tensor) -> str:
    return hashlib.sha256(ids.detach().cpu().numpy().tobytes()).hexdigest()


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def summarise(scores: torch.Tensor) -> dict:
    vals = scores[ANSWER_IDS].float()
    top = torch.topk(vals, 2)
    return {"scores": [float(x) for x in vals.cpu().tolist()],
            "winner_token_id": ANSWER_IDS[int(torch.argmax(vals).item())],
            "margin": float((top.values[0] - top.values[1]).item())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    corpus_bytes = Path(a.corpus).read_bytes()
    corpus_sha = hashlib.sha256(corpus_bytes).hexdigest()
    if corpus_sha != CORPUS_SHA256:
        raise RuntimeError(f"corpus_sha256_changed:{corpus_sha}")
    if not torch.cuda.is_available() or torch.cuda.get_device_name(0) != "NVIDIA GeForce RTX 3080 Laptop GPU":
        raise RuntimeError("frozen RTX 3080 CUDA device unavailable")
    if file_digest(Path(a.model) / "model.safetensors") != WEIGHT_SHA256:
        raise RuntimeError("frozen model weight digest mismatch")
    torch.cuda.reset_peak_memory_stats()
    tok = AutoTokenizer.from_pretrained(a.model, local_files_only=True, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(a.model, local_files_only=True, dtype=torch.float16,
                                                  attn_implementation="eager", low_cpu_mem_usage=True).cuda().eval()
    ids = [tok.encode(str(i), add_special_tokens=False) for i in range(8)]
    if ids != [[i] for i in ANSWER_IDS]:
        raise RuntimeError(f"answer_ids_changed:{ids}")
    rows = [json.loads(s) for s in corpus_bytes.decode("utf-8").splitlines()]
    if len(rows) != 64 or any(len(x["suffixes"]) != 16 for x in rows):
        raise RuntimeError("frozen corpus dimensions changed")
    records = []
    started = time.perf_counter()
    for ri, row in enumerate(rows):
        prefix = tok(row["prefix"], return_tensors="pt", add_special_tokens=False).input_ids.cuda()
        generation = 1000 + ri
        prefix_sha = digest(prefix)
        with torch.inference_mode():
            prefill = model(input_ids=prefix, use_cache=True, return_dict=True)
        handle = PrefixCache(prefill.past_key_values, row["bundle_id"], generation, prefix_sha, prefix.shape[1])
        for si, suffix_text in enumerate(row["suffixes"]):
            suffix = tok(suffix_text, return_tensors="pt", add_special_tokens=False).input_ids.cuda()
            combined = tok(row["prefix"] + suffix_text, return_tensors="pt", add_special_tokens=False).input_ids.cuda()
            if not torch.equal(combined, torch.cat((prefix, suffix), dim=1)):
                raise RuntimeError(f"effective_token_concat_mismatch:{ri}:{si}")
            # Fixed paired order is FULL then CACHED for each bundle/slot.
            t0 = time.perf_counter()
            f = summarise(full_scores(model, prefix, suffix))
            torch.cuda.synchronize()
            t1 = time.perf_counter()
            c = summarise(cached_scores(model, handle, bundle_id=row["bundle_id"],
                                        generation=generation, digest=prefix_sha, suffix=suffix))
            torch.cuda.synchronize()
            t2 = time.perf_counter()
            records.append({"bundle_index": ri, "bundle_id": row["bundle_id"], "slot": si,
                            "prefix_tokens": int(prefix.shape[1]), "prefix_sha256": prefix_sha,
                            "suffix_tokens": int(suffix.shape[1]), "full": f, "cached": c,
                            "winner_equal": f["winner_token_id"] == c["winner_token_id"],
                            "full_elapsed_ms": (t1 - t0) * 1000.0,
                            "cached_elapsed_ms": (t2 - t1) * 1000.0})
    elapsed = time.perf_counter() - started
    mismatches = sum(not x["winner_equal"] for x in records)
    if len(records) != 1024:
        status = "STOP_INCOMPLETE_FORMAL_OUTPUT"
    elif mismatches:
        status = "FAIL_TYPED_DECISION_DIVERGENCE"
    else:
        status = "PASS_TYPED_DECISION_EQUIVALENCE_1024"
    result = {"kind": "formal_full_corpus_categorical_readout", "allocation": "4652-v1",
              "status": status,
              "model_revision": MODEL_REVISION, "weight_sha256": WEIGHT_SHA256,
              "corpus_sha256": corpus_sha, "answer_token_ids": ANSWER_IDS,
              "gpu": torch.cuda.get_device_name(0), "cuda": torch.version.cuda,
              "paired_rows": len(records), "winner_mismatches": mismatches,
              "wall_seconds_including_bundle_prefill": elapsed,
              "peak_cuda_bytes": torch.cuda.max_memory_allocated(),
              "records": records}
    Path(a.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "records"}, indent=2, sort_keys=True))
    return 0 if status == "PASS_TYPED_DECISION_EQUIVALENCE_1024" else 2


if __name__ == "__main__":
    raise SystemExit(main())
