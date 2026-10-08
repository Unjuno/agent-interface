# Issue #6061 — T0 finite control fixture

## H / T / D / C / U

**H.** On a frozen finite target family, prediction-error-triggered action chunks preserve terminal target-tracking effect and release safety at least as well as fixed-period feedback while reducing full observations on predictable motion; abrupt reversal tests whether the residual trigger recovers sooner than nonpredictive sample-and-hold.

**T.** Eight opaque fixture rows × four policies (`fixed`, `triggered`, `sample_hold`, `yield`), six action ticks, max speed 1, capture period 4, residual trigger threshold 1. The fixture includes constant/perfect-predictor, abrupt reversal/stale-predictor, target disappearance, lease invalidation, focus invalidation, target-binding loss, stationary/zero-error, and abrupt-jump cases. Candidate output logs capture ticks, residual checks, action ticks/values, release reason, final tracking error, effect, and safety. A continuous low-cost `fast_position` stream supplies the residual; full observation is counted only at selected capture ticks. The raw-only auditor separately reconstructs all 32 policy traces and rejects five mutations (drop row, false capture, target-loss continuation, lease violation, false effect). Frozen local image intended: `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, `--pull never --network none --cpus 1 --rm`, candidate and auditor in separate WSLc containers, source read-only, unique outputs. GPU is intentionally unused.

**D.** `PASS_METHOD_SCOPED` only if all 32 rows independently reconstruct; triggered policy matches fixed policy's effect on every declared eligible row; at least one perfect-predictor row uses fewer full observations; stale-predictor reversal recovers with effect; target/focus/lease/binding gates release before any invalid action; and all five raw mutations are rejected. Any trace disagreement or safety continuation is FAIL; provenance or runtime gate failures are STOP; no retries.

**C.** The fixture's deterministic residual stream and motion law are authored; the residual may be more informative than a real GUI image channel, and cost is counted as observation/probe counts rather than measured wall-clock time.

**U.** Synthetic method result only. No DOOM/MAP01, GUI, model, OS input, physical held key, latency distribution, natural error rate, safety guarantee, user benefit, or runtime validation.

## Local construction checkpoint (not formal)

Host CPython 3.11.9 construction-only run `construction-02`: candidate/auditor agreement on 32 rows, zero errors (`PASS_METHOD_SCOPED`); five mutated outputs rejected (5/5). Candidate raw, audit output, stderr and exits are retained in the construction directory. The source is still preparation state: no current-main branch has been frozen, no formal candidate/auditor container has run, no allocation result is claimed, and the formal retry budget remains zero.

Two earlier pre-freeze construction attempts were rejected and remain distinct from the formal allocation. Attempt 01 compared the post-action agent state with the next tick's target, falsely failing the perfect-predictor and stale-predictor controls. During the sensor-refactor attempt, the raw-only oracle retained one reference to the removed residual field and stopped with `KeyError`; no construction result was produced. The final pre-freeze construction corrected both conditions and saved fresh output. These were source/construction issues, not formal candidate/auditor invocations or scientific outcomes; their console errors remain in this task transcript.

WSLc invocation is pending explicit resolution of the current #5085 owner/runtime HOLD. Do not launch until the user confirms the one-shot exception and all remaining source/branch/path/image/output gates are freshly verified. If not cleared, preserve STOP without substituting host-run output for the formal T0.
