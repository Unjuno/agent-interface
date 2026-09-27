# H/T/D/C/U — Issue #4174

H: explicit evidence-backed typed outcomes preserve uncertainty and bounded retry guidance; a coarse status/timeout-only comparator exposes futile-retry and premature-terminal counterexamples.

T: 9 families x 2 freshness x 2 completeness x 2 retry contexts x 2 deterministic repetitions = 144 formal rows. One formal invocation after source/corpus freeze. Standard library only; no GUI/model/provider/network/input.

D: PASS only with 144/144 oracle agreement, zero authority grants, all stale/incomplete rows FAILED_UNKNOWN, identical retry only for complete/current BLOCKED rows whose retry context allows it, comparator >=1 futile retry and >=1 premature terminal, audit errors=[], >=10 rejecting mutations, formal1/reruns0/replacements0/tuning0.

C: authored finite contract truth; comparator is deliberately incomplete and not alleged to be production code.

U: real application evidence extraction, planner/model comprehension, task/tokens/latency/cross-domain value remain untested.
