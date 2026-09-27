# Typed negative outcome contract v1 — Issue #4174

Allocation: `typed-negative-outcome-4174-20260923-01`

## H
A typed adapter using explicit evidence preserves uncertainty and retry guidance; a status/timeout-only comparator produces at least one futile retry and premature terminalization.

## T
Finite deterministic standard-library experiment. Formal corpus is generated before execution from 9 evidence families, CURRENT/STALE freshness, COMPLETE/INCOMPLETE completeness, preregistered retry-context validity, and two repetitions. Only BLOCKED admits both retry contexts; other families use REQUIRES_CHANGE. Candidate is authority-neutral. Independent auditor does not import candidate code.

## D
PASS iff every formal row matches the independent oracle, stale/incomplete/contradictory evidence is FAILED_UNKNOWN, authority_granted is always false, retryability exactly matches frozen semantics, comparator exposes >=1 futile retry and >=1 premature terminal, audit errors=[], and >=10 corruption controls reject. Formal invocation exactly once; no rerun/replacement/tuning.

## C
Authored specification fixture; intentionally incomplete comparator is not a claim about production behavior.

## U
No real GUI/model/planner/task utility, natural frequencies, latency/token benefit, or production integration.
