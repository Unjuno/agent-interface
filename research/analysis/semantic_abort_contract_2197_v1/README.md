# Semantic abort contract audit (#2197)

## H — hypothesis

The six semantic-abort cases can keep physical neutralization, application-effect disposition, cleanup obligation, and authority separate.

## T — test

Run the frozen six-case read-only fixture in `RESULT.json`. The fixture checks that release-only neutralization is not semantic abort, unknown/stale evidence causes query or abort, and cleanup remains mandatory for an active resource.

## D — data and controls

The source anchor is `main@0ef20cd93b6656f737c9521f7aa0eb0c80ce58f3`. Independent checks are explicit in the result. This v1 was prepared as a contract-level artifact; no model, GUI, input, network, live backend, or task action was invoked.

## C — competing explanations

A coherent contract may still be unusable by a model, may diverge from a real backend's release semantics, or may fail under a held-out application route. A six-row fixture cannot establish cleanup execution, task completion, latency, or safety in a live system.

## U — unresolved and stop

Disposition: `HOLD_PRE_MODEL_SEMANTIC_ABORT_TRANSFER`. The result is intentionally stopped before the model-facing/live-backend experiment requested by #2197. A successor should preserve this fixture, add an independent application-effect oracle and mandatory-cleanup instrumentation, then test model decisions on a held-out route.
