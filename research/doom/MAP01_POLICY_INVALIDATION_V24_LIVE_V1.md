# MAP01 v24 guarded live allocation

The preregistered `map01-policy-invalidation-v24-live-01` allocation completed
12 Astra-low decisions in 137.278 s of continuously advancing MAP01 control.
The independent score was unfinished, alive at 76% health, two kills, no death,
and no exit.  These outcome values are descriptive because the seed differs
from v23 and the runs are sequential.

The one-way authority contract worked on four live changes.  Decisions 4–7
each recorded an `INVALIDATED` health-number ROI, cancelled the active cover,
verified its release, retained the concurrently completed model output, and
admitted none of that output's commands.  Each following decision used coast
with no inherited cover-policy source.  Across the run, all 16 cover programs
and all 8 admitted action programs have verified terminal releases.  Four cover
renewals had a maximum 38.848328 ms release-to-readmission gap.

| Decision | Earliest changed sequence | Trigger sequence | Earliest capture to detection | Detection to release |
|---:|---:|---:|---:|---:|
| 4 | 200 | 201 | 346.779956 ms | 34.367839 ms |
| 5 | 203 | 204 | 544.457007 ms | 26.577347 ms |
| 6 | 230 | 230 | 215.921784 ms | 20.422730 ms |
| 7 | 239 | 239 | 208.599702 ms | 21.066926 ms |

The timeout-polled controller skipped the first already-changed sample in two
cases and detected the following sample.  Capture-to-detection for the selected
trigger was 208.600–215.922 ms.  This is materially slower than the input
release itself and isolates an avoidable controller latency.  Evaluating a
fresh observation directly when it is dequeued should remove the polling tail;
that change needs a new controller version and replay tests before another live
allocation.

The model calls were not cancelled.  All four outputs that became stale still
finished, so the run spent four decision slots and their tokens before admitting
a new action at decision 8.  Total reported usage was 148,803 input tokens,
95,104 cached input tokens, 1,281 output tokens, and 90 reasoning tokens.  A
safe cancellable planner path could reduce wasted wall time or tokens, but it
must retain partial-call status and must not treat cancellation as a model
answer.  That is separate from the event-driven stop-latency repair.

The manual HUD transcription from hash-checked frames is health
`[100,100,100,100,100,93,85,82,76,76,76,76]` and ammo
`[50,50,50,50,47,45,45,45,45,42,37,34]`.  The health ROI cannot distinguish
damage from pickup, identify a threat, or authorize a recovery action.  The
live result establishes removal of stale authority only.  It does not establish
causal survival benefit, reliability, human-speed reaction, token efficiency,
or MAP01 completion.

Run `python research/doom/audit_map01_policy_invalidation_v24_live_v1.py` to
verify the frozen sources, retained-file hashes, raw model calls, guard replay,
cancel/release chain, zero discarded-action admissions, and zero discarded
cover inheritance.
