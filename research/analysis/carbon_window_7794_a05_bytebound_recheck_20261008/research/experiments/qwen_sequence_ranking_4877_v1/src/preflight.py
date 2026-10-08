import hashlib
import json
from pathlib import Path

from transformers import AutoTokenizer

from candidates import TokenTrie

MODEL = "/hf/model"
INPUT = "/study/input/input.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    raw = Path(INPUT).read_bytes()
    payload = json.loads(raw)
    tok = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    receipts = []
    total_candidates = 0
    for item in payload["rows"]:
        token_paths = [tok.encode(c, add_special_tokens=False) for c in item["candidates"]]
        trie = TokenTrie(token_paths, tok.eos_token_id)
        roundtrips = [tok.decode(ids, skip_special_tokens=True) == c
                      for c, ids in zip(item["candidates"], token_paths)]
        if not all(roundtrips) or any(not ids for ids in token_paths):
            raise SystemExit("STOP_TOKENIZER_CANDIDATE_ROUNDTRIP")
        prompt_ids = tok.encode(item["row"]["prompt"], add_special_tokens=False)
        receipts.append({"case_id": item["row"]["case_id"], "prompt_tokens": len(prompt_ids),
                         "candidate_count": len(token_paths),
                         "candidate_token_lengths": [len(x) for x in token_paths],
                         "trie_prefix_count": len(trie.prefix_receipt(token_paths)),
                         "roundtrip": True})
        total_candidates += len(token_paths)
    print(json.dumps({"input_sha256": sha(raw), "input_bytes": len(raw),
                      "tokenizer_vocab": len(tok), "eos_token_id": tok.eos_token_id,
                      "pad_token_id": tok.pad_token_id, "rows": len(receipts),
                      "total_candidates": total_candidates, "model_weights_loaded": False,
                      "receipts": receipts}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()

