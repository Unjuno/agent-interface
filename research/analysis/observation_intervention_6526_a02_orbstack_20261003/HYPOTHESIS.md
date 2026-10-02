# Issue #6526 — A02 prospective successor (OrbStack)

Allocation: `OBSERVATION-INTERVENTION-6526-A02-ORBSTACK-20261003-01`

Predecessor A01 remains a terminal `STOP_AUDIT_ERRORS`; its exact 90 ms origin gate and raw/audit records are unchanged. A02 addresses only that method defect. It is a fresh randomized allocation (seed 652604), not a reclassification or rerun of A01.

## H / T / D / C / U

- **H:** In a disposable single-app Tk fixture with independent persistence-deadline sampling, periodic private-Xvfb root screenshots (`xwd`, nominal 10 ms cadence) increase missed persisted effects under a 100 ms deadline relative to endpoint-only MINIMAL and equal-cadence SHAM observation.
- **T:** Separate Xvfb/Tk smoke and 6-case construction preflight, then one frozen candidate and (only if candidate exits zero) one raw-only audit. Formal plan: seed 652604, 30 randomized blocks × 3 arms × 2 schedules = 180 trials. Each trial configures one `Tk.after(90, ...)` button invocation and atomic filesystem persistence. Deadline oracle samples at 100 ms (SENSITIVE) or 500 ms (STABLE) from a monotonic `trial_start`; screenshot/sham observation runs every 10 ms. The `after` arm timestamp and configured delay are recorded before starting the observer thread.
- **D:** Method-valid requires exactly 180 starts, one `action_schedule` and one action callback per trial, 180 independent deadline snapshots, balanced conditions and exact randomized execution order; each schedule uses delay 90 ms and is armed within 5 ms of `trial_start`; callback must not fire before its registered 90 ms delay. A callback arriving after the 100 ms deadline is a scored missed effect, not a method error: observer-induced event-loop delay is part of H's causal pathway. Persisted state is sampled independently; screenshot errors, missing provenance/records, contamination, or action-scheduling integrity errors yield STOP/HOLD. Stable control must succeed >=29/30 per arm. `H_PASS_SCOPED` requires SENSITIVE screenshot miss rate at least 0.20 above both controls and both one-sided exact paired McNemar p<=0.05; otherwise method-valid data yield `H_FAIL_SCOPED`.
- **C:** Same-machine CPU contention, X server capture scheduling, thread scheduling and filesystem behavior compete. Randomization within blocks and equal-cadence sham reduce but do not eliminate those explanations.
- **U:** One synthetic Tk fixture, one ARM64 OrbStack VM, one host and 30 blocks. No browser/other toolkit, human/model action, production-prevalence, or safety claim. VM quotas do not prove physical-host isolation.

## Freeze and stopping

Reuse the immutable A01 ARM64 image by exact image ID (no mutable pull); candidate and auditor containers use `--init --network=none --cpus=1 --memory=512m`. Freeze A02 source/input hashes, container invocation and decision rule before candidate execution. Candidate at most once; independent auditor at most once and only after exit 0. No rerun, post-outcome tuning, replacement rows, or pooling with A01. An incomplete/nonzero candidate is retained as STOP.

No external display, user data, live application, accessibility API, or consequential action is used. Candidate and auditor remain separate; the auditor consumes raw traces only.
