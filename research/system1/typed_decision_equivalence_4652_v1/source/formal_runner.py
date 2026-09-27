#!/usr/bin/env python3
"""One frozen 1,024-question interleaved typed-decision allocation."""

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

from cache_mechanics import CacheHandle, cached_logits, full_logits

ANSWER_IDS = list(range(15, 23))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def token_sha(tensor):
    return hashlib.sha256(tensor.detach().cpu().numpy().tobytes()).hexdigest()


def model_manifest_matches(model_path, manifest_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    actual = {}
    for path in Path(model_path).rglob("*"):
        if path.is_file():
            actual[path.relative_to(model_path).as_posix()] = {"size": path.stat().st_size, "sha256": sha(path)}
    expected = {item["path"]: {"size": item["size"], "sha256": item["sha256"]} for item in manifest["files"]}
    return actual == expected


def append_fsync(path, value):
    with Path(path).open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def write_json(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    study, out = Path(args.study), Path(args.out)
    freeze = json.loads((study / "FREEZE.json").read_text(encoding="utf-8"))
    env_path = study / "ENVIRONMENT.json"
    if sha(env_path) != freeze["environment_sha256"]:
        raise SystemExit("STOP_FREEZE_ENVIRONMENT_HASH")
    for name, expected in freeze["source_sha256"].items():
        if sha(study / "source" / name) != expected:
            raise SystemExit("STOP_FREEZE_SOURCE_HASH:" + name)
    if sha(args.corpus) != freeze["corpus_sha256"]:
        raise SystemExit("STOP_CORPUS_HASH")
    if sha(Path(args.model) / "model.safetensors") != freeze["model_weights_sha256"]:
        raise SystemExit("STOP_MODEL_WEIGHTS_HASH")
    if sha(study / "MODEL_MANIFEST.json") != freeze["model_manifest_sha256"] or not model_manifest_matches(args.model, study / "MODEL_MANIFEST.json"):
        raise SystemExit("STOP_MODEL_MANIFEST")
    if not torch.cuda.is_available() or torch.cuda.get_device_name(0) != freeze["gpu_name"]:
        raise SystemExit("STOP_GPU_IDENTITY")
    if torch.__version__ != freeze["torch_version"] or torch.version.cuda != freeze["cuda_version"]:
        raise SystemExit("STOP_TORCH_CUDA_VERSION")
    if transformers.__version__ != freeze["transformers_version"]:
        raise SystemExit("STOP_TRANSFORMERS_VERSION")
    if out.exists():
        raise SystemExit("OUTPUT_EXISTS_NO_RETRY")
    out.mkdir(parents=True)

    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, use_fast=True)
    encoded_answers = [tokenizer.encode(str(i), add_special_tokens=False) for i in range(8)]
    if encoded_answers != [[i] for i in ANSWER_IDS]:
        raise SystemExit("STOP_ANSWER_TOKEN_IDS")
    model = AutoModelForCausalLM.from_pretrained(
        args.model, local_files_only=True, dtype=torch.float16,
        attn_implementation="eager", low_cpu_mem_usage=True,
    ).cuda().eval()
    rows = [json.loads(line) for line in Path(args.corpus).read_text(encoding="utf-8").splitlines()]
    if len(rows) != 64 or any(len(row.get("suffixes", [])) != 16 for row in rows):
        raise SystemExit("STOP_CORPUS_SHAPE")

    started = time.time_ns()
    raw_path, journal_path = out / "ROWS.jsonl", out / "PROGRESS.jsonl"
    meta = {
        "schema": "typed-decision-equivalence-run-v1",
        "allocation": freeze["allocation"], "issue": 4652,
        "corpus_sha256": freeze["corpus_sha256"], "model_weights_sha256": freeze["model_weights_sha256"],
        "model_revision": freeze["model_revision"], "answer_token_ids": ANSWER_IDS,
        "torch": torch.__version__, "cuda": torch.version.cuda,
        "transformers": transformers.__version__, "gpu": torch.cuda.get_device_name(0),
        "gpu_total_memory": torch.cuda.get_device_properties(0).total_memory,
        "pid": os.getpid(), "started_ns": started,
        "freeze_sha256": sha(study / "FREEZE.json"),
        "environment_sha256": sha(env_path),
        "source_sha256": freeze["source_sha256"],
        "model_manifest_sha256": sha(study / "MODEL_MANIFEST.json"),
        "schedule": "bundle-major/slot-major; paired full-prefill then shared-prefix-cache",
        "expected_pairs": 1024,
    }
    write_json(out / "RUN.json", meta)
    append_fsync(journal_path, {"event": "formal_start", "run_sha256": sha(out / "RUN.json"), "time_ns": started})

    paired_winners = 0
    for bundle_index, row in enumerate(rows):
        prefix_cpu = tokenizer(row["prefix"], return_tensors="pt", add_special_tokens=False).input_ids
        prefix = prefix_cpu.cuda()
        prefix_digest = token_sha(prefix)
        generation = 1000 + bundle_index
        with torch.inference_mode():
            prefetched = model(input_ids=prefix, use_cache=True, return_dict=True)
        handle = CacheHandle(prefetched.past_key_values, row["bundle_id"], generation, prefix_digest, prefix.shape[1])
        for slot, suffix_text in enumerate(row["suffixes"]):
            suffix_cpu = tokenizer(suffix_text, return_tensors="pt", add_special_tokens=False).input_ids
            combined_cpu = tokenizer(row["prefix"] + suffix_text, return_tensors="pt", add_special_tokens=False).input_ids
            if not torch.equal(combined_cpu, torch.cat((prefix_cpu, suffix_cpu), dim=1)):
                raise SystemExit(f"STOP_TOKEN_BOUNDARY:{row['bundle_id']}:{slot}")
            suffix = suffix_cpu.cuda()
            full_all = full_logits(model, prefix, suffix)
            full_scores = full_all[ANSWER_IDS].detach().cpu().tolist()
            cached_all = cached_logits(model, handle, bundle_id=row["bundle_id"], generation=generation,
                                       prefix_sha256=prefix_digest, suffix_ids=suffix)
            cached_scores = cached_all[ANSWER_IDS].detach().cpu().tolist()
            full_order = sorted(range(8), key=lambda i: (-full_scores[i], ANSWER_IDS[i]))
            cached_order = sorted(range(8), key=lambda i: (-cached_scores[i], ANSWER_IDS[i]))
            same = full_order[0] == cached_order[0]
            paired_winners += int(same)
            record = {
                "bundle_id": row["bundle_id"], "bundle_index": bundle_index, "slot": slot,
                "prefix_sha256": prefix_digest,
                "input_token_sha256": token_sha(combined_cpu),
                "suffix_token_sha256": token_sha(suffix_cpu),
                "answer_token_ids": ANSWER_IDS,
                "full_scores": full_scores, "cached_scores": cached_scores,
                "full_winner_id": ANSWER_IDS[full_order[0]],
                "cached_winner_id": ANSWER_IDS[cached_order[0]],
                "full_top2_margin": full_scores[full_order[0]] - full_scores[full_order[1]],
                "cached_top2_margin": cached_scores[cached_order[0]] - cached_scores[cached_order[1]],
                "winner_equal": same,
            }
            encoded = json.dumps(record, sort_keys=True, separators=(",", ":"))
            record["record_sha256"] = hashlib.sha256(encoded.encode()).hexdigest()
            append_fsync(raw_path, record)
            append_fsync(journal_path, {"event": "pair_complete", "bundle_index": bundle_index,
                                        "slot": slot, "record_sha256": record["record_sha256"]})
        del handle, prefetched
        torch.cuda.empty_cache()

    completed = {
        "status": "FORMAL_COMPLETE", "pairs": 1024, "winner_equal_pairs": paired_winners,
        "winner_divergences": 1024 - paired_winners,
        "rows_sha256": sha(raw_path), "journal_sha256": sha(journal_path),
        "ended_ns": time.time_ns(), "formal_invocation_count": 1,
    }
    append_fsync(journal_path, {"event": "formal_complete", **completed})
    completed["journal_sha256"] = sha(journal_path)
    write_json(out / "RESULT.json", completed)
    print(json.dumps(completed, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
