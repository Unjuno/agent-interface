# Issue #6575 — formal allocation 01 report

**Disposition: `STOP_HARNESS_FIXTURE_MISMATCH`.** This allocation does not answer whether observation transforms change visual prompt-injection susceptibility. The candidate completed, but the independent audit found a frozen fixture disagreement; no scientific comparison is accepted. The failed allocation and all receipts are retained as-is. No stage was retried.

## Frozen scope

Allocation `OBS-INJECTION-TRANSFORM-6575-T0-20261002-01` was a finite, model-free T0 construction/provenance check: six deterministic synthetic scenes (three stipulated content classes × two layouts), four arms, 24 rows, 36 image items, and 12 invalid-crop checks. It used native WSLc 3.0.1.0 with cached image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, pull disabled, network disabled, one CPU, requested 1G memory, and uid 65534. No model, GPU, or external effect was used. The WSLc warning was: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` Thus the requested memory cap is recorded, but enforcement is not asserted.

## Stage receipts and outcome

- Construction: one formal invocation, exit 0; 10/10 protocol tests passed.
- Candidate: one formal invocation, exit 0; emitted all 24 rows and 12 invalid-crop decisions. Raw output SHA-256: `E9BF2CF8AAE79A3884DA765A54CE5D7583DD6CCB2D46F051C3F593870DC263D3`.
- Independent auditor: one formal invocation, exit 1, `FAIL_METHOD`. It reconstructed all 36 image items, saw all 24 rows, and rejected all 12 invalid-crop checks. It reported six `pixel_provenance_mismatch` errors, one for each scene's `FULL_PLUS_SHAM_CROP` sham image.

The disagreement is exact and frozen: candidate construction uses sham box `[4,32,116,64]` (112×32), while the staged auditor oracle specifies `[4,36,116,60]` (112×24). Therefore the auditor's independently reconstructed sham pixels cannot match the candidate output. This is a harness/fixture mismatch, not evidence for or against any injection-susceptibility hypothesis. The construction tests generated their oracle from scene code and did not detect the independently staged static-oracle discrepancy; that test-coverage gap is also retained as a lesson, not repaired in this allocation.

No rerun, source/oracle edit, or output replacement was made after the auditor's exit. Any future attempt would require a distinct, separately preregistered allocation with an explicit protocol delta and independent oracle consistency checks; it must not overwrite or relabel this STOP. T1/model testing is not supported by this result.

## Retained artifacts

`RUN.json`, stdout/stderr, exit receipts, candidate raw output, auditor input copy, and auditor JSON remain in the stage directories. `SHA256SUMS` records the retained formal files. `FREEZE.json` remains the pre-run freeze, so its formal invocation counts correctly remain zero; realized counts are reported above.
