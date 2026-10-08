# Pre-candidate design STOP — allocation 02

Allocation `EFFECT-OVERLAP-6278-PORTFOLIO-T0-20261002-02` is stopped before formal candidate invocation. The original `FREEZE.json` and all frozen inputs remain unchanged.

## Trigger

The latest #6278 protocol explicitly requires comparing the same abstract route graph before and after exact-effect, grant, readiness and time-feasibility filters, including a negative control where apparent networked-buffering advantage disappears. Allocation 02 contains an exact-edge contention positive control and separately contains partial-effect/over-granted routes in its main library, but it does not publish that paired abstract-versus-qualified comparison. Source review after freezing therefore found a preregistration coverage gap; the suite's 11/11 construction PASS does not waive it.

## Disposition

`STOP_PRE_CANDIDATE_MISSING_FILTERED_GRAPH_NEGATIVE_CONTROL` — candidate invocations 0; independent-auditor invocations 0; formal retries 0. This is a protocol/design STOP, not a scientific FAIL, not a portfolio outcome, and not an authorization to run.

The in-memory construction diagnostic on the existing authored contention fixture showed the relevant discriminator: with the advertised partial edge treated as eligible, aggregate partial/disjoint scores are 9/8; after requiring exact effect on that same edge, they are 8/8. These are non-frozen construction diagnostics only. They are not allocation-02 formal evidence and are not to be cited as an experimental result.

The frozen sources and their hashes are retained verbatim. The paired edge-filter contrast will be specified and tested in the additive successor allocation 03 before any formal run. Docker execution remains independently held pending explicit exclusive-slot assignment on #5085 and immediate resource preflight.
