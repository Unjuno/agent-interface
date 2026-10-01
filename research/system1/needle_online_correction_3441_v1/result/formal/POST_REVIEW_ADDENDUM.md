# Post-review addendum — Issue #4824 / PR #4831

This addendum qualifies the original artifacts without changing or replacing the frozen source, raw trainer output, or original committed `audit.json`.

## Audit disposition

The formal disposition remains **STOP_AUDIT**. The trainer assigned B labels to held-out A, contrary to the frozen class-0 contract; the auditor reported 30 baseline errors. No model efficacy PASS/FAIL/HOLD conclusion is supported.

## Corruption-control claim superseded

The original audit JSON records 11/11 mutation cases as rejected. This count is preserved as historical output, but it is **not a valid mutation-control result**: the control used `bool(audit_core(altered))`, while the unmodified raw already yields 30 errors. Thus every mutated result is truthy even if the mutation adds no detectable error. The 11/11 claim must not be interpreted as validation of those controls. The auditor construction check is not retroactively rerun against this consumed one-shot allocation.

## Exact audit bytes and GitHub text transfer

The original local auditor output is preserved separately as `audit_local_exact.bin` (1958 bytes, SHA-256 `3ea6325e2f685fbd46d4967d28a4d9c0d4f9ccd2b8c38da5b0c486e1a8d94e34`). Its bytes are exactly the auditor-written JSON plus its terminal LF.

The existing committed `audit.json` is left unchanged. GitHub readback of that text artifact is 1960 bytes, SHA-256 `1fbf2960957464656ea2a43a636589e1f109092d149c015c670b4d0566aa41bb`, with an extra terminal CRLF. Consequently the previous byte-for-byte provenance statement does not hold for the committed text file. The binary companion preserves the exact local bytes; the differing text-transfer hash is recorded here rather than hidden or silently normalized.

The original STOP result, source, raw artifact, and audit JSON remain intact. This correction changes interpretation only; it does not authorize a rerun.
