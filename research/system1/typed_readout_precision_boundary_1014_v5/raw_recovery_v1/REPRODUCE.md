# Reproduce the raw-only audit

This verifies the retained row-level result without loading or calling the model. The audit checks the corpus and locally cached model assets by SHA-256, then validates raw logits, derived tolerances, winners, cache-isolation fields, and five corruption controls.

Requirements: Python 3.11+; standard library only. Obtain the exact Qwen snapshot `Qwen/Qwen2.5-0.5B-Instruct` revision `7ae557604adf67be50417f59c2c2f167def9a775` in a local cache (the auditor reads its files only to hash them; it does not load weights).

From this directory, set `MODEL_DIR` to that snapshot directory and run:

```sh
python audit_raw.py --result raw_result.json --corpus corpus.jsonl --model "$MODEL_DIR" --out audit_recomputed.json
python -m unittest -v test_audit_core.py
```

Expected: `AUDIT_PASS_RAW_ONLY`, 27 rows, zero errors, and 5/5 corruption controls rejected. The checked-in `audit.json` is the original receipt; `audit_recomputed.json` is a fresh output and should not overwrite it.

The corpus is byte-pinned here. The frozen model snapshot is identified by revision and per-file hashes in `audit_raw.py`; model weights are intentionally not copied into this repository. No GPU, Docker, inference, generation, training, optimizer step, or retry is required for this audit.
