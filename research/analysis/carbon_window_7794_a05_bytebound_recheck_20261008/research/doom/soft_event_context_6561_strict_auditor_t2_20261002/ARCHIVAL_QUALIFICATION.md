# Archival qualification — T2 provenance HOLD

The original `REPORT.md`, candidate/audit receipts, source, inputs, and
manifests are preserved unchanged. The original report claims
`PASS_T2_STRICT_AUDITOR_SCOPED` and `PASS_INDEPENDENT_RAW_AUDIT`; this archive
does **not** validate those claims.

On the exact submitted PR #6603 Git blobs, all 12 entries in
`PRE_RUN_SHA256SUMS` and all 4 entries in `EVIDENCE_SHA256SUMS` fail
`shasum -c`. Representative mismatches remain after trying LF-to-CRLF
reconstruction: `T2_SPEC.json` is `7066fba9...` versus recorded
`8DED5013...`, and `candidate_result.json` is `db666130...` versus recorded
`029A6101...`. The pre-run manifest also contains mixed line endings and an
improper blank line. These are unresolved content/provenance mismatches, not a
scientific reclassification or evidence that any particular file was
deliberately altered.

Separately, the frozen auditor checks candidate-reported decision receipts
rather than independently recomputing the six decisions. The documented
posthoc reconstruction matched those receipts, but its checker stopped on an
over-specific host-description string; it was not a passing replacement
auditor. Do not rerun the candidate, promote either PASS label, or use this
package as decision-verified evidence. The distinct WSLc T0b package (#6609)
remains separate. Issues #6561 and #59 stay open; no live controller, game,
model, GUI, task effect, or production authority claim follows.
