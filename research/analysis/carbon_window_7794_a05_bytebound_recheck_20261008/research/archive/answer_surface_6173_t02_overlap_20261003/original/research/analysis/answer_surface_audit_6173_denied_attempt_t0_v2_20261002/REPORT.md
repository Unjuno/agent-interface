# Issue #6173 T0 successor 02 result

## Disposition

**PASS_METHOD_SCOPED.** The 13-case synthetic candidate and a separately
authored raw-only auditor agreed on every frozen classification. Candidate:
one invocation, exit 0. Auditor: one invocation, exit 0, zero errors. Formal
retries: zero.

The confirmed T0-01 defect is repaired at this bounded method layer:
denied_oracle is ATTEMPT_BLOCKED, distinct from a fully monitored
no_attempt_complete (NO_ORACLE_ACCESS_OBSERVED). Direct returned oracle
bytes and mixed legitimate/oracle access are EVALUATION_ORACLE_REACHED;
known oracle derivative bytes are POSSIBLE_DERIVATIVE. Allowed task and
documentation returns remain AUTHORIZED_TASK_EVIDENCE. Missing monitoring,
unknown destination/recipient, and unbound return evidence are
UNKNOWN_ACCESS. A CLEAN self-claim cannot override observed oracle bytes,
and a CONTAMINATED self-claim alone cannot create an access finding.

The independent audit cross-checks candidate input events against the
observer-side trace and validates candidate invocation count, allocation,
source-main identity, and input digest. Its mutation tests reject a collapsed
denied attempt, false-clean/false-contamination classifications, candidate
input drift, duplicate rows, forged provenance, and unexpected case inventory.

## Construction and provenance

The final frozen construction suite passed 15/15; py_compile and all package,
fixture, predecessor, and output hash checks passed. During test-first
development, an initial RED run occurred before candidate.py existed. A
subsequent run had four failures because test-helper traces omitted recipient
identity; the helper was corrected before freeze, then the complete suite
passed. These are construction history, not extra formal candidate/auditor
runs.

The candidate and observer fixtures are pinned by FREEZE.json against main
69a1bf509eb432e5e3c0c294d05ad7671d86adb6. The prior Issue #6173
METHOD_FAIL_AUDIT raw and audit-only adjudication remain untouched. One
unrelated OrbStack container was active at the preflight snapshot; no
container was created, entered, stopped, inspected, or modified. This
CPU-only scope follows Issue #6173's finite T0 design.

## Scope limits

This is synthetic finite-method evidence only. It is not evidence that a real
scored run accessed an oracle, that production monitoring is complete, or that
semantic inference and unlogged derivatives can be detected. No real answer,
model, user data, GitHub/web lookup, network, app, GUI, or physical input was
used. Real benchmark integrity and end-to-end effect remain untested.
