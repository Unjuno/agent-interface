# Typed decision equivalence — Issue #4652

This folder is an additive, GPU-local successor to #4639. Read `PLAN.md` and `FREEZE.json` before execution. `MODEL_MANIFEST.json` is the byte-identical predecessor manifest; `UPSTREAM_ENVIRONMENT_4623.json` preserves the predecessor's explicit construction-only status. No shared reader or runtime path changes here.

## Reproduction outline

1. Use only the locally cached image ID and locally cached model revision in `ENVIRONMENT.json`; do not pull, download, install, or use network access.
2. Recreate `inputs/corpus.jsonl` with the frozen `source/make_corpus.py` implementation, then require SHA-256 `c70d4ba3d06dec161fdc8d3f5e5312fbe3ff0af1c1a36cdcb0dc0e290efe27fd` (64 bundles, 270,228 bytes).
3. Run `source/construction.py` with CUDA enabled, source/model/corpus read-only, output on a dedicated writable mount. Any nonzero status is a terminal STOP; do not start formal.
4. Run one supervised invocation of `source/supervise.py` for the formal phase, with a 30-minute outer timeout and the exact model/corpus/image. A timeout consumes the sole allocation; do not retry.
5. Run `source/independent_audit.py` in a separate, network-disabled CUDA container. It independently loads the model, recomputes every full-prefill and cached vector, and checks retained raw evidence without importing runner/cache-helper code.

The retained vectors/margins are mechanism evidence only. No score tolerance, latency threshold, semantic score, fine-tuning, or authorization claim is added.
