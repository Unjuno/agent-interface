# Issue #6367 T0 — matched protective-adaptation method fixture

This is a finite synthetic evaluation-method test, not a MAP01, live-control,
model, GUI, safety, or performance result. It freezes nine matched policy pairs
(18 externally offered episodes) across beneficial, null, offer suppression,
late/exposure-shifted response, stale-generation, missing-occupancy,
safety-violation, and selection-trap cases.

`fixture.json` is the external offer schedule and frozen case oracle;
`events.json` is the fixed synthetic event/effect/release record. `candidate.py`
reports every scheduled offer and matched A/B contrast. `auditor.py` is a
separate raw-only implementation: it does not import candidate code. The
selection-trap report keeps the all-offer null contrast and emits no adapted-only
effect estimate. Missing outcomes cannot silently shrink the paired denominator.

See [REPORT.md](REPORT.md) for H/T/D/C/U, exact execution and scope, and
[FREEZE.json](FREEZE.json) for source and input identities. Formal CLI limits:
one candidate invocation, one independent audit after candidate exit 0, zero
retries. Unit/preflight tests are counted separately.
`FILES.sha256` covers candidate, auditor, fixture, formal outputs and report.
