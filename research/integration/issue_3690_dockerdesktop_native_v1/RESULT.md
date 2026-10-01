# Issue #3690 — Docker Desktop host validation

## Decision: `PASS_DOCKERDESKTOP_HOST_VALIDATION_SCOPED_POSTHOC_AUDIT`

The exact final #3683 source snapshot was exercised in two fresh containers on Docker Desktop 28.5.1 (`linux/amd64`) using the immutable cached Python image in `SOURCE_MANIFEST.json`.

- Container 1: 5/5 unit tests passed, exit 0.
- Container 2: raw-only CLI exit 0; status `PASS_OFFLINE_STRUCTURAL_AUDIT`; errors `[]`; all 21 corruption controls rejected.
- CLI output SHA-256 `e2ac7b32c1da563cbcd3cbea285ac5ace4f98d43b3cb9ea046d2bf6c1adbbbc0`, byte-identical to the retained baseline.
- Six frozen source/evidence SHA-256 and Git blob identities all matched.

## Wrapper failure retained

After both containers completed, the frozen PowerShell orchestration exited nonzero at its host-side assertion because it treated a `PSCustomObject`'s `.Count` as the number of JSON map properties. The correct property count is 21, which a separate read-only posthoc verifier confirms from the immutable CLI JSON. The initial formal wrapper failure is not hidden or rewritten; the posthoc verifier and its result are separately identified. No container/test/CLI rerun occurred.

## Reproduction and artifacts

- H/T/D/C/U and limits: `PREREG.md`.
- Exact source and execution identity: `SOURCE_MANIFEST.json`.
- Frozen two-container launcher: `run_formal.ps1` (run once only; the output directory is now populated and deliberately blocks rerun).
- Preserved formal logs/results: `results/formal01/`.
- Posthoc verifier (reads outputs only, launches no candidate or Docker): `posthoc_verify.py`.
- Posthoc audit: `results/formal01/verification-posthoc.json`.
- Construction and wrapper failure history: `CONSTRUCTION.md`.
- SHA-256 inventory: `SHA256SUMS`.

## Scope limits

This confirms a finite exact source/test/CLI boundary on Docker Desktop. It does not prove arbitrary auditor soundness or XRes guard correctness. The previous OrbStack run remains separate and unchanged. No XRes/X11 formal allocation, GUI, input, game, model, or network access occurred in these containers.
