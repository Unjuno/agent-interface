# Issue #8049 A03 — result

**Disposition: `PASS_METHOD_SCOPED`.** The preregistered interval met the
declared repeated-cohort coverage tolerance on the frozen synthetic design.
This is not evidence of distribution-free coverage or production calibration.

## Execution and independent audit

Allocation `UNJUNO-8049-IPCW-REPEATED-UNCERTAINTY-A03-ORBSTACK-20261005`
used seed 8049021 and 20,000 cohorts (200 units per stratum; stratum risks
0.40/0.10; independent follow-up probabilities 0.25/0.75; target risk 0.25).
The pinned Linux/arm64 Python image ran with network disabled, read-only
rootfs and source inputs, and separate output mounts. CPU=1 and memory=1g were
requested; memory enforcement is not asserted. Candidate and auditor each ran
once, both exited 0, and no retries occurred. Candidate could not read oracle
outcomes. The auditor independently reconstructed the raw rows and rejected
all four frozen mutations.

| Gate | Observed | Frozen criterion | Result |
|---|---:|---:|---|
| Reconstructed units | 8,000,000 | all 20,000 cohorts | pass |
| HT mean | 0.250325 | within 0.0012503333 of 0.25 | pass |
| Empirical / exact HT SD | 0.04415699 / 0.04420596 | relative error ≤2.5% | pass (0.111%) |
| Bootstrap coverage | 0.94935 | within 0.006 of 0.95 | pass |
| Mutation controls rejected | 4 / 4 | all frozen controls | pass |

Complete-case mean was 0.175064 (population limit 0.175), illustrating the
selection distortion under this authored follow-up mechanism; it is not a
general empirical claim.

## Predecessors and limits

A01's Wald interval undercoverage remains unchanged. A02 is a distinct
pre-container Docker CLI syntax STOP and did not execute either process. A03
uses a fresh seed and the corrected, preflight-tested mount syntax; it does
not relabel or overwrite either predecessor. Four construction pilots were
not formal evidence and are not pooled with A03.

Inference is limited to this exact known two-stratum model, fixed stratum
counts, seed, and interval recipe. Estimated propensities, misspecification,
distribution shift, real verifier labels, GUI/product effects, and safety or
action authority were not tested. Requested container resource limits are not
treated as proof of enforcement.

## Reproduction pointers

See [FROZEN.json](FROZEN.json), [RUN_RECORD.json](RUN_RECORD.json), raw
candidate output under `results/candidate-out/`, raw logs under `results/`,
and the independent [audit](results/audit-out/audit.json). Candidate output
SHA-256 is `534df739c7cea76fe779c04f1af9ab81db6d3ed3e3f874feb3fa59ca55b7670c`;
audit SHA-256 is `5eb388dd6f93be2646188388c61e88e82217d9794e07791024810dd1fb61ff8e`.
