# Issue #4820 — local amd64 Calc document-window result

## Disposition

**`STOP_AUDIT_OR_PROVENANCE` — no PASS claim.** The single frozen local Docker
runner completed and recorded a consistent live-unsaved edit, unchanged XLSX,
and two X11 window attribute receipts. The frozen independent auditor stopped
because the runner's parsed root-tree rows were recorded with indent 5, while
the runner/auditor incorrectly required indent 0 to identify a top-level
document-title window. No runner or audit rerun was made.

The retained raw X11 text visibly contains document window
`0x200325` (`baseline-local-amd64-4667-v2.xlsx - LibreOffice Calc`) with
`Map State: IsViewable`, and the separate VCL helper `0x20000b` with
`Map State: IsUnMapped`. This is a descriptive observation in the raw record;
the frozen decision remains STOP because the preregistered independent identity
gate did not complete.

## Measurements retained

- Live A1: `0 → 7`; `document_modified_unsaved=true`.
- Independent XLSX XML read: A1 remains `0`; post-fixture store calls: `0`.
- Workbook SHA-256 before/after/current:
  `7d28babbeb96c39b07a3b9a23538e842016f1ddef66fd5926dbea80676601afb` (identical).
- Root-tree windows: `0x200325`, `0x20000b`; both had successful xwininfo
  attribute receipts.
- Frozen auditor: `STOP_AUDIT_OR_PROVENANCE`, one error:
  `document_title_identity_or_cardinality`.
- Image: `issue3862-calc-readiness:build01`,
  `sha256:854f930b93be86111d80cca5268ee6423777ec21588de55a5fb717332993379d`,
  linux/amd64; network disabled, read-only root/source, bounded CPU/memory/PIDs.
- No GPU, network, user desktop, package install, workflow experiment, or
  retry. The original #4667 arm64 STOP remains unchanged.

## Exact retained artifact hashes

- `case01/raw.json` SHA-256:
  `9885a14af42d15553ab860bdaaf69566a0d43557cc63bf2a1741bc2039e6f659`
- `case01/audit.json` SHA-256:
  `31c3308620fdca9ce343f9a71a60fd9680c71a35f23d18b42c8dcc886a0d756f`
- `case01/baseline-local-amd64-4667-v2.xlsx` SHA-256:
  `7d28babbeb96c39b07a3b9a23538e842016f1ddef66fd5926dbea80676601afb`

The remaining question is worth a separately frozen successor only if the
document-title parser is corrected and a fresh allocation is authorized by a
new Issue. This STOP is not silently repaired or pooled with another run.
