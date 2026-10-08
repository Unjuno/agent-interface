# Decision-policy cache action guard R0

Parent: #1155. Allocation: #1163.

## H
A low-rate cached-policy supervisor can miss a hard-invalid state that begins and ends between samples. Binding every consequential cached-policy action to current deterministic evidence will prevent stale/ambiguous effects even when the supervisor misses that transition.

## T
Compare per-cycle re-decision, cached supervisor-only reuse, and the same cached reuse plus action-time current guard on identical 100 ms synthetic timelines. Formal: 250,000 scenarios, seed 2026091801, action cadence 5 ms, supervisor cadence 20 ms, one between-sample ambiguous window, one between-sample transient hard-invalid window, and one later persistent hard invalidation. Standard library only; no external action or authority.

## D
PASS only on zero reference/guard oracle mismatch, zero guarded hard-invalid/ambiguous effect, >0 supervisor-only stale hard-invalid effect, no valid-continuation mismatch before the first hard-invalid action, exactly one semantic decision per cached scenario, zero authority grants, source/audit integrity, mutation-control detection, invocation1/reruns0.

## C
This isolates guard placement, not real evidence acquisition cost. A supervisor may still improve early invalidation or switching. A positive result is not a token, wall-time, production-runtime, or live planner-gap claim.

## U
Synthetic state machine and deterministic timing only. Next rung, if any, should measure current-evidence acquisition and stop latency in a controlled live fixture before introducing learned supervision.
