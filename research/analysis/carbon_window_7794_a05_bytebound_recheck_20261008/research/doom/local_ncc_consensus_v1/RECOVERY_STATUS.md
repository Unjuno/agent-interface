# Recovery status: source-only archive, formal allocation unconsumed

This directory preserves the exact nine Git blobs from
`research/local-ncc-consensus-20260923` at
`793f8b2e14132b1f5123bcbf2baedc807760fdca`.
The source subtree is `328c22aa8d2197439a67254030bb8133ea29c32f`.
This is preservation of an existing source/plan/freeze package, not a new
experiment, formal result, runtime promotion, or completion of Issue #4163.

## Availability and execution boundary

All nine tracked files are available. The package contains a deterministic
five-band local NCC consensus mechanism probe, its fixed cases, runner,
verifier, tests, environment description, plan, and source hashes. It contains
no formal raw rows or result package. The latest Issue status reports the
original allocation remains unconsumed at formal **0/10**.

The frozen environment is Linux 6.18.44 x86_64 / glibc 2.41, CPython 3.13.5
(July 15, 2026 build), and NumPy 2.3.5. The Issue records that inspected host
and container alternatives did not establish that exact environment.
Historical host-only unit checks are construction evidence, not formal
execution or frozen-environment replication.

No source, runner, verifier, unit test, formal case, or copied-evidence control
was executed during this preservation inspection. Only downloaded file bytes
were hashed.

## Byte-level verification and provenance qualification

All eight `source_sha256` entries in the committed `FREEZE.json` match the
downloaded committed source/document bytes. Preserve all nine original Git
blobs unchanged.

The committed `FREEZE.json` itself (Git blob
`c7c38aed36b7f30af1868b420f6b8bb31e274b59`) has SHA-256
`01d315ac8366057cd7251d08c58e2f20ab6856248e64319e04971387e8fae892`.
The original pre-measurement Issue comment instead printed
`3c817c055900b6fe562065e16b8cc8854edd8cc31982bc53f4147ae16465b5be`
for FREEZE.json. These identities do not match. Git path history at the source
head exposes only its original freeze commit
`793f8b2e14132b1f5123bcbf2baedc807760fdca`. This archive preserves the
retrievable bytes and explicitly does **not** claim that the historical
FREEZE self-digest was reproduced. It does not rewrite the manifest or
reinterpret this discrepancy as a scientific result.

## Disposition and dependencies

**SOURCE_ONLY_ARCHIVE / UNCONSUMED_FORMAL_0_OF_10 /
HOLD_EXACT_FROZEN_ENVIRONMENT_AND_FREEZE_PROVENANCE.**

Source preservation does not authorize execution. Resolve the frozen
environment and the documented FREEZE self-digest discrepancy before
considering any formal action, under the original Issue's coordination and
authorization. No missing result is reconstructed and no threshold, seed,
case, plan, or scientific gate is changed. Preserve the original branch as
provenance.

At the 2026-10-01 preservation inspection, no PR used the source branch as
its head or base, and this study directory was absent from main commit
`40885011a5d8e15ab10bb6cc0e8eef65661718ee`. This is a bounded repository
check, not knowledge of all workers' unpushed local work. Source preservation
does not reserve or consume the pending formal allocation.

Sources:
- [Preserved source head](https://github.com/Unjuno/agent-interface/tree/793f8b2e14132b1f5123bcbf2baedc807760fdca/research/doom/local_ncc_consensus_v1)
- [Original public freeze](https://github.com/Unjuno/agent-interface/issues/4163#issuecomment-5787674638)
- [Environment STOP](https://github.com/Unjuno/agent-interface/issues/4163#issuecomment-5906860259) and [host inventory correction](https://github.com/Unjuno/agent-interface/issues/4163#issuecomment-5906870427)
- [Latest source-integrity and unconsumed-allocation status](https://github.com/Unjuno/agent-interface/issues/4163#issuecomment-5921015291)

