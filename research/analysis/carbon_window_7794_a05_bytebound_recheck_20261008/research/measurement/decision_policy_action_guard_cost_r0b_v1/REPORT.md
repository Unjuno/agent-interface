# Per-action current-evidence guard acquisition cost — first outcome

Decision: `PASS_ACTION_GUARD_ACQUISITION_COST_SCOPED`.

This continues the pre-existing source-first #1179 allocation. The originally retained `protocol.py`, `guard.py`, `PLAN.md`, and `prereg.json` bytes were preserved exactly. The completed source adds only the missing AF_UNIX server/runner/auditor mechanics needed by the preregistered comparison.

## Formal

One formal invocation, reruns/replacements/tuning 0. Seed `117920260918001`.

- warmup: 2,000 reads/arm, excluded;
- measured: 60,000 matched reads/arm, counterbalanced in 1,000-read blocks;
- invalidation publication -> socket response -> typed refusal probes: 10,000;
- malformed controls: 7/7 fail closed;
- stale HARD accepted effects: 0;
- AMBIGUOUS accepted effects: 0;
- inproc/socket disposition mismatches: 0.

Timing:

| Metric | p50 | p95 | p99 | max |
|---|---:|---:|---:|---:|
| in-process acquisition+validation | 0.001652 ms | 0.001752 ms | 0.003115 ms | 1.243241 ms |
| AF_UNIX acquisition+validation | **0.025028 ms** | **0.039589 ms** | **0.078198 ms** | 3.405086 ms |
| socket-minus-inproc paired delta | **0.023336 ms** | **0.037866 ms** | **0.076516 ms** | 3.403433 ms |
| invalidation publication -> typed refusal | **0.010847 ms** | **0.021849 ms** | **0.040826 ms** | **0.345029 ms** |

Frozen gates were socket p95 <=1.0 ms, p99 <=2.0 ms, median socket-minus-inproc <=0.50 ms, invalidation-refusal p95 <=2.0 ms and max <=10.0 ms. All pass with substantial margin.

## Interpretation

A separate local process boundary for acquiring a small fixed-size current-evidence record is comfortably cheap on this host. In this scoped design, per-action deterministic currentness validation is not a latency reason to replace the guard with a learned/high-frequency semantic supervisor. The richer Astra-authored cached policy can remain outside the critical path while a cheap local evidence fetch remains the final gate.

The result does not establish production observation cost. AF_UNIX with a 57-byte binary record is a controlled proxy; an actual compositor/screenshot/semantic evidence primitive can have different tails. The existing private-X11 ROI result #1172 separately measures one actual visual evidence primitive.

## Integrity

- formal raw RESULT SHA-256 `cec1844635f6f26d6271e66922c45b2208f36f24373cadf6ce06c6a754935d3f`;
- lossless gzip SHA-256 `7a676445060d39fae3c10cd62cc928d871b95bb6e0703dcaf6f6bf0e810704ce`;
- frozen-source postformal rehash 7/7 exact;
- independent audit PASS/errors[];
- copied-result corruption controls 5/5 reject;
- formal invocation1/reruns0;
- model/GUI/X11/task-input/shared-runtime actions0.
