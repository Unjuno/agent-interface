# #5139 synthetic class-attribution audit control

Evidence-only successor package for [Issue #5139](https://github.com/Unjuno/agent-interface/issues/5139), using the exact candidate audit source from PR #5208 head `20715c0dee3064f22e47c3d26f545697cfb2c6bf` (base `f7c7dd8caf2db49add9b85bb68a3660dcb48af70`). This does not edit #5208, its source, or any predecessor evidence.

## H / T / D / C / U

**H.** The independent raw-output auditor must derive each semantic class from the frozen intent instead of trusting the dataset's class label. Otherwise an equal-cardinality relabeling can move a miss between safety classes while all integrity checks pass.

**T.** Host Windows, CPython 3.11.9, standard library only. Synthetic sentinels formal=830513911 and support=830513912 (collision searches returned none). A balanced row mislabeled by swapping the equal-sized `yield:forbidden` and `yield:ambiguous` labels consistently in the support and held-out pools. The prescribed sampler rebuilt selected support and held-out rows; one balanced output for a true forbidden row was changed to `yield:ambiguous`.

**D.** The unchanged auditor returned `integrity_pass=true`, `errors=[]`. It reported balanced `yield:ambiguous` as 0/8 and `yield:forbidden` as 8/8, although the intentionally wrong output came from a ground-truth forbidden row. It did not recompute row class from the true intent. Exact mutated dataset, original dataset, three raw arm records and audit JSON are in the compressed bundle.

**C.** One retained host-only corruption-boundary diagnostic against the frozen PR head; 64 held-out rows per arm. No model, tokenizer, GPU, CUDA, Docker, OrbStack, GUI, or formal allocation was used. The first wrapper attempt's newline-encoding STOP is also preserved in the bundle and is excluded from the result.

**U.** This is an auditor-integrity defect in the synthetic #5139 package, not a Qwen/LoRA quality result or a live-action safety result. Keep #5208 preparatory until an independent `class == class_from(intent)` check for both support and held-out pools is added and this mutation is rejected. No prior result is changed.

## Restore and verify raw bundle

Run `python restore_bundle.py` in this directory. It concatenates the ordered Base64 parts, verifies archive length and SHA-256, checks ZIP members, then extracts to `restored/`. Expected archive: 219,085 bytes, SHA-256 `3a853f78c501e6c2ac1f05dcdfe0c486ca979b49a126bda1328dfd4f0dc16445`.

Selected retained file SHA-256:

- Original generated dataset: `4a9c4bb5d8515a71b46886d3fe4f7c49e9f99cd31e92dc2550b4a9571a94edad`
- Mutated dataset: `8058606289bbeb9cf31b7e5fb8082690dbc6c6bfab2e2a35e7d9be1e44ee776c`
- Raw outputs: `9228cca1152dcd352bde588370e23a9a01fa4bcea100fbb9b617b85935edac24`
- Audit output: `b37ff3818fe0a5b01a4237e393363f296611dd5f40c9953aa642a97d9dc9466e`

GitHub blob IDs and source SHA-256s for all frozen source files are retained in `restored/SOURCE_MANIFEST.json`.