# Issue #4912 — selected-code precision construction

This is a one-shot, construction-only successor to #4875's pre-load `STOP_OUTPUT_NOT_EMPTY`. It preserves the exact frozen comparison: full-prefill versus shared-prefix KV-cache logits for answer IDs 15–22, using FP16/BF16/FP32 on excluded rows B00/B17/B63 × suffix slots 0/7/15. It performs no generation, training, semantic scoring, GUI action or formal timing schedule.

## Frozen identity

- Main parent: `f3dc0f18b0aaef241a6cd34124b68439c3434b05`.
- Corpus: 270,292 bytes, SHA-256 `85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c`.
- Model: Qwen/Qwen2.5-0.5B-Instruct revision `7ae557604adf67be50417f59c2c2f167def9a775`; weights SHA-256 `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.
- Image: `sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261`, linux/amd64, PyTorch 2.5.1+cu121, Transformers 5.16.1, safetensors 0.8.0.

## Output and log isolation

Before the sole invocation, create a new empty host directory mounted writable at `/out`. Docker stdout, stderr and the invocation receipt must be stored in a separate sibling log directory that is not mounted into the container. The source/corpus and model are read-only mounts; network is disabled. Audit output is a separate writable directory, and the auditor mounts construction output read-only. Do not stop or alter the resident Ollama/X11 containers. Immediately before execution, verify RTX 3080 utilization and check for active concurrent GPU allocations. If another allocation is running, do not launch this one.

PASS requires one candidate precision (BF16 or FP32) to meet both absolute and relative <=0.002 bounds for all nine pairs, unchanged winners, cache isolation, controls, and zero independent raw-audit errors. A failure or gate mismatch is retained without retry. Scope is only these three excluded synthetic bundles, one model snapshot, one RTX 3080 and one image; no speedup, semantic accuracy, GUI, authority, deployment or product claim follows.