# Formal result — Issue #4829

**Disposition: `FAIL_ONLINE_CORRECTION_FORGETTING`.** The independent audit passed. On two of three fresh seeds, the shared candidate reached >=0.90 on opposing B while candidate-A retention had already fallen below 0.90; the untouched A base stayed at 1.00. The third seed did not acquire B and ended between the two mappings. Retain the across-seed variance rather than collapsing it into the construction-only result.

| Seed | Untouched base A | Candidate A step 0 → 32 | Candidate B step 0 → 32 | First D crossing | Update-only p95 |
|---:|---:|---:|---:|---:|---:|
| 66117 | 256/256 (1.000) | 256/256 → 104/256 (0.406) | 0/256 → 147/256 (0.574) | none | 0.822 ms |
| 66229 | 256/256 (1.000) | 256/256 → 0/256 (0.000) | 0/256 → 256/256 (1.000) | step 28: A 0/256, B 253/256 | 0.295 ms |
| 66341 | 256/256 (1.000) | 256/256 → 0/256 (0.000) | 0/256 → 256/256 (1.000) | step 31: A 0/256, B 256/256 | 0.291 ms |

The untouched base preserved A exactly in all three seeds. Initial candidate output exactly equaled base. All 99 arrival curves (accuracy and cross-entropy), final row logits, base outputs, and immutable-base values were independently recomputed with zero errors. Nine scope/epoch route controls behaved as frozen; independent audit rejected corrupted metric and logit controls.

## Protocol / provenance

- One formal trainer invocation for seeds 66117/66229/66341; one independent auditor invocation in a second container; no retries or tuning.
- Docker 29.8.0, `needle-pilot05:local`, image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, Linux/amd64, PyTorch 2.5.1+cpu, 1 thread, network none, read-only source/root, 1 CPU/2 GiB/64 PIDs. Dedicated Docker volume `unjuno-needle-online-correction-frontier-3441-v3-formal` retained.
- Raw `raw.json`: 627,988 bytes, SHA-256 `3e6bf26c8dc1c4cfe46804c1bd4db89af50acf23238e302c01bba9518b973b07`; the SHA was independently computed inside the retained Docker volume and on its byte-identical host export.
- Audit stdout is retained as `AUDIT.json`: `AUDIT_PASS`, 3 runs, 99 curve points, 9 controls, zero errors, corruption and logit-corruption controls rejected.
- Formal trainer source SHA-256 `e4b108a4630332af815a7c992e6259e7cc5cafdea396e5b0d6b31854d84a2877`; auditor `ac8977c41840e5f71c12619633c17d86fd3b228b7e92ec6a843442d24967ed19`; test `4470886f1aa3347a0c8268fe1b1a43df075585c20561af6e33cbc0c83a8e4cc6`. See `FREEZE.json`.
- Raw is retained as ordered `raw-parts/part-NNN-of-032.jsonpart`; concatenate bytes in numeric order with no separators to reconstruct exact `raw.json` and verify the SHA-256 above.

## Scope

This is a deliberately conflicting synthetic two-label task. It shows a plasticity/retention frontier for this one tiny CPU adapter recipe; it does not imply natural Astra feedback quality, useful GUI behavior, successful routing to the untouched base, production online learning, or general catastrophic-forgetting rates. Update-only p95 is optimizer-step time, not inference latency or deadline evidence. No action authority, live effects, provider, GUI, or user data were involved. NumPy was absent from the pinned image and emitted a nonfatal PyTorch warning; the study/auditor use pure PyTorch and JSON.

