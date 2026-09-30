# Stable visual anchors: six-task shared API comparison

Actual source 1323d1af882d4269ce556751983214ce26a75169, seed 991298. Freeze
95b1be72a49e6764ef9cd93df36176d14fcbef09ef72c7f6a9a264d442e58b78 preceded
execution. One direct arm followed by one persistent arm, six tasks each, same
primary conversation, WSL/system Python/browser path, task schedule and scorer.
Exact provider build/config, complete environment attestation, actual tokens and
host-render/useful-feedback endpoints are unavailable. Known layouts are reused
with new values; this is not held-out domain/generalization evidence.

The prior shared-api-six-pair-01 remains failed. This new allocation prospectively
chooses observed points inside stable right borders, away from caret/text, in both
arms. Import startup is repaired; no runtime guard, wait, scoring or single-repair
budget was changed. No helper model or input replay. The primary viewed all six
direct grounding images, persistent cold/repair images, and all twelve result
images. Result reviews explicitly distinguish visible SAVED from exact values.

## Results and tradeoff

Both arms saved all six expected tokens exactly once, no missing/unexpected/
duplicate submissions. Both runners exited 0; tracked children were [0,1,0] in
each arm, not proof of full descendant cleanup. Direct has 12 completed public
programs including navigation; persistent has 18. All recorded releases are
verified with no held input. Persistent task 4 refused the old layout with zero
input and completed after one explicit fresh-image repair. No other refusal.

| Observed quantity | Direct | Persistent |
|---|---:|---:|
| Exact saved tasks | 6/6 | 6/6 |
| Primary grounding requests | 6 | 2 (cold + repair) |
| Recorded grounding wait | 96.82 s | 41.04 s |
| Public read-only captures | 25 | 70 |
| Non-repair action-to-application-feedback | 277–291 ms | 723–1345 ms |
| Task-4 action-to-application-feedback | 288 ms | 18.546 s including repair |

The persistent route reduces grounding requests while increasing local capture
work and action-to-application-feedback time. Do not substitute these timings
for model-useful feedback or pure inference. Primary acknowledgement spans
include host polling, image rendering, reasoning, commentary and publication.
Repair wait is already inside persistent task-4 action time; do not add it again.
All per-task timing rows remain in comparison.json, including repair.

## Integration decision

Keep the existing recovery budget and guard checks. Add brief model-facing
guidance to avoid blinking carets/changing text when selecting an anchor inside
the intended target. This pair shows scoped correct continuation with that rule,
not causal proof that the rule eliminated the earlier refusal. No automatic point
selection or sensor is added. The shared API has a complete six-row construction
pair here, but #2789 acceptance remains HOLD_INTEGRATION_INCOMPLETE because model/
environment attestation and required model/host timing are incomplete. No human-
tempo, token savings or universal faster-path claim.

Run python3 verify.py to audit retained hashes, exact submissions, release rows,
zero-input repair, review order, capture/grounding counts and derived timings.
