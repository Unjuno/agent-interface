# #6219 hash-bound publication recovery — original METHOD_FAIL retained

This is recovery of the oldest abandoned remote branch, not a new experiment.
See [REPORT.md](REPORT.md) for the transformation, reference hashes and limits.
All 14 original unreadable Git blobs are preserved in `published_blobs/` as
non-executable `.bin` evidence. The complete source tip is also archived.

Eleven readable files in `decoded_material/` match pre-existing SHA-256
references: nine from the recovered freeze's declared hash table, and the
candidate raw and audit from PR #6644's recorded digests. Three other decoded
prefixes are explicitly unbound derivatives, not asserted original bytes.
Do not treat those derivatives as a cryptographically restored freeze/receipt.

The saved 36-row raw's independent function-level audit still returns
`METHOD_FAIL`, `ORACLE_CONTRACT:case_addition`. No source/oracle/fixture is
repaired to make it pass; no formal allocation, candidate wrapper, auditor
wrapper, container, model or GUI is run by recovery. The historical candidate
and auditor counts/exit codes are not changed. Issue #6219 remains open.
