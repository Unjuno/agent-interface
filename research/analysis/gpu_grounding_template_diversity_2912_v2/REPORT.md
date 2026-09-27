# Issue #4561 — fixed-pool template-diversity grounder

**Disposition: `HOLD_OR_FAIL_FROZEN_GATES_NOT_MET`.** The one pre-registered formal allocation completed, and the independent raw-results audit is integrity-clean (`errors=[]`). The template-diversity hypothesis did **not** meet the frozen success gates. This is a bounded negative/underpowered synthetic result, not a general claim that broader training is harmful.

## H / T / D / C / U

- **H:** at matched update and sampled-example budgets, training on eight synthetic form-geometry families rather than two improves exact field+submit localization on four unseen families.
- **T:** frozen local raster corpus, 8×10 two-channel coordinate heatmaps, three fixed seeds, narrow 2-family versus broad 8-family training, 400 Adam updates per model, batch 16. Exact PNG/pixel/label hashes were committed before any training.
- **D:** one allocation only; scoped PASS required broad accuracy ≥0.90 on every held-out family, ≥0.10 aggregate absolute improvement over narrow, zero accepted wrong coordinates, and zero audit errors. Failed gates are retained without retry or tuning.
- **C:** the only changed factor was training-family breadth. Same architecture, initial state per seed, sample count, optimizer/update count, image preprocessing, four held-out families/16 held-out images, acceptance threshold 0.75 and strict schema validator. Synthetic data only; no pretrained weights, network, GUI or runtime use.
- **U:** synthetic family coverage, architecture capacity, 400-step budget and confidence calibration limit interpretation. The study cannot establish behavior on real applications or arbitrary interfaces.

## Formal result

The pinned local Docker image trained six models (2,400 optimizer steps total) and evaluated 96 seed×arm×held-out-image cases. The independent exact-source auditor reports:

| Metric | Narrow: 2 families | Broad: 8 families |
|---|---:|---:|
| Exact field+submit pairs | 12/48 (25.0%) | 10/48 (20.8%) |
| Accepted candidate coverage at confidence ≥0.75 | 0/48 (0%) | 0/48 (0%) |
| Accepted wrong coordinates | 0 | 0 |

Broad held-out exact-pair accuracy by entire source family: family-09 **3/12 (25.0%)**; family-10 **7/12 (58.3%)**; family-11 **0/12**; family-12 **0/12**. Aggregate broad-minus-narrow difference: **−2/48 = −0.0416667 (−4.17 percentage points)**. The per-family ≥90% requirement and ≥10-point improvement requirement both fail. The zero accepted-wrong gate passes only because all 96 predictions yielded; this is zero useful candidate coverage, not safe success.

All six models began at cross-entropy near 4.38. End-of-run losses ranged from 0.288–0.976 (narrow) and 0.492–1.391 (broad), with substantial seed variation. Broad training did not yield held-out gains in this allocation. Each model took approximately 1.30–1.66 seconds of measured training time; maximum recorded allocated CUDA memory was 97,356,288 bytes (~92.8 MiB). These local synthetic metrics are not production performance claims.

## Integrity and provenance

- Pre-formal source and corpus freeze: [`FREEZE.json`](FREEZE.json), source commit `26326602008ba2da5c5604844829a278baef3065`, freeze commit `a6975b6fcea1d3ff7795f8d27b5182c83cfa79ff`.
- Formal raw output: [`results/formal01/results.json`](results/formal01/results.json), SHA-256 `5ff992341e4f28357a4b0bdd1166d7c2a33e1aadab80fd8b576500c3a3b9fe97`.
- Independent audit: [`results/formal01/audit.json`](results/formal01/audit.json), SHA-256 `7a3c50690607645ba24b9fe463f7c23dd9dfce123b2a3fc0ddc23e7127f278c6`; errors empty, 96 cases checked. All seven post-result corruption mutations also rejected.
- All 48 rendered PNGs are retained under `results/formal01/corpus/`; they match the pre-frozen corpus manifest. No formal rerun, replacement or post-result tuning occurred.
- Runtime: cached PyTorch 2.5.1+cu121 Docker image, CUDA 12.1, Pillow 10.2.0, RTX 3080 Laptop GPU; `--network none`, read-only source bind, separate writable result mount, deterministic algorithms and `CUBLAS_WORKSPACE_CONFIG=:4096:8`.
- Formal invocations: 1; optimizer steps: 2,400; failed build attempt to obtain Pillow 10.4.0: construction-only, no training or data result; existing image's Pillow 10.2.0 was pinned before source/corpus freeze.

## Conclusion and boundary

This allocation does not support the claim that eight-family exposure beats two-family exposure under the frozen 400-step protocol. The observed broad arm was 4.17 points worse on aggregate and had no held-out exact hits on two of four families. No post-hoc increase in steps, threshold adjustment, family replacement or architecture tuning is included here. Any follow-up must be a fresh, explicitly linked successor allocation and must preserve this result unchanged. No real-UI grounding, action, deployment, token saving, or runtime promotion was tested or authorized.
