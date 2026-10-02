# Issue #6009 T0 — online route-state switching costs

Allocation: ROUTE-SWITCHING-6009-T0-20261001-01
Preparation base: b2e7221c3c374cacc7037515f2df1508e965ac81
Scope: deterministic finite method test; no runtime or live-interface changes.

## H — hypothesis
On a fixed safe task sequence with directed route-transition costs, one-step
switching-aware selection will complete the same exact effects at a lower total
transition-plus-service cost than service-greedy and fixed-sticky selection.
A separate sequence with binding expiry will show that an ineligible route is
not continued and an alternate proven route can preserve completion. No general
superiority or competitive-ratio claim is made.

## T — test
Use three abstract routes (A direct, B guarded, C cached), five short sequences,
asymmetric directed costs, an unknown terminal horizon at each online decision,
an expiring binding, high-cost terminal handback, one deadline refusal, and a
fast route with UNKNOWN effect proof. Compare service-greedy,
sticky-with-safe-fallback, and one-step switching-aware selection. Every
attempted decision costs one abstract unit; successful transition/service,
refused attempts, and terminal handback are separately charged. The chooser sees
only the current task and current route. A rent/compile comparator is not
applicable: C is already available, with no acquisition/compile lifecycle in
this frozen model. An independent auditor replays choices and charges, computes
a hindsight exact dynamic-programming reference, and tests four corruptions:
omitted transition charge, future-task leak, UNKNOWN binding use, and choosing
speed over missing effect proof.

## D — decision
PASS_METHOD_SCOPED only if the independent replay agrees for all attempted tasks
and terminal handbacks; no unknown route/proof is selected; completed effects
are exact-once; all four corruptions are detected; the alternating sequence
strictly favors switching-aware over both comparators; binding expiry completes
by a proven alternate; and the DP reference is reproducible. FAIL_METHOD on an
accounting disagreement, future information, forbidden effect, or missing
crossover. HOLD_COST_UNIDENTIFIED if a cost is unknown; never impute zero.

## C — competing explanations
Per-task greedy may suffice for one-shot routes; sticky reuse may win on
persistent task families; direct control may remain preferable whenever another
route lacks effect proof.

## U — limits and stop
Costs are abstract units, not milliseconds, tokens, or real GUI work. The DP
sees the complete sequence and is not an online policy. No theorem, live route
eligibility, correctness, GUI outcome, or product benefit is established. One
candidate and one separate raw-only audit; no retry.

## Execution note
Docker Desktop service was Stopped/Manual at preparation, and desktop-linux
server was unavailable in the earlier bounded check. At experiment preparation,
the shared CPU container interval was owner-bound to another task. This is a
host-only method test, not a container reproduction; no container was started,
queried, or modified by this run.
