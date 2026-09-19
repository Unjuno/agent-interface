# Partial-admission MAP01 held-input occupancy posthoc v2 — retained result

Task `MAP01-HELD-OCCUPANCY-PARTIAL-POSTHOC-20260916-002`, Issue #443.
Publication BASE `8176db65ae5ee0e742581ff5cff50d01d7a8155b`; source-first freeze HEAD `b95e678d182349bda4168698db5882de0b9ff0cb`; one complete-log compute head `e1ec11fc68e416b0ab391e4625b0de7da79f33aa`.

## Decision

**`SCHEMA_CENSORING_TOO_WIDE`.**

The new partial-admission semantics successfully close the analyzer-coverage failure retained by #428, and the complete v38/v39 retained logs now reconstruct and independently audit. However, the preregistered uncertainty gate fails for v39: aggregate interval width / occupancy upper bound is `0.25453708285828974`, above the frozen `0.25` maximum. The threshold is not changed post-result.

This is a measurement-schema result, not a live-control failure. It says the retained normal hold telemetry is still slightly too censored for the nominated next matched occupancy metric. It does **not** say v39 had less useful control than v38 or that a recovery mechanism failed.

## Source-first chronology

The exact GitHub-published analyzer/test/auditor/runner bytes were tested before the complete-log computation. Construction Actions run `35098614517`, job `104802092381`, used sparse checkout with no retained v38/v39 logs, py-compiled the published sources and passed seven frozen semantic tests. This included the exact #428 `cover-4:10` timestamps.

Authoritative source identities are in `FREEZE.md` / `plan.json`. The complete-log computation was then executed exactly once in Actions run `35098833590`, job `104802821158`. Frozen source SHA checks passed, frozen semantic tests passed again 7/7, the full computation completed, independent audit passed, result hashes were retained and the exact output artifact was uploaded.

No model/provider call, GUI action, XTEST input, game execution, or v38/v39 rerun occurred.

## New semantic boundary

Only pre-`keys_held` interruption handling changed from v1.

- `zero_admission_interrupted`: no task-key admission before independently verified empty termination; any-key occupancy `[0,0]` under the retained runtime event contract.
- `partial_admission_interrupted`: a strict prefix of requested keys was admitted but no `keys_held` marker was reached; any-key lower bound `0`, upper bound earliest admission attempt to earliest independently verified empty release; full keyset is explicitly **not** established.
- `full_admission_no_marker_interrupted`: all requested admission records exist but no `keys_held`; same conservative any-key interval and no full-keyset claim.
- normal completed holds and interruption after `keys_held`: inherited v1 rules unchanged.

The exact retained #428 counterexample now reconstructs as:

| field | value |
|---|---:|
| program / step | `cover-4:10` |
| requested | `Down + space` |
| admitted | `Down` only |
| classification | `partial_admission_interrupted` |
| any-key lower | `0.000 ms` |
| any-key upper | `13.209 ms` |
| full keyset established | `false` |

This edge accounts for only about **0.614%** of v39's total interval width. The semantic repair therefore makes the full analysis possible but is not the dominant remaining uncertainty.

## Complete retained-log result

| retained run | holds | class inventory | model wait | occupancy lower | occupancy upper | interval width | width / wait | width / upper | frozen gate |
|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| v38 | 11 | 11 ordinary completed | 27488.831 ms | 3048.890 ms | 4039.878 ms | 990.987 ms | 0.036051 | 0.245301 | PASS |
| v39 | 29 | 27 ordinary + 1 keys-held interruption + 1 partial admission | 43317.917 ms | 6301.200 ms | 8452.733 ms | 2151.534 ms | 0.049668 | **0.254537** | **TOO WIDE** |

The inherited gate requires **both** width/model-wait `<=0.10` and width/occupancy-upper `<=0.25` for both runs. v39 misses only the second criterion. Its allowed width at exactly 25% of the upper bound would be `2113.18325 ms`; observed width is `2151.534 ms`, an excess of `38.35075 ms`. This proximity is diagnostic only and is not permission to relax the frozen threshold.

### Decision-level intersections

v38's model-wait occupancy uncertainty is concentrated in iteration 1:

- iteration 1: lower `3048.890 ms`, upper `4039.878 ms`, width `990.987 ms` during `11418.360 ms` model wait;
- all other v38 decision windows have zero nominated cover-program occupancy in this metric.

v39:

- iteration 1: lower `1542.045 ms`, upper `2110.101 ms`, width `568.056 ms` during `5720.461 ms` model wait;
- iteration 4: lower `2228.434 ms`, upper `2987.122 ms`, width `758.688 ms` during `7197.658 ms` model wait; this window includes the 13.209 ms partial-admission `cover-4:10` edge;
- iteration 5: lower `2530.721 ms`, upper `3355.510 ms`, width `824.790 ms` during `8915.949 ms` model wait;
- other v39 decision windows have zero nominated cover-program occupancy in this metric.

The interval widths are dominated by ordinary completed holds whose normal key-up calls were not timestamped. That is the next measurement bottleneck.

## Independent audit and retained evidence

Frozen independent auditor status: **`PASS_PARTIAL_OCCUPANCY_AUDIT`**, zero errors.

Exact output identities:

- `result.json` SHA-256 `e6b99058f7d0424f51451cb7ebb0e418572c5f72a5c307e2fb6a0496b819c702`;
- `summary.log` SHA-256 `c830015b2d48b5beaa90f041b7f4d807b5feb1ed3775f0ce83c7ca2ac5f29d98`;
- `audit.json` SHA-256 `88e2286f409d6ec79e97f5b392fc259cb8a0280d8eba0d4cfb79f9328bbfb22e`;
- exact Actions artifact ZIP SHA-256 `1391709838769fe65da09c795470233fe27431f799141b165606669b76962cf5`.

The exact output artifact is retained losslessly in this research directory as base64-encoded ZIP plus a verification/restoration helper. Raw v38/v39 runtime logs are not duplicated; they remain in their existing canonical repository paths and are bound by the frozen SHA-256 values.

## H / T / D / C / U

**H:** explicit zero/partial/full-no-marker interruption states are sufficient to reconstruct every started hold in the complete retained logs without overstating intended multi-key occupancy.

**T:** seven pre-frozen semantic tests including the exact `cover-4:10` edge, SHA-bound v38/v39 retained inputs, one complete-log compute attempt, independent auditor and unchanged #428 diagnostic gate.

**D:** semantic reconstruction **PASS**; independent audit **PASS**; final measurement disposition **`SCHEMA_CENSORING_TOO_WIDE`** because v39 width/upper=`0.254537 > 0.25`.

**C:** physical any-key occupancy is not useful task control. A partial key admission can have a physical effect without ever establishing the intended keyset. Conversely, verified-empty release is only an upper endpoint for ordinary unlogged key-up. The remaining uncertainty is mainly ordinary-hold release timing, not partial-admission classification.

**U:** two stochastic retained episodes, no causal v38-v39 comparison, no exact normal key-up time, no threat/survival or task-effect score, and no new live evidence.

## Next single question

Do **not** add more posthoc semantics or tune the 0.25 gate. Instrument the local input-owner path so every task-key `up` has a monotonic timestamp tied to the same owner/program/step receipt, then validate that instrumentation in the smallest disposable X11 hold/cancel fixture before another MAP01 allocation.

The next rung should ask whether explicit key-up telemetry collapses interval width enough while preserving verified release/cancel behavior. It should not require a new model call or MAP01 run until the instrumentation itself is independently validated.
