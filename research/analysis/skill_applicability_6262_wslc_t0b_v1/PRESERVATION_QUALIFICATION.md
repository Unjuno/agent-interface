# Historical container-reproduction preservation qualification

This note accompanies PR #6349 at original head `da13306b5117ae2d843b6a0883eb5a0e3e9610b2`. All 15 original evidence files, raw outputs, manifests, predecessor records and recorded `PASS_CONTAINER_REPRODUCTION_SCOPED` remain unchanged. Shared navigation is reconciled only by retaining all current-main entries and adding this package's original entry/link.

## Mutation-control scope

The inherited [auditor from #6289](https://github.com/Unjuno/agent-interface/blob/8b154b1f0ebb35dc7faa2eb4929cda9e35193604/research/analysis/skill_applicability_6262_gpu_t0_v1/auditor.py) names one control `fabricated_infeasible_edge`, but its implementation flips the full-ledger `wide_certificate_passes` Boolean; it does not fabricate an infeasible projection. The retained statement that four exact coded mutations were rejected must not be expanded into independently demonstrated infeasible-edge robustness. No source or result is repaired here.

## Receipt and review limits

The pre-freeze wrong-image-pin STOP and its correction remain preserved. Construction stderr prints five tests and OK, but construction.exit contains only a newline. Exact construction exit status remains unverified; it is not converted to a passing captured exit. Candidate/auditor exit 0/0 and invocation counts remain separately recorded in RUN_RECORD.json.

The 4,786,213-byte candidate raw was not fully reread for this review, and no hashes were recomputed. This is static source/receipt inspection and Git-blob custody verification, not independent full-raw revalidation. No candidate, auditor, test, GPU, container or scientific experiment was rerun.

This archive preserves a local WSL2/Podman CUDA reproduction of a finite synthetic fixture. It does not establish real skill applicability, GUI correctness, safety, product benefit, Docker parity, GPU necessity/speed or memory-limit enforcement. The embedded predecessor fixture ID remains unchanged and distinct from the external T0B allocation identity.
