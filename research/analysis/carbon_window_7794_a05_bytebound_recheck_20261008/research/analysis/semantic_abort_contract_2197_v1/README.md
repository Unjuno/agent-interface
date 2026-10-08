# Semantic abort contract audit (#2197)

## H — hypothesis

The six semantic-abort cases can keep physical neutralization, application-effect disposition, cleanup obligation, and authority separate.

## T — test

Run `python3 research/analysis/semantic_abort_contract_2197_v1/run_check.py`. The independent runner constructs the six frozen rows and derives agreements and violations by comparison rather than trusting the result counts.

## D — data and controls

The source anchor is the reproducible base commit `main@ce13fcc11d4a3a7fc5f44743fa2431c7272743f3`. The runner output is the independent check; the expected result records 6 cases, 6 agreements, and 0 violations. No model, GUI, input, network, live backend, or task action was invoked.

## C — competing explanations

A coherent contract may still be unusable by a model, may diverge from a real backend's release semantics, or may fail under a held-out application route. A six-row contract fixture cannot establish cleanup execution, task completion, latency, or safety in a live system.

## U — unresolved and stop

Disposition: `HOLD_PRE_MODEL_SEMANTIC_ABORT_TRANSFER`. The result is intentionally stopped before the model-facing/live-backend experiment requested by #2197. A successor should preserve this fixture, add an independent application-effect oracle and mandatory-cleanup instrumentation, then test model decisions on a held-out route.
