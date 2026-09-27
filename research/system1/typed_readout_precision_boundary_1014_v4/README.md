# Issue #4912 — selected-code precision construction

This one-shot construction-only allocation compares full-prefill and shared-prefix KV-cache logits for the eight answer codes consumed by the typed readout. It uses three previously excluded corpus rows under FP16, BF16 and FP32. It performs no text generation, training, formal timing block, semantic scoring, GUI action or authority change.

## Frozen identity

- Main parent: `f3dc0f18b0aaef241a6cd34124b68439c3434b05`.
- Exact corpus: 270,292 bytes, SHA-256 `85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c`. Preserved from the pre-existing local checkout and matches the original source manifest. Main currently contains a distinct 270,228-byte corpus; it is not used.
- Model: `Qwen/Qwen2.5-0.5B-Instruct`, revision `7ae557604adf67be50417f59c2c2f167def9a775`; every asset is checked against the original MODEL_MANIFEST before loading.
- CUDA image: `sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261` (linux/amd64), PyTorch 2.5.1+cu121, Transformers 5.16.1, safetensors 0.8.0.
- Hardware: NVIDIA GeForce RTX 3080 Laptop GPU, 16 GiB.

## One-shot construction command

The command and absolute paths are recorded verbatim in `FREEZE.json`. Source, corpus and model are mounted read-only; the only writable mount is a new empty output directory. Network is disabled. The existing Ollama container is left untouched.

```powershell
docker run --rm --pull=never --network none --read-only --gpus all --cpus=2 --memory=8g --pids-limit=64 --tmpfs /tmp:rw,noexec,nosuid,size=512m -v "<SOURCE>:/src:ro" -v "<MODEL>:/models/model:ro" -v "<FRESH_OUTPUT>:/out:rw" -e HF_HOME=/tmp/hf -e TRANSFORMERS_OFFLINE=1 --entrypoint python sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261 -B /src/run_construction.py --model /models/model --corpus /src/corpus.jsonl --out /out
```

## Frozen construction rows and decisions

Rows are B00/B17/B63 × suffix slots 0/7/15 (nine pairs). The same cache helpers, tokenizer, prefixes, suffixes, and eight token IDs `[15,16,17,18,19,20,21,22]` are used across precisions. PASS requires at least one of BF16/FP32 to meet both max absolute and max relative error <=0.002 on all nine pairs, unchanged winners on every pair, suffix isolation, verified hashes, and a zero-error raw-only audit with all five corruption controls rejected. No formal 64×16 timing schedule runs here.

Three raw-audit tests passed in the pinned CPU container before the freeze; see `FREEZE.json` for the exact invocation, image, hashes and test result.

