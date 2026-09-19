# Use-boundary source-version recheck — rendered cooperative condition view

Decision: **PASS_SOURCE_VERSION_RECHECK_SCOPED**. Retain a cooperative source-version recheck as a fail-closed read/use freshness candidate. It is not authentication, semantic equality proof, atomic action admission, or a production runtime change.

Task lineage: Issue #249; stopped allocation `QUIET-LATCH-USE-RECHECK-20260916-009`; completed allocation `QUIET-LATCH-USE-RECHECK-20260916-010`.
Publication base frozen before measurement: `0a9156e7c0931b086f5276e79873cf9fe03382eb`.
Exact additive scope: `research/live_control/quiet_latch_use_recheck_v1/**`.

## Question

The preceding fresh-condition candidate accepts a cooperative current-condition sample after producer restart, while keeping unacknowledged warning history independent. That sample is already historical by the time it is consumed. This block asks one narrower question:

> if the cooperative source changes between sample acceptance and use, does checking only the source's monotonic version at the use boundary prevent consumption of the stale sampled value?

Both arms receive the same initial full condition sample and the same second source-version receipt. The only classification difference is whether the second receipt is enforced. Pending warning history, SQLite persistence, rendered fixture, event identity and source process are otherwise the same. No task input API is present.

## Frozen design

Before measured execution, Issue #249 records exact source hashes, the 56-case schedule, shuffle seed and gates. The schedule contains:

- stable true and stable false;
- true→false and false→true after initial sampling;
- true→false→true and false→true→false ABA trajectories;
- four candidate-only malformed/stale recheck controls.

Each main trajectory has four repetitions per arm: 48 main cases. Four control classes have two repetitions each: 8 controls. Total: 56 first cases.

The baseline receives but ignores the valid source-version recheck for classification. The candidate consumes the original sample only if the use-time source version equals its sampled source version. A mismatch or invalid recheck yields `UNKNOWN`; it does not overwrite the old evidence, acknowledge pending history or grant input.

### Construction and stopped allocation retained

Two pre-measurement harness problems were preserved:

1. the first construction runner placed successful Xvfb display-name assignment inside the same-line `if` suite, leaving `DISPLAY` undefined on success;
2. after that was fixed, a construction-only audit expected a stable candidate template that the two-case construction matrix did not contain.

Both occurred before measured allocation. A three-case construction then passed execution and audit.

Allocation 009 retained the scientific source and original schedule but was terminated by the outer tool budget after six complete first outcomes, with one additional incomplete case directory. `EXTERNAL_STOP.json` identifies the six complete cases and incomplete directory. No 009 result is pooled or substituted into 010.

Allocation 010 changes only orchestration: every already-frozen case runs in a fresh private Xvfb/database/source/application process through `run_case.py`. `finalize.py` merely checks all declared first outcomes before writing the final manifest. The measured per-case function and candidate logic are unchanged from 009.

## Environment

- CPython 3.13.5
- Linux 6.18.44
- SQLite 3.46.1
- python-xlib 0.33
- Intel Xeon Platinum 8370C, affinity CPUs 0..4
- CPU operating frequency not pinned
- local `CLOCK_MONOTONIC`; reported resolution 1 ns
- fresh private Xvfb 640x400x24 per measured case
- zero model calls, zero game calls, zero task-input/actuation requests

Clock resolution is not timing accuracy or a scheduling bound.

## First measured results

| Condition | Baseline | Source-version recheck candidate |
|---|---:|---:|
| Stable sample remains current | 8/8 correct | 8/8 correct |
| One source change after sample | **8/8 stale wrong value consumed** | **8/8 UNKNOWN** |
| ABA: state changes and returns | 8/8 final value correct | **8/8 UNKNOWN** |
| Invalid/stale recheck controls | n/a | **8/8 UNKNOWN** |
| Pending warning history preserved | 24/24 | 32/32 including controls |
| Task-input requests | 0 | 0 |

All frozen gates pass.

The flip condition is the positive safety result: the baseline consumes the old sampled boolean after the source has changed, while the candidate detects a version mismatch and refuses to classify that old sample as current.

The ABA condition is the explicit availability cost: source state returns to the same semantic boolean that was initially sampled, so the baseline happens to be correct. The candidate still yields `UNKNOWN` because the source changed twice. **The version token proves no change, not semantic equivalence after change.** This false stop is retained rather than optimized away post hoc.

## Descriptive timing

Both arms intentionally perform the same source-version request, so these numbers do **not** estimate the cost of adding a recheck relative to a system that makes no second request. They describe the frozen experiment path only.

| Endpoint | Baseline median [range] | Candidate median [range] |
|---|---:|---:|
| recheck source round trip | 0.227255 ms [0.125015, 0.597390] | 0.247856 ms [0.164090, 1.089436] |
| consume/render round trip | 0.626310 ms [0.508650, 1.604454] | 0.633808 ms [0.393057, 1.363545] |

These are serial single-case observations on one shared host, not latency guarantees or population intervals.

## Evidence semantics

The source version is cooperative metadata. The experiment assumes the source increments it on every relevant write. A faulty or malicious source can lie, skip increments or return fabricated versions. The version is not authentication.

A successful recheck still does not atomically couple the sample to a later action. State can change after the recheck and before any subsequent side effect. This study deliberately stops at the read/use classification boundary and issues no input.

Unacknowledged event history remains preserved throughout. A condition recheck cannot acknowledge a past event, resolve an active condition, mint a Lease, revive prior input or infer task success.

## ERROR CHECK

The independent checker imports none of the measured condition-view implementation. It verifies:

- the frozen schedule and source SHA-256 identities;
- every measured file in the final manifest;
- source-version progression and initial/recheck receipts;
- process restart identity and SQLite integrity;
- pending-history preservation;
- rendered current/pending pixel digests;
- zero task-input events/requests;
- all main classifications and control refusals.

Six semantic audit corruptions are rejected: erased pending history, invented input, wrong source version, fabricated pixels, fabricated clean process termination, and forced stale candidate classification in a stable case.

## H / T / D / C / U

**H:** a use-time source-version check can reject a current-condition sample that changed after read but before use.

**T:** 56 frozen serial first cases, plus construction and a separately retained stopped 009 allocation. Exact same recheck receipt is given to both measured arms; only enforcement differs.

**D:** all preregistered gates pass. Retain `PASS_SOURCE_VERSION_RECHECK_SCOPED`. Do not promote ABA behavior as efficient; it is an intentionally conservative false stop.

**C:** a semantic-equivalence check could avoid some ABA false stops, but would require stronger source semantics and is a separate mechanism. A source can also change immediately after the version recheck.

**U:** one cooperative boolean source, one rendered synthetic fixture, one host, no task input, no model/game, no source authentication, no atomic check/action transaction, no cross-domain evidence.

## Next single question

Keep persistence and source-version semantics fixed. Add exactly one **check-to-side-effect race** fixture: after a successful version recheck, mutate the source before a separately admitted dummy side effect. Compare (A) recheck-only admission with (B) a source-version condition that is validated in the same local commit boundary as the dummy side effect. Do not add model behavior or richer semantic matching in that experiment.
