# Executed commands and first outcomes

Source path: `research/local_model/typed_readout_prefix_gpu_1014_v1/`.
Issue: [#4623](https://github.com/Unjuno/agent-interface/issues/4623).

1. Container build attempt 001 failed before creating the local image because
   Transformers 5.16.1 requires `safetensors>=0.8.0`, while the source pinned
   0.7.0. See `construction/BUILD_001.json`.
2. The environment-only pin was corrected to 0.8.0. The image built from the
   immutable PyTorch CUDA base recorded in `ENVIRONMENT.json`.
3. The Docker GPU probe reported PyTorch 2.5.1+cu121, CUDA 12.1, CUDA available,
   and `NVIDIA GeForce RTX 3080 Laptop GPU`.
4. Construction command 001 loaded the pinned model in a network-disabled,
   read-only-root GPU container and stopped because an artificial leading space
   made answer `0` two tokenizer IDs. Raw structured reason:
   `construction/CONSTRUCTION_001.json`.
5. Construction command 002 used the existing bare-token spelling. It passed
   the single-token vocabulary and per-suffix-isolation checks, but failed the
   preregistered full-vocabulary FP16 logit tolerance on three excluded bundles.
   Output: `construction/CONSTRUCTION_002.json`.
6. An independent Docker audit reimplemented the full/cached calls without
   importing construction helpers and exactly reconstructed all three retained
   errors and argmax counts: `construction/AUDIT_CONSTRUCTION_002.json`.

The exact container invocation used for 002 and its independent audit was:

```powershell
docker run --rm --gpus all --network none --read-only --cpus 2 --memory 8g --pids-limit 64 --tmpfs /tmp:rw,size=256m --mount "type=bind,source=<pinned-model-snapshot>,target=/models/model,readonly" --mount "type=bind,source=<source-package>,target=/experiment,readonly" --mount "type=bind,source=<construction-output>,target=/out" --workdir /experiment --entrypoint python codex-typed-readout-4623:construction construction.py --model /models/model --corpus /experiment/corpus.jsonl --out /out/CONSTRUCTION_002.json
```

Only mount paths differ for the independent audit, which invokes
`construction_audit.py`. Formal model calls: 0. Formal latency rows: 0.
