#!/usr/bin/env python3
"""Independent GPU recomputation; imports no formal runner/cache helper."""

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

ALLOWED = [15, 16, 17, 18, 19, 20, 21, 22]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def token_digest(tensor):
    return hashlib.sha256(tensor.detach().cpu().numpy().tobytes()).hexdigest()


def verify_model_inventory(model_path, manifest_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    observed = {}
    for path in Path(model_path).rglob("*"):
        if path.is_file():
            digest = sha(path)
            observed[path.relative_to(model_path).as_posix()] = {"size": path.stat().st_size, "sha256": digest}
    expected = {item["path"]: {"size": item["size"], "sha256": item["sha256"]} for item in manifest["files"]}
    return observed == expected


def same_vector(left, right, tolerance=1e-4):
    return len(left) == len(right) == 8 and all(
        math.isfinite(float(a)) and math.isfinite(float(b)) and abs(float(a) - float(b)) <= tolerance
        for a, b in zip(left, right)
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--run", required=True)
    ap.add_argument("--supervisor", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    study = Path(args.study)
    freeze = json.loads((study / "FREEZE.json").read_text(encoding="utf-8"))
    run = json.loads(Path(args.run).read_text(encoding="utf-8"))
    supervisor = json.loads(Path(args.supervisor).read_text(encoding="utf-8"))
    errors = []
    if freeze.get("environment_sha256") != sha(study / "ENVIRONMENT.json"):
        errors.append("frozen_environment_digest")
    if sha(args.corpus) != freeze["corpus_sha256"]:
        errors.append("corpus_digest")
    if sha(Path(args.model) / "model.safetensors") != freeze["model_weights_sha256"]:
        errors.append("model_weight_digest")
    if sha(study / "MODEL_MANIFEST.json") != freeze["model_manifest_sha256"] or not verify_model_inventory(args.model, study / "MODEL_MANIFEST.json"):
        errors.append("model_manifest_inventory")
    if not torch.cuda.is_available() or torch.cuda.get_device_name(0) != freeze["gpu_name"]:
        errors.append("gpu_identity")
    if torch.__version__ != freeze["torch_version"] or torch.version.cuda != freeze["cuda_version"]:
        errors.append("torch_cuda_identity")
    if transformers.__version__ != freeze["transformers_version"]:
        errors.append("transformers_identity")
    if run.get("freeze_sha256") != sha(study / "FREEZE.json"):
        errors.append("run_freeze_digest")
    if run.get("environment_sha256") != sha(study / "ENVIRONMENT.json"):
        errors.append("run_environment_digest")
    if run.get("source_sha256") != freeze["source_sha256"]:
        errors.append("run_source_manifest")
    if run.get("model_manifest_sha256") != sha(study / "MODEL_MANIFEST.json"):
        errors.append("run_model_manifest_digest")
    if run.get("corpus_sha256") != sha(args.corpus) or run.get("model_weights_sha256") != sha(Path(args.model) / "model.safetensors"):
        errors.append("run_input_identity")
    if supervisor.get("status") != "FORMAL_COMPLETE" or supervisor.get("return_code") != 0 or supervisor.get("retained_rows") != 1024:
        errors.append("supervisor_completion")
    if supervisor.get("rows_sha256") != sha(args.raw):
        errors.append("supervisor_raw_digest")
    for name, expected in freeze["source_sha256"].items():
        if sha(study / "source" / name) != expected:
            errors.append("source_digest:" + name)

    corpus = [json.loads(line) for line in Path(args.corpus).read_text(encoding="utf-8").splitlines()]
    records = [json.loads(line) for line in Path(args.raw).read_text(encoding="utf-8").splitlines()]
    if len(corpus) != 64 or len(records) != 1024:
        errors.append("formal_row_count")
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, use_fast=True)
    answer_tokens = [tokenizer.encode(str(i), add_special_tokens=False) for i in range(8)]
    if answer_tokens != [[i] for i in ALLOWED]:
        errors.append("answer_token_ids")
    model = AutoModelForCausalLM.from_pretrained(
        args.model, local_files_only=True, dtype=torch.float16,
        attn_implementation="eager", low_cpu_mem_usage=True,
    ).cuda().eval()

    matches = 0
    winner_equal = 0
    maximum_vector_error = 0.0
    for bundle_index, row in enumerate(corpus):
        selected = records[bundle_index * 16:(bundle_index + 1) * 16]
        prefix_cpu = tokenizer(row["prefix"], return_tensors="pt", add_special_tokens=False).input_ids
        prefix = prefix_cpu.cuda()
        prefix_hash = token_digest(prefix)
        if not selected:
            continue
        with torch.inference_mode():
            prefix_output = model(input_ids=prefix, use_cache=True, return_dict=True)
        original_cache = prefix_output.past_key_values
        generation = 1000 + bundle_index
        for slot, (saved, suffix_text) in enumerate(zip(selected, row["suffixes"])):
            if saved.get("bundle_index") != bundle_index or saved.get("bundle_id") != row["bundle_id"] or saved.get("slot") != slot:
                errors.append(f"schedule:{bundle_index}:{slot}")
            try:
                unsigned = {k: v for k, v in saved.items() if k != "record_sha256"}
                expected_digest = hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                if expected_digest != saved.get("record_sha256"):
                    errors.append(f"record_digest:{bundle_index}:{slot}")
            except Exception:
                errors.append(f"record_encoding:{bundle_index}:{slot}")

            suffix_cpu = tokenizer(suffix_text, return_tensors="pt", add_special_tokens=False).input_ids
            combined_cpu = tokenizer(row["prefix"] + suffix_text, return_tensors="pt", add_special_tokens=False).input_ids
            if not torch.equal(combined_cpu, torch.cat((prefix_cpu, suffix_cpu), dim=1)):
                errors.append(f"token_boundary:{bundle_index}:{slot}")
            if saved.get("prefix_sha256") != prefix_hash:
                errors.append(f"prefix_identity:{bundle_index}:{slot}")
            if saved.get("input_token_sha256") != token_digest(combined_cpu) or saved.get("suffix_token_sha256") != token_digest(suffix_cpu):
                errors.append(f"token_digest:{bundle_index}:{slot}")
            suffix = suffix_cpu.cuda()

            # Full-prefill path is evaluated from concatenated tokens, independently.
            with torch.inference_mode():
                full_output = model(input_ids=combined_cpu.cuda(), use_cache=False, return_dict=True)
                full_vector = full_output.logits[0, -1, ALLOWED].float().cpu().tolist()

            # Rebuild the per-question cache copy independently; no runner helpers are imported.
            private = copy.deepcopy(original_cache)
            positions = torch.arange(prefix.shape[1], prefix.shape[1] + suffix.shape[1], device="cuda")
            mask = torch.ones((1, prefix.shape[1] + suffix.shape[1]), dtype=torch.long, device="cuda")
            with torch.inference_mode():
                cached_output = model(input_ids=suffix, past_key_values=private,
                                      cache_position=positions, attention_mask=mask,
                                      use_cache=True, return_dict=True)
                cached_vector = cached_output.logits[0, -1, ALLOWED].float().cpu().tolist()

            for label, actual, stored in (("full", full_vector, saved.get("full_scores", [])),
                                          ("cached", cached_vector, saved.get("cached_scores", []))):
                if not same_vector(actual, stored):
                    errors.append(f"{label}_vector:{bundle_index}:{slot}")
                if len(actual) == len(stored) == 8:
                    maximum_vector_error = max(maximum_vector_error, *(abs(float(a) - float(b)) for a, b in zip(actual, stored)))
            full_order = sorted(range(8), key=lambda i: (-full_vector[i], ALLOWED[i]))
            cached_order = sorted(range(8), key=lambda i: (-cached_vector[i], ALLOWED[i]))
            full_winner, cached_winner = ALLOWED[full_order[0]], ALLOWED[cached_order[0]]
            equal = full_winner == cached_winner
            winner_equal += int(equal)
            margin_full = full_vector[full_order[0]] - full_vector[full_order[1]]
            margin_cached = cached_vector[cached_order[0]] - cached_vector[cached_order[1]]
            if (saved.get("full_winner_id") != full_winner or saved.get("cached_winner_id") != cached_winner
                    or saved.get("winner_equal") is not equal or saved.get("answer_token_ids") != ALLOWED
                    or abs(float(saved.get("full_top2_margin", float("nan"))) - margin_full) > 1e-4
                    or abs(float(saved.get("cached_top2_margin", float("nan"))) - margin_cached) > 1e-4):
                errors.append(f"decision_or_margin:{bundle_index}:{slot}")
            matches += 1
        del original_cache, prefix_output
        torch.cuda.empty_cache()

    if matches != 1024:
        errors.append("recomputed_count")
    decision = "PASS_TYPED_DECISION_EQUIVALENCE_1024" if not errors and winner_equal == 1024 else (
        "FAIL_TYPED_DECISION_DIVERGENCE" if not errors else "FAIL_INDEPENDENT_AUDIT")
    result = {
        "schema": "typed-decision-equivalence-independent-audit-v1",
        "status": decision, "errors": errors, "recomputed_pairs": matches,
        "winner_equal_pairs": winner_equal, "winner_divergences": matches - winner_equal,
        "maximum_stored_vector_abs_error": maximum_vector_error,
        "independent_model_recomputation": True,
        "model_weights_sha256": sha(Path(args.model) / "model.safetensors"),
        "corpus_sha256": sha(args.corpus),
        "raw_sha256": sha(args.raw),
        "run_sha256": sha(args.run),
        "supervisor_sha256": sha(args.supervisor),
    }
    raw = json.dumps(result, sort_keys=True, indent=2) + "\n"
    Path(args.out).write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if not errors and winner_equal == 1024 else 2


if __name__ == "__main__":
    raise SystemExit(main())
