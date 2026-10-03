# Typed raw audit revision

Author worker `01a0ff33-b04b-7b51-8194-a60b82fed8a2`, FINAL-v5, 2026-10-03.
This supplements PR #6863 head `82bf35dba0c709370e18d3ccacef434818879ba5`.
The original source, `audit.py`, five v1 tests, all original raw/audits/logs and
outcomes remain unchanged. `SHA256SUMS.v1` preserves the prior complete manifest.

While applying the #6860 nonauthor review's JSON-type finding to this package,
the author found the same value-equality limitation in v1. Counts, observation
identity and result transitions could be replaced by equal-valued bool/float;
input type/representation, source pin and critical event details were not checked.
This is an evidence-gate defect, not a new runtime dispatch result. V1's reported
five corruption tests never covered these cases and remain historical checks.

The separate `audit_v2.py` imports neither runtime, producer nor v1. Its oracle
reconstructs all 150 expected rows, including input label/type/representation,
exact integer counts, result/exception, dispatched payload and critical event
order/type. Recursive comparisons preserve JSON scalar types. Shape/coverage
mistakes fail closed; metadata includes the explicit source pin. The before CLI
requires its baseline module pin; the default pin is the fixed compiled source.
This is tailored to the retained inert fixture, not a generic journal validator.

H: preserving each recorded JSON type and ordered critical event closes v1's
equal-valued aliases while retaining the original 11 failing baseline rows.
T: 5 new tests with 1236 corrupted copies: 1215 numeric aliases, 9 identity/source/
metadata changes, 5 event type/order changes and 7 malformed/coverage changes.
D: unchanged after passes; unchanged before retains exactly 11 boundary errors;
every corruption fails. Normal and optimized test runs must pass.
C/U: source/raw provenance remains a separate hash check; no formal allocation,
physical input, model, GUI, performance or reliability measurement is introduced.

Test-first copied-v1 draft: 1198 failed corruption assertions and 6 errors,
exit 1. Five errors came from malformed input shapes; one came from the new
source-pin argument being unsupported by the original function signature. The
first complete output is retained in `checks/audit-v2-red/`, with original private
bytes preserved before publication redaction. The unchanged `audit.py` is also
the exact initial copied draft source; no failing source has been lost.

Corrected v2: 5/5 normal CPython 3.11.9 and 5/5 optimized CPython 3.12.14,
both exit 0. It rejects all 1236 copied corruptions. Original before raw: audit
exit 1, 11 errors; original after raw: audit exit 0, zero errors. No producer,
runtime, archive build or consumed experiment was replayed. Original runtime
and composition results in README remain applicable because their source,
test definitions, inputs and dependencies have not changed here.

Before raw SHA-256 remains
`49351cb9f105632b08e6aa95908fb2dea4ced09d182fda9e4bf2161ff78b5546`;
after remains `6b4169b5fe325c3b3b35b1ef6507525f825f1be72fabd061e54b0c4f30e61e70`.
`V2_PUBLICATION.json` binds new auditor/tests and each original/public receipt/log.
Absolute private paths are replaced in public copies; exact original bytes were
read back privately before redaction. Five new command/UTC/exit/log receipts are
under `checks/audit-v2-*/`. Derived receipt cwd is attributed to the retained runner.

```text
python -B -m unittest discover -s research/integration/compiled_admission_sequence_57_20261003_01a0ff33 -p test_audit_v2.py -v
python -B -O -m unittest discover -s research/integration/compiled_admission_sequence_57_20261003_01a0ff33 -p test_audit_v2.py -v
python -B research/integration/compiled_admission_sequence_57_20261003_01a0ff33/audit_v2.py research/integration/compiled_admission_sequence_57_20261003_01a0ff33/after.json --output <fresh-output>
```

This evidence-content revision supersedes the v1 proposal digest for future votes.
No vote on an earlier head applies automatically. Reviewer identities and all
existing comments/objections remain visible; a new immutable proposal will be
published outside the proposed source tree after final readback. Nonauthor
consensus, exact current-main combination and conditional application remain.
