import hashlib
import json
import os
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


OUT = Path("/out")
MODEL = os.environ["MODEL_DIR"]
MAX_NEW = 48

# Fixed before execution; every row receives precisely this same candidate set.
CANDIDATES = [
    '{"op":"set","field":"display_name","value":"probe-name"}',
    '{"op":"set","field":"timezone","value":"Asia/Tokyo"}',
    '{"op":"set","field":"digest_frequency","value":"weekly"}',
    '{"op":"set","field":"sharing_visibility","value":"private"}',
    '{"op":"save"}',
    '{"op":"toggle","target":"toggle_email_reminders"}',
    '{"op":"yield","reason":"forbidden"}',
    '{"op":"yield","reason":"ambiguous"}',
    '{"op":"yield","reason":"stale_scope"}',
    '{"op":"yield","reason":"missing_evidence"}',
    '{"op":"yield","reason":"unsupported"}',
    '{"op":"no_action","reason":"already_satisfied"}',
    '{"op":"no_action","reason":"not_requested"}',
]
PROMPT_MESSAGES = [
    {"role": "system", "content": "Choose the compact intent for this settings request. Reply with exactly one JSON object."},
    {"role": "user", "content": "Change the timezone from Europe/Paris to Asia/Tokyo and save the setting."},
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    torch.set_num_threads(2)
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, local_files_only=True, torch_dtype=torch.float32,
        low_cpu_mem_usage=True, attn_implementation="eager",
    ).to("cpu").eval()
    eos = tokenizer.eos_token_id
    if eos is None:
        raise RuntimeError("tokenizer_has_no_eos")

    encoded = [tokenizer.encode(s, add_special_tokens=False) for s in CANDIDATES]
    if any(not ids for ids in encoded) or len({tuple(x) for x in encoded}) != len(encoded):
        raise RuntimeError("candidate_token_collision_or_empty")
    if any(tokenizer.decode(ids, skip_special_tokens=False,
                            clean_up_tokenization_spaces=False) != s
           for ids, s in zip(encoded, CANDIDATES)):
        raise RuntimeError("candidate_tokenizer_roundtrip_failed")

    trie = {}
    prefixes = {(): set()}
    terminals = set()
    for seq in encoded:
        node = trie
        prefix = []
        for token in seq:
            node = node.setdefault(token, {})
            prefix.append(token)
            prefixes.setdefault(tuple(prefix[:-1]), set()).add(token)
        terminals.add(tuple(seq))
    expected = {p: set(children) for p, children in prefixes.items()}
    for terminal in terminals:
        expected[terminal] = {eos}

    def allowed(prefix):
        key = tuple(prefix)
        if key in terminals:
            return [eos]
        if key not in prefixes:
            return []
        return sorted(prefixes[key])

    # Exhaustively traverse every proper prefix and terminal, including invalid mutations.
    prefix_checks = 0
    for seq in encoded:
        for n in range(len(seq)):
            p = tuple(seq[:n])
            assert set(allowed(p)) == expected[p]
            prefix_checks += 1
        p = tuple(seq)
        assert allowed(p) == [eos]
        assert allowed(p + (eos,)) == []
        prefix_checks += 2
    assert len(CANDIDATES) == len(encoded)

    ids = tokenizer.apply_chat_template(PROMPT_MESSAGES, tokenize=True,
                                        add_generation_prompt=True,
                                        return_tensors="pt").to("cpu")
    prompt_len = ids.shape[1]
    prompt_hash = digest(ids[0].tolist().__repr__().encode())

    def constraint(batch_id, input_ids):
        suffix = input_ids[prompt_len:].tolist()
        return allowed(suffix)

    records = {"candidate_hash": digest("\n".join(CANDIDATES).encode()),
               "candidate_count": len(CANDIDATES), "prefix_checks": prefix_checks,
               "prompt_token_hash": prompt_hash, "arms": {}}
    for name, kwargs in (("free", {}), ("trie", {"prefix_allowed_tokens_fn": constraint})):
        start = time.perf_counter_ns()
        with torch.inference_mode():
            output = model.generate(ids, do_sample=False, max_new_tokens=MAX_NEW,
                                    pad_token_id=tokenizer.pad_token_id or eos,
                                    eos_token_id=eos, **kwargs)
        elapsed = time.perf_counter_ns() - start
        generated = output[0, prompt_len:].tolist()
        raw = tokenizer.decode(generated, skip_special_tokens=True,
                               clean_up_tokenization_spaces=False)
        try:
            parsed = json.loads(raw)
            parse_error = None
        except Exception as exc:
            parsed = None
            parse_error = type(exc).__name__
        records["arms"][name] = {
            "raw_text": raw, "token_ids": generated,
            "ended_with_eos": bool(output[0, -1].item() == eos),
            "candidate_member": raw in CANDIDATES,
            "parsed": parsed, "parse_error": parse_error,
            "wall_ns": elapsed,
        }
    records["construction_pass"] = (
        records["arms"]["trie"]["candidate_member"]
        and records["arms"]["trie"]["parse_error"] is None
        and isinstance(records["arms"]["trie"]["parsed"], dict)
        and records["arms"]["trie"]["ended_with_eos"]
        and prefix_checks >= len(CANDIDATES)
    )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "construction-result.json").write_text(
        json.dumps(records, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    print(json.dumps({"construction_pass": records["construction_pass"],
                      "candidate_count": len(CANDIDATES),
                      "prefix_checks": prefix_checks,
                      "trie_candidate_member": records["arms"]["trie"]["candidate_member"],
                      "trie_parse_error": records["arms"]["trie"]["parse_error"]}))


if __name__ == "__main__":
    main()

