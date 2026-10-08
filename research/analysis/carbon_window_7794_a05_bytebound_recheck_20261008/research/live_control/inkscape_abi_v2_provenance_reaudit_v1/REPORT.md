# Inkscape ABI-v2 provenance re-audit v1

Task: `O3-INKSCAPE-ABI-V2-PROVENANCE-REAUDIT-20260916-010`  
Issue: #215  
Immutable base: `227ba648f1c0b83e9a5b69f4e0c7d39839d3578f`

## H

The reconciliation that brought `inkscape_authority_ended_abi_v2/**` onto current main did not repair the original PR #168 live-formal source provenance defect. The old formal terminal/observation data can remain historically useful, but the claim that the formal live result is bound to retained/reconstructible bridge-v2 and normalizer-v2 source bytes must be re-audited separately from semantics.

## T

A source-first offline provenance audit froze GitHub observations before formal execution and recomputed current source identities directly from the retained files.

Current main identities:

- `authority_ended_bridge_v2.py`: SHA-256 `37e544086fe70087c0a2e6c03ce8c42c1c5dd71989f7fe541eb9055b3551eb52`; Git blob `63639f44eba47a2842e57e3761730e6f6224e815`
- `post_authority_normalize_v2.py`: SHA-256 `dc664652c7c29b002005feb7b69122d29619a449c6ad781a65ac5abfaa186d41`; Git blob `a6eb2b8a8964b34ac22dd4f1cbeaaff879f7e5b1`

The retained manifest, whose Git blob is `fc4b121620daabf011ff0948ef890473d65a33a1`, says the sources were “Frozen before formal seed 994600” and instead records:

- bridge: `37e6551baedaddad50ca8ef64677e3c387f742875ad3e28fa6ea630e58ad7d51`
- normalizer: `dc98340c5434160684802a92f04d96f47420bf908198f8861b2148cbd12bdc72`

The retained `build_candidate.py` Git blob `6c26d47a702f3af061658928fcfafa4bef4da4d1` hard-codes those same claimed formal hashes as its expected candidate identities.

GitHub also returned `404 Not Found` for both source paths when queried at formal-evidence commit `38f40605e6131d9695e1b3b3b789512819affb29`. The original direct parent chain is:

1. `38f40605...` — retain formal evidence;
2. `9ca8fbbb...` — add bridge-v2 source, parent = formal-evidence commit;
3. `08e176fb...` — add normalizer-v2 source, parent = bridge source commit.

## First outcome

Result ID: `inkscape-abi-v2-provenance-reaudit-v1-20260916-01`  
Formal retries: **0**  
Hard gates: **8/8 PASS**  
Decision: **`INVALIDATE_ABI_V2_FORMAL_SOURCE_PROVENANCE_REQUIRE_RERUN`**

All eight gates passed: current source hashes/blobs recomputed correctly; both current source hashes differ from the manifest’s formal claims; the rebuild gate reuses the stale claims; both source paths were absent at the formal-evidence commit; source-add commits are strictly after the formal-evidence commit; and reconciled main still retains the post-formal source blobs.

Formal-result SHA-256: `8734b094b5755142c9532b008add84c382026d61fb189d956e928926430e18e7`. Independent audit: PASS with zero errors.

## D

The old ABI-v2 live formal result is **not retained as source-bound/reconstructible formal evidence**. Reconciliation onto main does not repair missing pre-execution source identity.

This decision is deliberately narrower than semantic rejection:

- **Invalidated:** the claim that the old live formal run is reproducibly tied to the retained bridge-v2/normalizer-v2 source bytes.
- **Not invalidated by this audit:** the bridge-v2 semantic contract itself, offline contract evidence, and historical raw terminal/observation records.

Do not delete or rewrite the historical directory. Downstream work may use current exact source for new offline reasoning, but must not cite the old live formal as satisfying a source-first live gate.

## Required repair

One of two evidence closures is required before the live gate can be treated as passed:

1. recover the exact source bytes that actually executed in the old formal run and retain them immutably with verifiable identity; or
2. commit the complete current live candidate/runner source first, then perform one fresh model-free formal live run and retain its first outcome plus exact source identities.

Merely changing the manifest to the current hashes would be invalid: it would relabel the old run without proving those bytes executed.

## C

Exact old formal-run source bytes could still exist outside Git history. This audit only establishes that current canonical repository evidence cannot reconstruct them. The previously noted timing-label inconsistency is separate and non-gating.

## U

Until source-first live evidence is repaired, downstream live crash-after-send claims remain HOLD. The next action is environment feasibility plus source-first rerun preparation; no old evidence should be silently promoted to fill the gap.
