# #6576 timer-quantization eligibility experiment A01

## H / T / D / C / U

- **H:** A finite timing trace rounded to a coarse timer quantum can still be accepted by the current #6576 reference eligibility diagnostics, even when its threshold-exceedance tail has very few distinct observed values. This would expose an unmodeled measurement-resolution condition; it would not show that EVT is always invalid on quantized data.
- **T:** Freeze three independent synthetic exponential timing pairs (continuous control, quantum 0.25, quantum 1.0; scale 1.0; 4,000 training and 10,000 held-out observations per arm). Generate and hash all input before candidate execution. Run the current gate diagnostics on observed/rounded values. An independent raw-only auditor recomputes the sample identity, type-7 threshold, block-median stability, lag-1 threshold-indicator correlation, per-mode exceedance count, tie counts, and gate decision. Record underlying-latent held-out exceedances above the observed-data threshold as descriptive context only.
- **D:** `COUNTEREXAMPLE_A01` iff a quantized arm is `ELIGIBLE_REFERENCE` while its training threshold-exceedance set has at most 12 distinct observed values. Otherwise `NO_COUNTEREXAMPLE_IN_FROZEN_FIXTURE`. This finite synthetic diagnostic can only identify a missing eligibility dimension in this fixture; it does not establish estimator miscalibration or operational risk.
- **C:** One pinned Python 3.12 linux/arm64 container on the dedicated #6576 OrbStack VM/private Docker Engine, network disabled, read-only root/source/input, separate writable output, 1 CPU, 2 GiB RAM, swap 0. Candidate once; independent auditor once iff candidate exits 0; retries 0. This is not the formal six-case T0 allocation and does not use the shared native-CI Engine.
- **U:** No TailID/CRAN parity, EVT p99 calibration, independent-stationarity proof, physical release timing, real timer characterization, safety/deadline protection, or population claim. The chosen quanta are synthetic sensitivity settings, not assertions about this host's timer resolution.

## Frozen conditions and interpretation

Seed 65761111 generates three independent exponential streams. Each observed value is rounded to the nearest declared quantum (quantum 0 denotes no rounding). The gate diagnostic uses the current #6576 rule: 20 consecutive blocks' medians with maximum/minimum ratio at most 1.5, absolute lag-1 correlation of 90th-quantile exceedance indicators at most 0.1, at least 40 exceedances for the declared `normal` mode, no censoring, and a present synthetic endpoint identity. The tie counter is deliberately an audit measurement, not a post-hoc change to the candidate decision.

No fitting, case substitution, threshold tuning, or rerun is permitted after candidate invocation. Preserve any infrastructure or audit failure as the first outcome. This construction allocation is separate from the pending formal #6576 T0 and does not consume or authorize it.
