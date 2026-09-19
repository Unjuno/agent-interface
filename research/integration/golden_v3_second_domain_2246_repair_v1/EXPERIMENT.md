# Fail-closed GTK golden-v3 scorer repair

Successor evidence for #2615. This additive package does not alter the merged #2539 preflight or claim full #2492 acceptance.

## Contract

The evaluator accepts task success only when dispatch is terminal and completed; terminal release and independent cleanup succeed; the independent useful-effect receipt is exact; and no provenance contradiction is present. A stale case is accepted only when the nested diagnostic is exactly STALE_OBSERVATION and the attempt records zero consequential input and zero effect. Any failed predicate exits nonzero.

## H/T/D/C/U

- H: explicit terminal/effect/provenance gates prevent a false PASS.
- T: deterministic positive, false-effect, incomplete-release, ambiguous-refusal, and exact-stale fixtures.
- D: JSON fixtures, evaluator source hash, pinned python:3.12-slim-bookworm digest, raw case evaluations, and authoritative workflow result.
- C: all positive gates pass; all negative fixtures are rejected; exact stale provenance is required.
- U: this does not establish GTK live execution, provider/model utility, production readiness, latency, or generality.

Formal run policy: one first-result block; no rerun, replacement, or tuning.
