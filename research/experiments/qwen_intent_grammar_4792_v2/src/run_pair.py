"""One-load CPU paired free-versus-state-trie decoding allocation."""
import argparse
import hashlib
import json
import os
import sys
import time
import traceback
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from candidates import TokenTrie
from protocol import bind_intent, simulate_bound

SYSTEM_PROMPT = "Return only a compact intent JSON object; do not emit scope_id or generation."
MAX_NEW_TOKENS = 48


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def stop(path, state, reason, detail=None):
    path.mkdir(parents=True, exist_ok=True)
    payload = {"schema": "qwen-intent-grammar-stop-v2", "state": state, "reason": reason,
               "detail": detail, "generation_calls": 0 if state == "STOP_PREMODEL" else None}
    (path / "STOP.json").write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))


def load_json(text):
    try:
        return json.loads(text.strip()), None
    except Exception as exc:
        return None, type(exc).__name__


def verify_frozen(root, freeze):
    errors = []
    for rel, expected in freeze["source_sha256"].items():
        path = root / rel
        if not path.is_file() or sha_file(path) != expected:
            errors.append("source:" + rel)
    for rel, expected in freeze["recovered_artifacts_sha256"].items():
        path = root / rel
        if not path.is_file() or sha_file(path) != expected:
            errors.append("artifact:" + rel)
    if errors:
        raise ValueError(",".join(errors))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    freeze_path = Path(args.freeze)
    root = freeze_path.parent
    output = Path(args.out)
    if output.exists() and any(output.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    output.mkdir(parents=True, exist_ok=True)
    try:
        freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
        verify_frozen(root, freeze)
        if os.environ.get("EXPERIMENT_IMAGE_ID") != freeze["docker_image_id"]:
            raise ValueError("docker_image_id_environment_mismatch")
        if torch.cuda.is_available():
            raise ValueError("cuda_visible_in_cpu_allocation")
        doc_bytes = Path(args.input).read_bytes()
        data = json.loads(doc_bytes.decode("utf-8"))
        if data.get("seed") != freeze["seed"] or data.get("split") != "heldout" or len(data.get("rows", [])) != freeze["row_count"]:
            raise ValueError("input_seed_split_or_count_mismatch")
        if data.get("schema") != freeze["protocol_schema"]:
            raise ValueError("input_protocol_schema_mismatch")
        torch.set_num_threads(freeze["cpu_threads"])
        torch.set_num_interop_threads(1)
        model_path = Path(args.model)
        model_hashes = {name: sha_file(model_path / name) for name in freeze["model_sha256"]}
        if model_hashes != freeze["model_sha256"]:
            raise ValueError("model_hash_mismatch")
        adapter_dir = Path(args.adapter)
        expected_adapter = {Path(name).name: value for name, value in freeze["recovered_artifacts_sha256"].items()
                            if name.startswith("recovered/") and Path(name).name != "fit.json"}
        adapter_hashes = {name: sha_file(adapter_dir / name) for name in expected_adapter}
        if adapter_hashes != expected_adapter:
            raise ValueError("adapter_hash_mismatch")
        if hashlib.sha256(doc_bytes).hexdigest() != freeze.get("input_sha256", hashlib.sha256(doc_bytes).hexdigest()):
            raise ValueError("input_hash_mismatch")

        tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
        eos_id = tokenizer.eos_token_id
        if eos_id is None:
            raise ValueError("tokenizer_eos_missing")
        prepared = []
        for item in data["rows"]:
            row = item["row"]
            candidates = item["candidates"]
            if not candidates or candidates != sorted(set(candidates)):
                raise ValueError("candidate_set_not_nonempty_sorted_unique:" + row["case_id"])
            paths = [tokenizer.encode(text, add_special_tokens=False) for text in candidates]
            for text, token_path in zip(candidates, paths):
                if tokenizer.decode(token_path, skip_special_tokens=True) != text:
                    raise ValueError("candidate_tokenizer_roundtrip:" + row["case_id"])
                if not token_path:
                    raise ValueError("empty_candidate_token_path:" + row["case_id"])
            messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": row["prompt"]}]
            ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt")
            prepared.append((item, paths, ids))

        # Exactly one CPU model load, after all source/input/artifact/tokenizer gates.
        model = AutoModelForCausalLM.from_pretrained(
            args.model, local_files_only=True, trust_remote_code=False,
            torch_dtype=torch.float32, low_cpu_mem_usage=True, attn_implementation="eager",
        ).to("cpu")
        # The predecessor config names its historical /model mount. Point PEFT
        # at the already hash-verified base snapshot in this new local container.
        peft_config = PeftModel.from_pretrained
        model = peft_config(model, args.adapter, is_trainable=False, local_files_only=True)
        model.eval()
        model.generation_config.do_sample = False
        model.generation_config.temperature = None
        model.generation_config.top_p = None
        model.generation_config.top_k = None

        header = {
            "record_type": "header", "schema": "qwen-intent-grammar-paired-raw-v2",
            "allocation": freeze["allocation"], "issue": freeze["issue"], "seed": freeze["seed"],
            "input_sha256": hashlib.sha256(doc_bytes).hexdigest(), "input_bytes": len(doc_bytes),
            "model_sha256": model_hashes, "adapter_sha256": adapter_hashes,
            "image_id": freeze["docker_image_id"], "torch": torch.__version__,
            "transformers": __import__("transformers").__version__, "peft": __import__("peft").__version__,
            "device": "cpu", "dtype": "float32", "threads": torch.get_num_threads(),
            "interop_threads": torch.get_num_interop_threads(), "attn_implementation": "eager",
            "do_sample": False, "max_new_tokens": MAX_NEW_TOKENS,
            "model_load_count": 1, "fit_count": 0,
            "source_sha256": freeze["source_sha256"],
            "prompt_sha256": hashlib.sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
        }
        raw_path = output / "RAW.jsonl"
        def generate(ids, arm, trie=None):
            input_ids = ids.to("cpu")
            mask = torch.ones_like(input_ids)
            allowed_callback = None
            if trie is not None:
                prompt_len = input_ids.shape[1]
                def allowed_callback(batch_id, full_ids):
                    prefix = full_ids[prompt_len:].tolist()
                    return trie.allowed(prefix)
            start = time.perf_counter_ns()
            with torch.inference_mode():
                result = model.generate(input_ids, attention_mask=mask, max_new_tokens=MAX_NEW_TOKENS,
                                        do_sample=False, pad_token_id=eos_id,
                                        prefix_allowed_tokens_fn=allowed_callback)
            latency = time.perf_counter_ns() - start
            token_ids = result[0, input_ids.shape[1]:].tolist()
            text = tokenizer.decode(token_ids, skip_special_tokens=True).strip()
            parsed, parse_error = load_json(text)
            return {"arm": arm, "raw_text": text, "parsed": parsed, "parse_error": parse_error,
                    "output_token_ids": token_ids, "output_tokens": len(token_ids),
                    "latency_ns": latency, "input_tokens": int(input_ids.shape[1])}

        with raw_path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(header, sort_keys=True, separators=(",", ":")) + "\n")
            stream.flush()
            for index, (item, paths, ids) in enumerate(prepared):
                row = item["row"]
                trie = TokenTrie(paths, eos_id)
                input_ids = ids[0].tolist()
                free = generate(ids, "free")
                constrained = generate(ids, "constrained", trie)
                for result in (free, constrained):
                    parsed = result["parsed"]
                    bound = bind_intent(parsed, row["state"], row["requested_generation"])
                    result["bound"] = bound
                    result["effect"] = simulate_bound(bound, row["state"])
                receipt = {
                    "record_type": "paired_row", "index": index, "row": row,
                    "candidates": item["candidates"], "candidate_token_ids": paths,
                    "candidate_prefix_receipt": trie.prefix_receipt(paths),
                    "prompt_input_ids": input_ids,
                    "free": free, "constrained": constrained,
                }
                stream.write(json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
                stream.flush()
        print(json.dumps({"state": "RUN_COMPLETE", "rows": len(prepared), "generation_calls": 2 * len(prepared),
                          "raw_sha256": sha_file(raw_path)}, sort_keys=True))
    except BaseException as exc:
        state = "STOP_PREMODEL" if "model" not in locals() else "STOP_DURING_RUN"
        stop(output, state, type(exc).__name__, str(exc)[:1000])
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
