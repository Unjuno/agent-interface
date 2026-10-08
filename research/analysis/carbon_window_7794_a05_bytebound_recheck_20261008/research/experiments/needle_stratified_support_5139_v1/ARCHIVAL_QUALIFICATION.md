# Archival qualification — closed PR #5169

This directory preserves, without modifying, the five original files from
`research/needle-stratified-support-5139-v1-20260928` at commit
`5f8310d7a6cfef255ed95a7acbe724c6f6f04fa6` (closed Draft PR #5169). The
preserved files and their Git blobs are byte-identical to that commit. This is
a preservation-only integration; it does not reopen #5169, change #5014/#5139
protocols, authorize a resource allocation, or promote the probe as an
experimental result.

## Scope and retained conclusion

The package is a host-only synthetic feasibility probe. It shows that a
deterministic nested 16-row/4-row selector can match template and field
marginals on a reconstructed 64-row `set` pool. The committed report records
four host tests and a separate raw-only audit with no errors. This is not the
full dataset generator or its independent raw audit, and it provides no model,
LoRA, quality, safety, latency, GPU, Docker, or population-level evidence.

The report's residual confound remains binding: the 16-row arm covers 16
template-by-field cells, while the nested 4-row arm covers only four. Matching
marginals therefore does not match the joint distribution or establish a
causal quality comparison. The fixed construction sentinel is not an
allocation/formal seed and must not be reused or selected for outcomes.

The original report's one-time local Docker/image readiness observation is
historical only: it explicitly records that no Docker invocation or image
execution occurred and that the allocation had no lease. No container, model,
CUDA, or GUI work is performed or authorized by this archive.

## Immutable source identities

Original PR #5169 reports these SHA-256 identities, independently matched to
the recovered files:

- `build_support.py`: `72f22a12665fa1e75da166ea18a45b10d69b45215e22546e483e647451846786`
- `audit_support.py`: `b45b2880ccff0e3b945b8702ed6451ab8483e7a5f784ae9efd69a3014498534e`
- `test_support.py`: `10b6eb386b6a5d99afc5b1f3da81ad22f7803224d2bafb74ed8c42161a33c01b`
- `raw.json`: `361a17ee45c6dd6e2e69b89da3c93216d4d2d778b95d4afdfbb68b4a98308053`
- `REPORT.md`: `3488fbd4bae9b2502ab6c8e9738eab1fbaeec01fbe0b07fa86d306baa9375ca0`

## Current local preservation checks

On current main `a0fbf78d5963f9392a3e75dff8db242c4b5e1317`, the package path was
absent before recovery. The old branch remained unchanged. The retained tests
and existing raw-only auditor are rerun locally once as preservation checks;
the historical report remains the source of its original run claims. These
checks do not clear #5139's separate current-main source/data/model/image,
historical attribution, reviewer, or exact resource-allocation gates.
