import argparse
import hashlib
import json
import time
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, LogitsProcessor, LogitsProcessorList

from candidates import TokenTrie
from protocol import bind_intent, simulate_bound

MODEL = "/hf/model"
ADAPTER = "/study/assets"
SYS = "Return only a compact intent JSON object; do not emit scope_id or generation."


class TrieLogits(LogitsProcessor):
    def __init__(self, trie):
        self.trie = trie

    def __call__(self, input_ids, scores):
        prefix = input_ids[0, self.prompt_len:].tolist()
        if prefix and prefix[-1] == self.trie.eos_token_id:
            return scores
        allowed = self.trie.allowed(prefix)
        if not allowed:
            raise RuntimeError("trie_has_no_continuation")
        mask = torch.full_like(scores, -torch.inf)
        mask[:, allowed] = scores[:, allowed]
        return mask


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def format_prompt(tokenizer, prompt):
    return tokenizer.apply_chat_template([{"role": "system", "content": SYS},
                                          {"role": "user", "content": prompt}],
                                         tokenize=False, add_generation_prompt=True)


def score_path(model, prompt_ids, candidate_ids, eos, device):
    ids = prompt_ids + candidate_ids + [eos]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    with torch.inference_mode():
        logits = model(input_ids=input_ids, use_cache=False).logits[0]
        start = len(prompt_ids) - 1
        positions = logits[start:start + len(candidate_ids) + 1].float()
        targets = torch.tensor(candidate_ids + [eos], dtype=torch.long, device=device)
        selected = torch.log_softmax(positions, dim=-1).gather(1, targets[:, None]).squeeze(1)
    return [float(x) for x in selected.cpu().tolist()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    raw = Path(args.input).read_bytes()
    data = json.loads(raw)
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    tok = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    base = AutoModelForCausalLM.from_pretrained(MODEL, local_files_only=True, torch_dtype=torch.float32,
                                                attn_implementation="eager", device_map={"": "cpu"})
    model = PeftModel.from_pretrained(base, ADAPTER, is_trainable=False, local_files_only=True).eval()
    device = torch.device("cpu")
    results, call_count = [], 0
    for item in data["rows"]:
        row, candidates = item["row"], item["candidates"]
        prompt = format_prompt(tok, row["prompt"])
        prompt_ids = tok.encode(prompt, add_special_tokens=False)
        candidate_ids = [tok.encode(c, add_special_tokens=False) for c in candidates]
        prompt_tensor = torch.tensor([prompt_ids], dtype=torch.long, device=device)
        start = time.perf_counter()
        with torch.inference_mode():
            free_ids = model.generate(prompt_tensor, do_sample=False, max_new_tokens=48,
                                      pad_token_id=tok.pad_token_id, eos_token_id=tok.eos_token_id)[0, len(prompt_ids):].tolist()
        free_s = time.perf_counter() - start
        call_count += 1
        trie = TokenTrie(candidate_ids, tok.eos_token_id)
        proc = TrieLogits(trie)
        proc.prompt_len = len(prompt_ids)
        start = time.perf_counter()
        with torch.inference_mode():
            trie_ids = model.generate(prompt_tensor, do_sample=False, max_new_tokens=48,
                                      pad_token_id=tok.pad_token_id, eos_token_id=tok.eos_token_id,
                                      logits_processor=LogitsProcessorList([proc]))[0, len(prompt_ids):].tolist()
        trie_s = time.perf_counter() - start
        call_count += 1
        scored = []
        start = time.perf_counter()
        for cand, ids in zip(candidates, candidate_ids):
            token_lp = score_path(model, prompt_ids, ids, tok.eos_token_id, device)
            scored.append({"candidate": cand, "token_ids": ids, "token_logprobs": token_lp,
                           "sum_logprob": sum(token_lp)})
        rank_s = time.perf_counter() - start
        scores = {x["candidate"]: x["sum_logprob"] for x in scored}
        ranked = sorted(candidates, key=lambda c: (-scores[c], c))
        free_text = tok.decode(free_ids, skip_special_tokens=True)
        trie_text = tok.decode(trie_ids, skip_special_tokens=True)
        outputs = []
        for arm, raw_text in (("free", free_text), ("trie", trie_text), ("ranked", ranked[0])):
            try:
                obj = json.loads(raw_text)
            except Exception:
                obj = None
            bound = bind_intent(obj, row["state"], row["requested_generation"])
            effect = simulate_bound(bound, row["state"])
            outputs.append({"arm": arm, "text": raw_text, "bound": bound, "effect": effect,
                            "exact": obj is not None and canonical(obj) == row["target"]})
        results.append({"case_id": row["case_id"], "prompt": prompt, "prompt_token_ids": prompt_ids,
                        "candidate_scores": scored, "ranked_candidates": ranked,
                        "free_token_ids": free_ids, "trie_token_ids": trie_ids,
                        "outputs": outputs, "timing_seconds": {"free": free_s, "trie": trie_s,
                                                                  "ranked": rank_s}})
    out = {"schema": "qwen-sequence-ranking-raw-v1", "input_sha256": sha(raw),
           "rows": results, "generation_calls": call_count,
           "candidate_forward_scoring_passes": sum(len(x["candidate_scores"]) for x in results),
           "model_training": False}
    encoded = json.dumps(out, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"
    Path(args.output).write_bytes(encoded)
    print(json.dumps({"rows": len(results), "bytes": len(encoded), "sha256": sha(encoded),
                      "generation_calls": call_count, "scoring_passes": out["candidate_forward_scoring_passes"]}, sort_keys=True))


if __name__ == "__main__":
    main()

