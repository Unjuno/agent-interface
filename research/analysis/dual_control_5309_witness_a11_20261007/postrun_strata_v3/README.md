# A11 post-run strata successor V3

This is a separate, one-shot read-only diagnostic allocation created after review found that V2's source/freeze/result provenance was rewritten after a completion had already been recorded. V2 artifacts and the formal A11 result are preserved as-is; this V3 does not adjudicate whether V2 executed as claimed.

V3 reads only the frozen A11 candidate input, choices, raw rows, and oracle. It does not run the candidate, environment, or formal auditor. The diagnostic allocation ID is distinct from the source workload allocation. Its sole purpose is to reconstruct the descriptive strata from retained bytes and keep that post-hoc result separate from A11's formal `FAIL_AUDIT_MISSPECIFIED_STRATUM_GATE`.

See `FREEZE.md` for H/T/D/C/U, exact source hashes, and the one permitted command. No execution is authorized until the freeze is committed and independently checked.
