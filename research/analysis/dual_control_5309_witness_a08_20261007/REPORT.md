# Issue #5309 A08 — isolated effect-witness boundary

## Result

`PASS_WITNESS_BOUNDARY_SCOPED`. A08 is the first method-valid run in this successor chain: the candidate had no mount for the auditor oracle or hidden-state labels, and its source/input contain no truth mapping. The independent auditor reconstructed all 56 rows with zero errors and zero authority grants. This establishes only the finite authored method boundary described below.

## Frozen allocation and execution

- Issue: [#5309](https://github.com/Unjuno/agent-interface/issues/5309); allocation `5309-WITNESS-A08-ORBSTACK-20261007`.
- Frozen main: `3dba6c86f212c37a2d80c844b816c38921a42cc5`.
- Container: OrbStack Docker 29.4.0, linux/arm64; Python 3.14.5 image pinned to `python@sha256:c845af9399020c7e562969a13689e929074a10fd057acd1b1fad06a2fb068e97`.
- Candidate and auditor each ran exactly once, exit 0; no retries. Network disabled, root filesystem read-only, only declared mounts present, configured 1 CPU/256 MiB, capabilities dropped. These are container settings; resource-limit enforcement was not independently benchmarked.
- Candidate isolation smoke confirmed candidate code/input available, oracle absent, source read-only. Auditor smoke confirmed oracle available and candidate source absent.

## Hypothesis and gate

Under equal predicted information gain and the same two-action admitted set, generic IG's deterministic lexical tie selects the action that yields an exact state receipt while losing the independent effect receipt. It must not complete the task. Witness-aware ranking selects the equal-cost action predicted to preserve that receipt and completes only when an independent receipt is actually observed.

The finite table is two opaque receipt cases × seven scenarios × four arms = 56 rows. The auditor—not the candidate—maps case IDs to true hidden state, correct commit, and effect receipt. The candidate chooses a commit only from the observed receipt symbol and its declared receipt-to-task mapping.

## Findings

- Primary: both compared arms expose the same admitted action set. GENERIC_IG picks `a-progress-witness-loss`, returns `UNKNOWN_EFFECT_WITNESS_LOST`; WITNESS_AWARE picks `b-progress-preserve-witness`, verifies the observed effect receipt, and returns `COMPLETE`.
- Existing-witness control: both arms complete using the pre-existing receipt, with no supplemental probe.
- No-safe-path and stale-receipt: UNKNOWN. Duplicate receipt ID: consumed once; witness-aware completes only on the single receipt. Urgent stop: `STOP_AND_RELEASE` before commit. Misspecified model: witness-aware returns `UNKNOWN_MODEL_MISMATCH`. Fail-closed never acts; task-only remains `UNKNOWN_TASK_TARGET`.
- All 56 decisions, action choices, effect receipts, commits, stop/freshness/dedup traces and zero-authority rows were independently reconstructed. Six construction-time corruption cases were rejected before freeze.

## Retained evidence and hashes

- Candidate raw: [candidate-raw.json](out/candidate-raw.json), SHA-256 `7ab0a1a031e3a174ae44a6983cb050d09a4f6fc77a9af5c572d09051fc11fb0c`.
- Independent audit: [audit.json](out/audit.json), SHA-256 `0b9925023fbf55b04d587886b6a56a25c7690f87fd5fc254fb0200338ccbf132`.
- Candidate input SHA-256: `fc0465c31f04c47055bb91d3a819b97469661ae88f7b4ff37ac7912df7200984`.
- Oracle SHA-256: `953a4b868d9244fb178c07e275f4004e3a2d333f2db89d0f10be3923e311f62d`.
- Candidate SHA-256: `591289612179c1f53d6c7283a45eb0f24ba102b9d2eb40850c68d70e68aa9b5e`.
- Auditor SHA-256: `81ae0b9c00e49d575af313eaef46376ee1ab5c08ffb6adaced4d566196b8e98c`.
- Frozen commands, all remaining source/test hashes and H/T/D/C/U: [PRE_RUN.md](PRE_RUN.md) and the pre-execution registration on Issue #5309.

## Lineage, limitations, next boundary

A04 was STOPped before invocation because main advanced after freeze. A05 was a pre-start invalid Docker mount option. A06 raw audit passed but the candidate read the oracle truth table, so it is `FAIL_METHOD_CANDIDATE_TRUTH_LEAKAGE` and is not evidence for H. A07 had a pre-start output-mount path typo. All are preserved in their own additive paths and Issue comments; none was rerun. A08 corrects the method and launcher separation.

This remains a synthetic finite model, deliberately favorable to the witness-aware tie-break. It does not estimate how often real applications destroy effect evidence, validate user utility, or establish GUI/model/runtime/product benefit, human performance, safety, or physical release. A next useful test would vary observation-model misspecification and witness cost across held-out, non-isomorphic finite dynamics before any natural-interface claim.
