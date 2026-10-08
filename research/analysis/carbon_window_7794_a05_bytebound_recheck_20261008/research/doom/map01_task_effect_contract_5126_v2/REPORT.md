# #5126 contract v2 construction outcome — preserved gate failure

**Disposition: `FAIL_EXPECTED_GATE_MISMATCH`; not a formal allocation.**

## H / T / D / C / U

**H.** An untyped shared `source_event_id` namespace must reject both repeated
scorer source references and a scorer reference colliding with a physical
edge.

**T.** Reused the immutable #5126 v1 synthetic input corpus and ran the v2
candidate, independent oracle, and raw-only auditor. The raw corpus contains
both `duplicate_scorer_event` and `cross_plane_event_id_collision`.

**D.** Candidate/oracle agreed on all 13 rows; 12/13 candidate classifications
matched the then-frozen expected labels. The cross-plane collision was
correctly classified as `UNRESOLVED_DUPLICATE_SOURCE_EVENT`, but the
within-scorer duplicate was also classified as that new status while its
retained expected label remained `UNRESOLVED_DUPLICATE_EFFECT`. The raw-only
auditor therefore returned `FAIL_CROSS_PLANE_SOURCE_ID_GATE` with
`expected_gate:duplicate_scorer_event`. Preserve this result as a gate failure;
do not relabel it PASS. It exposes an outcome-taxonomy mismatch, not a
candidate/oracle disagreement.

**C.** Focused tests passed 5/5, including a post-classification raw collision
mutation detected by the auditor. The exact candidate, oracle, auditor,
runner, tests and failed output hashes are recorded below.

**U.** Host-only deterministic construction; no container, live scorer,
physical input, model, GPU, or source-schema readiness claim. This is a
pre-freeze construction failure, not the one-shot formal result. The prior v1
corpus and all v1 source/result/audit bytes remain unchanged.

Result SHA-256:
`faa3b38c12e277d1202cb692fea6d29ab89a270b55e2e23e82009104b7067d20`.
Audit SHA-256:
`50c7af00e2804c230f4bdfb7a0090f3d028b795aaebbb067f800bd9fa2294735`.

## Construction snapshot hashes (captured after the failed gate)

- `contract.py`: `e1dcb03c1afe655ad63d3355d578278e1fb91650f9bfb92d91ae28c53d3c59cb`
- `oracle.py`: `e67a553b510456e158caeed71825408467fa685bb77212c7be316f0a778dd43b`
- `audit.py`: `c52fe8a44dbc9c555e829ebb9fdb034de75e2dcc717e990bfe111b30ade03a68`
- `run.py`: `e80c13f5edf82e690fc80fd52871ac5d91a03e20b8abe55fb2329f570f970090`
- `test_contract.py`: `9a0210496e6872e7a34f10eb346c6f22a7726980ec21226e120a000d7b085ffc`
- Input v1 corpus: `536de27a25cdc7b9936235dc1ef900cf174f2acbf16239a696474ede5f69fa9f`

Next version will explicitly preserve the intended distinction between
cross-plane identity collision and duplicate scorer/effect rows before its own
freeze. No v2 output is overwritten.
