# Intent-generation fencing T0 — result

## H / T / D / C / U

**H.** In the frozen finite event-order fixture, FENCE_RECONCILE blocks old-generation proposals after a delivered authenticated revision, cancels admitted/unemitted work with verified release, preserves UNKNOWN for emitted/pending effects, preserves completed effects, and resists stale messages and generation reuse. Compare START_ONLY and atomic ADMISSION_FENCE.

**T.** Eleven event traces × three policies = 33 rows. Raw rows retain ordered events, proposal/published/delivered tokens, delivery uncertainty, prior effect state, admission, emission, terminal effect state, release and stale reactivation. One candidate process, one separate raw-only auditor process; no task input, GUI, model, input injection or product runtime.

**D. PASS_METHOD_SCOPED.** Candidate exit 0; 33 unique rows. Independent auditor exit 0, errors empty, and 4/4 corruption controls rejected. Stable no-revision case progresses. FENCE_RECONCILE refuses known superseded proposals, cancels pre-emission work with release, marks emitted/pending effects UNKNOWN with release, retains verified completed effects, holds when delivery is uncertain, rejects generation reuse across planner restart, rejects a revision between precheck and commit, and does not reactivate stale intent. Atomic ADMISSION_FENCE also rejects the check/commit race. This is only the frozen deterministic fixture result.

Raw SHA-256: `ac463423fbc353e04fe570caa139f5bbb8050f86e23f6a092524acdb6a2300bb`. Audit SHA-256: `0ae689b20b8afb4bb99f4d4ab5b6747468e7fee4fa134cde5bd9b3ee1caf32d0`.

**C.** The reducer and independent oracle are synthetic. Actual authentication, transport, broker atomicity, OS emission/release, semantic effect receipts, and existing-gate sufficiency are untested.

**U.** Method-only finite event-order evidence. No product/runtime integration, GUI safety, human-consent, semantic alignment, latency, or real effect-reliability claim.

## Execution environment

Python 3.11.9 on Windows host, using RAM-only pipes and `-B`. Docker Desktop was open but bounded `docker info` timed out; C: had zero free bytes. No Docker/container/GPU/model/GUI/input/task effect was used. The predecessor allocation-01 auditor syntax STOP and missing raw capture are preserved separately at [v1 STOP](../intent_generation_fencing_3442_t0_v1/STOP.json); this is a distinct allocation and path, not a retry under allocation-01.
