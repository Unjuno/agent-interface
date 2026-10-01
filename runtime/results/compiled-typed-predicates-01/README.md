# Integrated graph scalar predicates

The current graph accepted `true` for integer `1` and `false` for integer `0`
under Python equality. This could select an action/completion branch and certify
an expected effect under the wrong scalar meaning. The guarded adapter then sent
the second fixture action and returned TASK_SUCCEEDED. This is a concrete #52/#55
correctness blocker in the #57 integrated path, not another compression idea.

Branches and expected effects now require matching type and value. A branch
mismatch stops as unknown_state before admission/input. An effect mismatch stops
as effect_failed, retains the actual completed prefix and pending effect, and
never calls the verifier or another action. Same-type bool/int/string behavior,
unknown evidence, ordinary authority checks, deadlines and release are unchanged.

RED: 49 tests ran, 13 failing subcases (8 branch, 4 effect, 1 guarded adapter).
GREEN: 49 tests normal and optimized Python. Shared local CI: protocol 383 and
harness 183. Core contracts 65; CLI plus portable distribution 126; private Xvfb
X11/backend boundary 55. Groups overlap; do not add them as unique test counts.
Full logs and CI result hash links retained. tested-source.json identifies the
working-tree source used for these runs. Python 3.12.3, Ubuntu 24.04.4, WSL3.0.1
package / WSL2 execution, kernel6.18.40.1. Shared Node host source did not change.

The first archive build ran before committing and correctly pinned old main
279679a33f6029c6e13eca6be51890d8bebb25e7. initial-build retains that old artifact,
manifest and sums; it does NOT verify this fix. Rebuild from the source commit
and exercise the typed predicate boundary in an isolated archive before publish.

No model invocation or live application trial is allocated here. The X11 tests
exercise backend contracts, not end-to-end live semantic completion. No speed,
token, cost or human-tempo gain is inferred. The trusted perception/effect
callbacks, matched assistance and finite cold/warm/invalidation/repair comparison
in desktop-composition-admission-01 remain unresolved/unallocated. New #6231
same-schema effect-drift work is synthetic T0, not product adoption evidence.

Final portable artifact pins source commit `06a9a3e44` and passes 15 deterministic
branch/effect/control cases under isolated `python -I` from /tmp. archive-probe.json
records outcomes and archive hash. Archive core source bytes equal tested source;
shared CI log SHA links and tested-source hashes were verified before publication.
This probe uses the same finite fixture contract as unit tests and is not an
independent task oracle. Initial host bundle is retained with its initial manifest.

Additional review/static/replay checks: first invocation ran 24 checks but one
replay import failed because the tracked test was not materialized in the sparse
checkout (25 entries including loader error). Preserve that log. Materialized
only the exact tracked test from HEAD, then the complete requested review/static
validator/replay set passed 36 tests. No runtime source or old evidence changed.
Remote base meanwhile advanced to fe37b6913 via unrelated research-only paths;
no overlap with this runtime closure. Hosted jobs are queued at publication,
so local evidence is the merge basis, not a claim of complete hosted green CI.
