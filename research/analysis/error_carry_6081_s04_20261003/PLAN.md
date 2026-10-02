# Issue #6081 S04 — Euclidean-baseline and stateless-rounding successor

## Lineage and allocation

Fresh allocation: `ERROR-CARRY-6081-S04-WSLC-20261003-01`.
It follows the retained `STOP_METHOD_INVALID_BASELINE` in
`error_carry_6081_t0_20261001`; that candidate, audit, raw and STOP are not
edited or rerun. The correction has two parts: nearest-direction selection uses
exact squared Euclidean distance (including command norm), and the independent
per-slot arm is now stateless stochastic rounding rather than the predecessor's
identical repeated-nearest schedule. This is a method successor, not a repair
or reinterpretation of the consumed allocation.

## H / T / D / C / U

**H.** In the declared constant-displacement finite actuator model, exact
cumulative-error scheduling reduces all-offered mean squared prefix error on
nonrepresentable rational directions versus both (A) horizon-wide Euclidean
nearest legal direction and (B) fixed-seed independent stochastic rounding,
without any safety-envelope, deadline, release, calibration, or legality
regression. The null remains plausible.

**T.** Two separately scored alphabets (cardinal-4 and cardinal-plus-diagonal
8-way); twelve frozen direction rays; each ray normalized to the boundary of
that alphabet's convex hull (L1 for cardinal-4, L-infinity for 8-way); horizons
1, 2, 3, 4, 5, 7, 8; and eight fixed seeds for the stateless stochastic arm.
The four arms are horizon-nearest, independent stochastic rounding,
exact cumulative-error carry, and explicit no-continuation. This yields 5,376
primary requests plus three fail-closed controls. The candidate receives only
`cases.json`; a separately implemented raw-only auditor receives that input,
the hidden `truth.json`, and candidate raw output. Exact rational arithmetic is
used throughout. The fixed safety envelope is maximum per-coordinate prefix
error <= 1. Controls cover unavailable required combination, deadline shorter
than frozen horizon, calibration-ID mismatch, an omitted-release raw mutation,
and a held-out acceleration+collision model. Candidate and auditor each run at
most once in separate cached-digest WSLc containers (`--pull=never`,
`--network=none`, CPU-only), after construction tests and exact hash freeze.
Retries and tuning are zero.

**Primary endpoint / D.** The primary endpoint is mean squared position error
over every offered primary request and every requested prefix; a preflight
refusal counts as zero movement for all remaining prefixes, so refusal cannot
vanish from the denominator. `PASS_METHOD_SCOPED` requires the independently
reconstructed error-carry arm to be strictly lower than both A and B on the
pooled predeclared nonrepresentable linear cases, with per-alphabet results
shown separately; no emitted schedule may exceed the envelope; all completed
schedules must release; no illegal command or deadline extension is allowed;
exact-representable controls remain exact; all three formal refusal controls
match their frozen outcomes; and the auditor rejects omitted release. The
held-out nonlinear control must be classified as transfer-unsupported and is
never pooled into the linear endpoint. Any gate failure is retained as
`FAIL_METHOD`, `FAIL_AUDIT`, or `HOLD_TRANSFER`; no retuning or retry.

**C.** Independent stochastic rounding is seed-sensitive and can have
substantial finite-prefix variance; eight seeds are a deterministic probe, not
a confidence interval. Alphabet-specific normalization means the two
alphabets are not pooled as one physical actuator. A one-unit abstract safety
envelope is a method control, not a calibrated physical bound.

**U.** Synthetic exact arithmetic only. No OS/game/GUI input, calibrated motor,
real key dwell, latency, collision response, focus/lease behavior, model,
human outcome, MAP01 progress, or live safety claim. The nonlinear control is
an authored counterexample, not a physical-dynamics estimate. Diagonal command
semantics are abstract and do not imply any keyboard's actual displacement.

## Stop and provenance rules

Freeze exact current `main`, all source/data/test/oracle hashes, image digest,
and clean output paths before candidate launch. If source/main/image/path or
runtime checks fail, preserve a pre-candidate STOP with candidate/auditor
counts zero. Candidate exit must be zero before audit. Never inspect or alter
another container. Preserve every stdout/stderr, exit code, raw and audit byte.
The candidate ran once. The first independent audit invocation exposed an
oracle bookkeeping defect (the mutation-test sentinel was counted as a request)
and exited 2; it is retained unchanged. After an oracle-only correction and
passing construction tests, the auditor ran once more in a fresh container and
exited 0. This deviation and both audit outputs are reported; no candidate
retry occurred. Report WSLc resource controls only as requested unless
independently observed.
