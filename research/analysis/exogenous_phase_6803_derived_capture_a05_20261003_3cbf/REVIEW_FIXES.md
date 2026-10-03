# Post-run verification hardening, no formal rerun

The independent read-only reviewer checked initial result head
`dfef1c8a3f169dd69da3263f155ec1703e7b003c` against main
`66822a57d2bc05082c6b82aa0b02bf7762dba98b`. The reviewer independently
reconstructed all 147 rows, both contrasts, ten mutants, four legacy probes,
seven staged hashes and sequential runtime records. The finite result and
scoped claims were supported; no critical scientific-result issue was found.
Merge verdict was WITH FIXES for two important automated-verifier gaps.

## Important gap 1: immutable publication binding

The original verifier compared current sources against current FREEZE_02.json,
but did not directly compare that freeze/source set with Git objects at the
published allocation-02 commit. A rehashed post-freeze amendment could pass.
The reviewer demonstrated this without changing the checkout.

The revised verifier now byte-compares both retained freeze files with their
respective historical commits, and every allocation-02 bound source with Git
commit `4b3da15ca4dbb4720e173475174c3a6c77169176`. CI explicitly fetches both
published source commits. The regression changes 512MiB to 1GiB in a real
temporary copied preregistration and rehashes its copied freeze; verification
must reject it even without relying on the outer manifest.

## Important gap 2: semantic custody/summary consistency

The original verifier did not parse STAGING_02, compare retained RUN with the
reconstructed summary, or validate the consumed allocation identity. Rehashed
metadata could incorrectly describe source isolation, row count or live effects.
Actual retained records were independently checked and found consistent.

The revised verifier checks exact role paths/file allowlists/staged digests,
staging image/source/allocation identity and output ownership; compares RUN by
type-sensitive canonical JSON with reconstructed raw/audit/runtime metrics;
checks consumed identity, three distinct container IDs, and sequential launch/
container/finish chronology. Real copied-file regressions cover an extra
candidate audit.py, a wrong staged digest, RUN claiming 999 rows/live effect1,
a wrong consumed allocation and a receipt finish preceding launch.

## Minor control clarification

The frozen boolean-time-alias mutant changes delivery 11 to True. It is a valid
corruption and remains rejected, but does not itself test the equality alias
1==True. The new post-run test changes echoed onset1 to True: ordinary structure
equality accepts the alias, while the frozen canonical auditor rejects it.
No original mutant, candidate, fixture, auditor or scientific test is changed.

## Observed red/green and preservation

The eight new post-run review tests first produced six failures (the six missing
rejection behaviors); the existing positive-data and genuine-alias checks
passed. After the first publication-binding fix, five failures remained. After
the custody/summary/chronology fix, all eight passed; the whole package passed
22/22 tests. Formal invocation counts remain 1/1/1 with no retry. No VM restart,
container launch, science retuning or formal output modification occurred.

Original REPORT.md, RUN.json, source freezes, formal raw/receipts/mutants and
MANIFEST_SHA256.json remain unchanged. The first manifest describes initial
result commit dfef1c8a3; its original post-run helper hashes are historical.
The additive MANIFEST_SHA256_REVIEW.json covers the revised verifier/tests,
this supplement and every retained file, including the original manifest.
The safe default verify_evidence.py selects the review manifest when present.
Source/inputs/outputs are independently checked against the immutable formal
freeze, not promoted by regenerating a package manifest.

The previous 14-test/96-target result remains a historical first verification,
not silently replaced. Local full Analysis Index 25/26 commands with two
disclosed provenance assertions also remains verbatim; actual first PR Actions
passed all eight applicable checks plus one out-of-scope formal skip.
New-head actual CI and non-author follow-up review are required before merge.

This hardening affects evidence delivery only. PASS_METHOD_SCOPED and
HOLD_LIVE_TRANSFER are unchanged; no real-world claim or #57/#59 completion.
