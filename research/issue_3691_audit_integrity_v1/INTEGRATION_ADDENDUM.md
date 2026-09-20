# Integration addendum — Issue #3691 audit integrity

Current disposition as of 2026-09-21 JST. The original README, RESULT, source,
and native receipts are preserved byte-for-byte as historical construction
records.

PR #3722 later validated the exact source commit
`f823cbc77e87d2f9ff3456ddf49f2f819bbc340a` in two fresh network-disabled
containers: 8/8 tests passed in the first; a separate raw-only CLI returned
`PASS_OFFLINE_STRUCTURAL_AUDIT`, `errors=[]`, and 12/12 source-defined controls
true in the second. Immutable receipts and the source snapshot are retained in
`research/integration/issue_3691_orbstack_docker_validation_v1/` on `main`.

This was OrbStack Docker on Linux/arm64, not Docker Desktop host integration.
The Docker Desktop service/engine STOP recorded in the original result remains
accurate, and Issue #3691's Docker Desktop-specific gate remains open. The
historical `artifacts/native_audit.json` has 11 controls; the later exact-source
CLI has 12 because the frozen auditor includes `replacement_study_manifest`.
Keep those receipts distinct. No XRes formal allocation or runtime claim is
added.
