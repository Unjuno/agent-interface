# Frozen protocol and H/T/D/C/U

## H — research hypothesis

On a finite guarded sensorimotor DSL with a complete declared transition/effect
oracle, bounded equality saturation can find a lower-cost represented program
than a strict-improvement fixed-order greedy baseline while preserving every
observable contract. It must not certify optimizations that depend on deleting
freshness reacquisition, changing edit/save order, or omitting release.

## T — T0 method experiment

Three source programs: a pure ASCII `TRIM(LOWER(TRIM(input)))` chain; a
duplicate-passive-check program; and a held-out program combining that pure
chain with a world change, required refresh/freshness guard, order-sensitive
edit then save, and explicit release on both success and UNKNOWN exits.
Compare (1) source, (2) deterministic fixed-order greedy rewriting that accepts
only strict immediate cost reductions, and (3) bounded equality-closure
saturation and lexicographic extraction. Rewrites are exactly those in
`candidate.py`; costs are frozen in `fixture.json`. Exhaustively run source and
both outputs over every declared input, persisted value, starting epoch pair,
and branch. Preserve node/term count, rounds, elapsed saturation time and
extraction status. Apply three separate unsound controls: delete REFRESH, swap
EDIT/SAVE, and delete RELEASE.

## D — decision

`PASS_METHOD_SCOPED` only if the independent, separately implemented auditor
reconstructs every source/greedy/extracted trace for the full finite state
product; the e-closure completes under the frozen bound; all extracted
programs have identical value/effects/source epochs/authority/terminal
outcomes to source; all three invalid controls are rejected or uncertified;
and the held-out extracted program has strictly lower predeclared cost than
greedy with no hard-contract violation. Any changed effect, stale-action
admission, held authority at terminal, incomplete closure presented as complete,
or mismatch is FAIL/HOLD; no retry.

## C — alternative

A small explicit rewrite set or critical-path analysis may give the same
savings more simply. The greedy route may be sufficient once a commutation
bridge is made explicit; e-closure bookkeeping can cost more than the single
eliminated transform.

## U — limits

Finite authored ASCII DSL and stipulated oracle only. The equality closure is
an explicit bounded set of equivalent whole-program terms, not a production
union-find e-graph implementation. No empirical timing distribution,
application state, GUI, model, user behavior, or safety guarantee is measured.
The cost vector is a declared proxy, not observed latency. No general GUI
equivalence or production utility follows.
