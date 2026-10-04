# A04 identity-guard audit v2

The one-shot pinned-container probe retained five method-case rows per arm.
Baseline A03 contextualized all four malformed source identities (owner,
intent, measurement key, and bracket key), while the guarded successor kept
those rows unscoped and retained the admitted F8 state. Both arms forwarded the
valid positive control contextually.

Audit v1 stopped because the freeze's `baseline_invocations` and
`successor_invocations` count the five method cases, while the candidate result
uses those field names for one probe process per arm. `AUDIT_V1_STOP.json`
preserves that first adjudication stop; it is not a scientific FAIL. Audit v2
validates the five raw case rows against the freeze, validates the one probe
process per arm in the candidate result, and writes an audit-only normalized
receipt to `RESULT-AUDIT-V2.json`. The original `RESULT_CANDIDATE.json` and raw
bytes are unchanged.

The three bridge tests and three v2 auditor tests pass in normal and optimized
Python, including mutations that reintroduce contextual attribution or remove
a mismatch case. Both suites and the retained-output audit pass in the pinned
network-disabled, read-only Python 3.12.11 container. This remains a
malformed-source bridge boundary test; it does not show that the real owner
emits such records.
