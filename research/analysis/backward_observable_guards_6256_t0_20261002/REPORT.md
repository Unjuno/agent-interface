# Issue #6256 T0 result: backward-derived observable guards

**Overall gate: `HOLD_INCOMPLETE_MUTATION_COVERAGE`.** The retained candidate and independent raw-only audit agree (`PASS_METHOD_SCOPED`, zero audit errors), but review against Issue #6256's full preregistered D criterion found that a required stale-generation mutation control was not explicitly run. Preserve the first result unchanged; do not promote this T0 to an overall pass.

## Question and method

For the frozen finite action `bounded_save_and_release`, compute the exact universal total-correctness preimage: every declared outcome must terminate within the 3-step horizon, produce `exact_target_saved`, avoid all forbidden prefix tags, and end with `empty_verified` release. Separately partition states by the permitted observation cues, search cue subsets on the predeclared `certificate_status=verified` stratum, and compare a loose authored guard to a guard made unnecessarily strict by a layout predicate. Candidate code and raw output are retained; the independent auditor re-enumerates the same frozen model without importing the candidate module.

## Result

- Frozen model: 10 states and 13 action outcomes. Construction suite before freeze: 7 tests passed.
- Candidate: one invocation, exit 0. Independent audit: one invocation, exit 0, `PASS_METHOD_SCOPED`, errors 0. Retries and posthoc candidate/auditor reruns: 0.
- Universal preimage: `ready_simple`, `ready_complex`, `unobservable_safe_alias`.
- In the verified-certificate stratum, the minimum sufficient cue set is six fields: pixels, fresh generation, fresh committed-state receipt, release availability, bounded termination, and effect-contract reliability. The certificate status is fixed to verified in this stratum.
- Pixels alone leave the visually identical ready/already-committed pair `UNKNOWN_NOT_OBSERVABLE`; the fresh typed committed-state receipt separates that pair into ADMIT and REFUSE.
- The missing-certificate safe/silent pair is identical under every permitted cue but has different modeled outcomes. It stays `UNKNOWN_NOT_OBSERVABLE`; no global cue set distinguishes the entire model. This correctly prevents the observed model from overclaiming observability.
- The loose authored guard admitted four unsafe states (`already_committed`, `late_completion`, `release_blocked`, `unreliable_effect_contract`). It also rejected two states in the mathematical preimage: the verified `ready_complex` case (a genuine overstrong-layout counterexample) and `unobservable_safe_alias` (which remains inadmissible in practice because its cue cell is mixed/UNKNOWN).
- Five implemented mutation controls exposed unsafe shortcuts: existential success over an unreliable save, omission of release, omission of termination, pixels-only merging of ready and duplicate-submit states, and omission of the forbidden-prefix check.

## Why HOLD

Issue #6256's D requires every specified negative mutation to be rejected, explicitly including ignoring stale generation. The frozen model includes a stale-generation state and the exact preimage/guard accounts for it, but this allocation did not include a separate mutation that drops the generation gate. The independent audit's pass therefore proves only the coded checks; it cannot substitute for the omitted preregistered control. This omission is not repaired posthoc, and the raw PASS is not relabeled. A separately frozen additive successor would be required to test that control.

## Scope

This is a deterministic synthetic finite-model result on Windows host CPU. Docker Desktop's service was stopped and its status command did not return within the bounded wait; no container, engine, or shared resource was changed. No real GUI, model, network, user data, external action, or OS input was used. The transition/effect table is an authored simulator; the result does not establish that a real application satisfies it, authorize input, replace independent post-action effect verification, or demonstrate safety, latency benefit, or product utility.

See `FREEZE.json`, `PLAN.md`, `MODEL.json`, source, raw candidate/audit JSON, and `results/t0-01/RUN.json` for provenance and reproduction.
