#!/usr/bin/env python3
"""Independent full/cached reconstruction audit; imports no experiment helper."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ANSWER_IDS = list(range(15, 23))
CORPUS_SHA256 = "85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c"
WEIGHT_SHA256 = "fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe"


def tensor_sha(x: torch.Tensor) -> str:
    return hashlib.sha256(x.detach().cpu().numpy().tobytes()).hexdigest()


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--record", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    raw = Path(a.corpus).read_bytes()
    errors = []
    if hashlib.sha256(raw).hexdigest() != CORPUS_SHA256:
        errors.append("corpus_sha256_mismatch")
    source = json.loads(Path(a.record).read_text(encoding="utf-8"))
    rows = [json.loads(s) for s in raw.decode("utf-8").splitlines()]
    if file_sha(Path(a.model) / "model.safetensors") != WEIGHT_SHA256:
        errors.append("model_weight_sha256_mismatch")
    if not torch.cuda.is_available() or torch.cuda.get_device_name(0) != source.get("gpu"):
        errors.append("gpu_identity_mismatch")
    tok = AutoTokenizer.from_pretrained(a.model, local_files_only=True, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(a.model, local_files_only=True, dtype=torch.float16,
                                                  attn_implementation="eager", low_cpu_mem_usage=True).cuda().eval()
    tokenized = [tok.encode(str(i), add_special_tokens=False) for i in range(8)]
    if tokenized != [[i] for i in ANSWER_IDS] or source.get("answer_token_ids") != ANSWER_IDS:
        errors.append("answer_tokenizer_mapping_mismatch")
    retained = source.get("records", [])
    if len(rows) != 64 or len(retained) != 1024:
        errors.append("denominator_mismatch")
    rebuilt = 0
    mismatches = 0
    seen = set()
    for ri, row in enumerate(rows):
        prefix = tok(row["prefix"], return_tensors="pt", add_special_tokens=False).input_ids.cuda()
        prefix_hash = tensor_sha(prefix)
        with torch.inference_mode():
            prefix_result = model(input_ids=prefix, use_cache=True, return_dict=True)
        frozen_cache = prefix_result.past_key_values
        for si, suffix_text in enumerate(row["suffixes"]):
            key = (ri, si)
            if key in seen:
                errors.append(f"duplicate_pair:{ri}:{si}")
            seen.add(key)
            if len(retained) <= ri * 16 + si:
                continue
            observed = retained[ri * 16 + si]
            suffix = tok(suffix_text, return_tensors="pt", add_special_tokens=False).input_ids.cuda()
            whole = tok(row["prefix"] + suffix_text, return_tensors="pt", add_special_tokens=False).input_ids.cuda()
            if not torch.equal(whole, torch.cat((prefix, suffix), dim=1)):
                errors.append(f"token_concat_mismatch:{ri}:{si}")
            with torch.inference_mode():
                full_logits = model(input_ids=whole, use_cache=False, return_dict=True).logits[0, -1].float()
            private = copy.deepcopy(frozen_cache)
            position = torch.arange(prefix.shape[1], prefix.shape[1] + suffix.shape[1], device=suffix.device)
            mask = torch.ones((1, prefix.shape[1] + suffix.shape[1]), dtype=torch.long, device=suffix.device)
            with torch.inference_mode():
                cached_logits = model(input_ids=suffix, past_key_values=private, cache_position=position,
                                      attention_mask=mask, use_cache=True, return_dict=True).logits[0, -1].float()
            fs = full_logits[ANSWER_IDS].detach().cpu().tolist()
            cs = cached_logits[ANSWER_IDS].detach().cpu().tolist()
            fw = ANSWER_IDS[int(torch.argmax(full_logits[ANSWER_IDS]).item())]
            cw = ANSWER_IDS[int(torch.argmax(cached_logits[ANSWER_IDS]).item())]
            if observed.get("bundle_id") != row["bundle_id"] or observed.get("slot") != si:
                errors.append(f"pair_identity_mismatch:{ri}:{si}")
            if observed.get("prefix_sha256") != prefix_hash:
                errors.append(f"prefix_hash_mismatch:{ri}:{si}")
            if any(abs(float(x) - float(y)) > 0.0 for x, y in zip(fs, observed.get("full", {}).get("scores", []))):
                errors.append(f"full_scores_mismatch:{ri}:{si}")
            if any(abs(float(x) - float(y)) > 0.0 for x, y in zip(cs, observed.get("cached", {}).get("scores", []))):
                errors.append(f"cached_scores_mismatch:{ri}:{si}")
            if len(fs) != 8 or len(cs) != 8:
                errors.append(f"score_width_mismatch:{ri}:{si}")
            if not all(torch.isfinite(full_logits[ANSWER_IDS]).tolist()) or not all(torch.isfinite(cached_logits[ANSWER_IDS]).tolist()):
                errors.append(f"nonfinite_reconstruction:{ri}:{si}")
            if observed.get("winner_equal") != (fw == cw):
                errors.append(f"winner_equal_flag_mismatch:{ri}:{si}")
            if fw != observed.get("full", {}).get("winner_token_id") or cw != observed.get("cached", {}).get("winner_token_id"):
                errors.append(f"winner_reconstruction_mismatch:{ri}:{si}")
            if fw != cw:
                mismatches += 1
            rebuilt += 1
    result = {"kind": "independent_raw_only_full_corpus_audit", "status": "PASS_RECONSTRUCTION" if not errors else "FAIL_AUDIT",
              "independent_implementation": True, "rows_reconstructed": rebuilt,
              "winner_mismatches": mismatches, "errors": errors,
              "scope": "synthetic fixture categorical equivalence only"}
    expected_status = ("FAIL_TYPED_DECISION_DIVERGENCE" if mismatches else "PASS_TYPED_DECISION_EQUIVALENCE_1024")
    if source.get("status") != expected_status:
        result["errors"].append("formal_status_disagrees_with_reconstruction")
        result["status"] = "FAIL_AUDIT"
    Path(a.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors and rebuilt == 1024 else 2


if __name__ == "__main__":
    raise SystemExit(main())
