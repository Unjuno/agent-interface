# Issue #6405 T0 result — `PASS_METHOD_SCOPED`

This is the finite no-participant method-feasibility rung for the approval-sequence discrimination idea. It is not a human experiment or a security/authority result.

## Outcome

- Frozen input: nine scripted requests, identical across three arms (27 arm/request rows): static A, exact source-bound changed-field highlighting B, and bounded nonconsequential-repeat batching C.
- Candidate: one pinned-image OrbStack container, exit 0; emitted all 27 rows. Raw SHA-256: `e7c9b610315d5d221cac41a089fc83f5d476934f3a469d26eb57177a77d8b9aa`.
- Independent raw-only auditor: separate pinned-image container, exit 0; `PASS_METHOD_SCOPED`, zero errors.
- Five controls rejected: omitted field, swapped recipient, stale highlight, overbroad batch, and prior-receipt reuse.
- The denied R08 request emitted no receipt. The late scope expansion R09 referenced R01 as predecessor but required its own changed request digest and receipt. C grouped only the five eligible repeated nonconsequential requests and kept per-request scope, expiry, response and receipt identity.
- Audit output SHA-256: `e7c9b610315d5d221cac41a089fc83f5d476934f3a469d26eb57177a77d8b9aa` is the raw digest recorded by the auditor; the audit JSON file hash is recorded in `RUN.json`/`SHA256SUMS`.

## H / T / D / C / U

**H — method claim only.** A finite scripted fixture can represent identical static confirmation, source-bound highlighting of actual field changes, and bounded batching without losing exact per-request data or digest-bound receipt boundaries.

**T.** The nine-row frozen fixture was run once through candidate generation across three arms; a separately implemented auditor reconstructed it from the frozen fixture and independently checked presentation, highlights, grouping, decision controls and receipt bindings. Container invocations were one candidate then one auditor; retries 0; network disabled; read-only source/input mounts; only the designated output directory writable. Full commands and image/runtime identity are in `RUN.json`.

**D.** `PASS_METHOD_SCOPED`: all exact fields matched, B highlighted only the actual changes, C batched only R01–R05 with no group-level authority, deny/cancel controls were preserved, approved receipts bound principal/request digest/scope/expiry, the denial minted no receipt, R09 was not covered by R01, and all five corruption controls were rejected.

**C.** A strong request-bound broker digest or a concise changed-field sentence may make salience/batching unnecessary. The fixture is scripted and contains no human attention or behavior.

**U.** This result does not measure fatigue, comprehension, false approval/denial, usability, consent, actual broker behavior, safer choices, or a human benefit. It validates only finite fixture and auditor behavior. T1 remains unperformed and requires separately reviewed voluntary consent, privacy/accessibility safeguards and preregistration.

## Reproducibility and disposition

Allocation `APPROVAL-SEQUENCE-DISCRIMINATION-6405-T0-20261002-01`; base `d7e8a932da27e7f271920de409b079fedc75dee1`. See `FREEZE.json`, `fixture.json`, `candidate.py`, `auditor.py`, `results/t0-01/raw.json`, `results/t0-01/audit.json`, and `RUN.json`. This scoped method pass justifies review of the artifact, not promotion of a UI or approval policy. Keep Issue #6405 open for human-behavior evidence; do not infer that any actual user approved wisely or that the agent is authorized to act.
