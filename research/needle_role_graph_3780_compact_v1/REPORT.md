# Receipt-gated LoRA role graph — formal result

Allocation: `needle-role-graph-3779-compact-v1`
Issue: #3780
Branch: `research/needle-role-graph-3780-compact-20260921`
Disposition: `PASS_ROLE_GRAPH_SKILL_COMPOSITION_SCOPED`
Independent audit: `PASS_AUDIT_CONFIRMED_SCOPED`, zero errors.

## Frozen source

Runner SHA-256: `b9f92af480255b11febc607feb527827334ffa2ec26b1881b1c2166afd3cd5b8`
Auditor SHA-256: `7c6c20f86471231b550a502f17a9190e7819698538b82762caf6e3f647dd9c67`
The runner was frozen before its single formal invocation. Full compact, losslessly packed raw evidence is in [RESULT_ENVELOPE.json](RESULT_ENVELOPE.json); its decompressed canonical JSON hash is `8c2d2714061a35dc451e81366b8852696ee7a83af52bb94990e55afbe408e079` (19,823 bytes). The independent auditor verifies the outer digest, then recomputes metrics directly from all packed rows.

## Results

| Role | Correct | Held-out | Accuracy |
|---|---:|---:|---:|
| A (base) | 3,978 | 4,096 | 0.971191 |
| B (LoRA) | 3,761 | 4,096 | 0.918213 |
| C (LoRA) | 3,779 | 4,096 | 0.922607 |

All roles exceed the preregistered 0.90 threshold. Flat and graph dispatch packed rows are identical for all 12,288 examples. Both graph generations traversed A→B→C. Eight negative controls (unknown destination, skipped edge, wrong source, stale generation, wrong adapter version, unverified result, wrong scope, and duplicate receipt) yielded without graph-state mutation. The generation-1 receipt was rejected in generation 2. B/C full state snapshots round-tripped exactly; the base stayed tensor-identical.

Construction timing on Windows 10 / Python 3.11.9 / PyTorch 2.5.1+cu121, CPU, one thread, deterministic algorithms enabled: base training 1,952.4 ms; B adapter 43.0 ms; C adapter 42.8 ms. Timing is descriptive for this host and synthetic workload only.

## Provenance clarification

The frozen runner's result envelope contains the inherited literal allocation label `needle-role-graph-3775-v1`. The source SHA-256 above, preregistered successor identity, branch, and Issue #3780 identify this actual run; the embedded label is stale copy-forward metadata and must not be confused with unrelated repository item #3775. This discrepancy does not alter the packed rows or measured gates, but is retained explicitly as a provenance warning. Frozen runner/raw evidence are not edited.

## Environment and limits

Docker was checked but its Linux engine pipe was absent; this was a host-CPU run, not container evidence. No Docker restart/repair, image pull, disk cleanup, GUI or input occurred.

This establishes only a bounded synthetic composition result with fixture-oracle transition receipts. It does not establish realistic skill transfer, real application effects, production authorization, concurrency, cross-process persistence, or general performance. #3778 remains the separately preserved STOP caused by stdout truncation; its raw result is not reconstructed or changed by this new successor.
