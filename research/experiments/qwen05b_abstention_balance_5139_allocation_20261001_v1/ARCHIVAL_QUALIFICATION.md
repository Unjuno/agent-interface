# Archival qualification — Issue #5139 allocation preparation

This package preserves inactive Draft PR #5877 branch `research/qwen05b-abstention-balance-5139-20261001-01`, head `f6184be61bbb4a69f267a99d759f49f19ceab5d3`, as preparation history only. Its fourteen original files are unchanged. The reservation recorded in the package was for 2026-10-01 and is expired; this archive does not renew it.

## H / T / D / C / U

- **H:** with an equal 32-row support budget and the specified fixed model/training/evaluation protocol, the balanced 4-per-class support sample may improve exact action/effect quality and abstention safety over the predecessor-shaped support mix.
- **T:** the archived package specified a two-arm Qwen2.5-0.5B LoRA study on a local RTX 3080 and Docker Desktop, with a finite GPU window, frozen source/data/model/tokenizer/image and an independent CPU audit. That window has expired; the package was based on an older main and is not a current formal freeze.
- **D:** no Docker workload, model/tokenizer load, CUDA call, fit, adapter update, candidate, or formal audit occurred for this allocation. The PR's historical host-only suite was reported as 17/17 construction tests. This recovery reran the package's pinned CPU construction suite on 2026-10-03 under CPython 3.14.5: 17/17 pass. `py_compile` passed and the current analysis index reports 594 retained result/failure directories. Such tests do not satisfy any model-quality gate.
- **C:** historical `sad_cannon` execution identity/owner/fit count remain unresolved; this archive does not infer that prior fits were zero, that resources are now free, or that predecessor allocations did not overlap. The reserved window and stale main pin are not reused.
- **U:** no model-quality, abstention, adapter, runtime, product, or GPU result is established. The expired allocation, unresolved historical execution attribution, stale freeze and current Docker/runtime gate prevent formal execution.

## Integrity qualification

The original `SHA256SUMS.txt` and `FREEZE.sha256` are preserved unchanged. `SHA256SUMS.txt` has thirteen entries, of which three fail: `FREEZE.json` once and the duplicate `COVERAGE_SUMMARY.json` entry twice; the other ten entries pass. The separate one-entry `FREEZE.sha256` also fails on `FREEZE.json`. `ARCHIVAL_SOURCE_SHA256SUMS` records the actual SHA-256 values for all fourteen recovered original files without repairing or rewriting either historical manifest. All fourteen recovered Git blobs were compared against the original PR head.

Disposition: `ARCHIVE_PREPARATION_ONLY_EXPIRED_ALLOCATION_AND_UNRESOLVED_HISTORY`. Issue #5139 remains open. Any future study requires a distinct current-main freeze, reconciliation of historical execution attribution, fresh source/data/model/tokenizer/image hashes, and a new explicit exclusive resource allocation. Do not run the archived formal runner under this expired allocation.
