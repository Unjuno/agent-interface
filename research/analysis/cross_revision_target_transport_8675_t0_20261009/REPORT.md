# Issue #8675 T0 A01 — cross-revision target correspondence

**Disposition: `PASS_RELATIONAL_REIDENTIFICATION_SCOPED` for the frozen synthetic protocol.** The result supports a narrow structural-correspondence signal under sibling reorder. It does not validate a general entropic Gromov–Wasserstein implementation or establish live GUI identity.

The hypothesis was that a soft, fused node-and-relation matcher could recover more correct correspondences than exact ID/path and exact role-label-actionability baselines while abstaining on unsafe controls. The frozen gate required at least a 15 percentage-point held-out coverage gain, one-sided 95% upper false-rebind bound at or below 1%, abstention on every automorphism and semantic-change control, and independent reconstruction of every row.

## Frozen method and corpus

The source anchor is `cef53dbe8d131a8e116c92b5c79257f1db5f77b3` (`origin/main` at freeze). The deterministic corpus contains 860 graphs: 60 development identity controls, 300 held-out positives (100 each for sibling reorder, inserted duplicate Save, and transparent wrapper), and 500 held-out negatives (200 automorphisms, 150 removed targets, and 150 semantic-role changes). Candidate input excludes the oracle field; a pre-freeze test altered the oracle while confirming unchanged candidate output.

The relational candidate exhaustively enumerates injective mappings of five source nodes into each current graph. Its fused cost weights typed node-attribute mismatch and categorical pair-relation mismatch equally. It applies Gibbs soft mass to complete mappings at temperature 0.05 and emits a target only when best cost is at most 0.12, target marginal is at least 0.95, and the gap to the next target marginal is at least 0.90. A single-child node typed `container` is contracted for relation comparison in the transparent-wrapper fixture.

This is a finite, entropic assignment-space approximation to fused Gromov–Wasserstein matching. It is not the canonical entropic FGW optimization over fractional coupling matrices. The attribute baseline is an exact tuple match, not a nearest-neighbor implementation. Those method boundaries are part of the result.

## Observed result

| Method | Correct held-out positive matches | Coverage | False rebinds / 500 negatives |
|---|---:|---:|---:|
| Exact ID + path | 0 / 300 | 0.0% | 0 |
| Exact role + label + actionability | 0 / 300 | 0.0% | 0 |
| Relational soft assignment | 100 / 300 | 33.3% | 0 |

The relational method gained 33.3 percentage points over the best baseline. Its one-sided 95% exact binomial upper bound after zero false rebinds in 500 controls is 0.5974%, below the frozen 1% limit. The independent audit reconstructed all 860 predictions with no discrepancy, and all five corruption controls were detected.

The recovered cases were exactly the 100 sibling-reorder cases. It abstained on all 100 inserted-duplicate cases and all 100 wrapper cases, as well as all 200 automorphism, 150 removed-target, and 150 semantic-change controls. Therefore the aggregate discriminator passes, while evidence of useful transfer is limited to sibling reorder; this matcher did not demonstrate continuity through added lookalikes or a transparent wrapper at its frozen concentration threshold.

## Scope and next decision

The result is CPU-only synthetic method evidence. It does not measure OCR/accessibility errors, real app revisions, user intent, effect correctness, freshness, leases, focus, authorization, or action outcomes. A correspondence remains advisory and grants no action authority. The data supports keeping fail-closed re-grounding for revisions with added lookalikes or wrapper changes; it only motivates further isolated study of reorder continuity.

Formal candidate and audit invocations were each run once from the freeze; retries were zero. The per-case SHA-256 file was generated afterward as a custody supplement and did not affect any gate. `FREEZE.json` pins inputs, source, commands, thresholds, and pre-execution hashes. `results/raw.json` and `results/audit.json` preserve the exact one-shot outputs.

## Reproduction and integrity

Run from this directory:

```sh
python3 candidate.py design.json > results/raw.json
python3 audit.py design.json results/raw.json > results/audit.json
```

The commands above document the frozen protocol; do not rerun this consumed A01 allocation. SHA-256 values for the frozen inputs and outputs are listed in `SHA256SUMS`.
