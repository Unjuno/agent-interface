# Package integrity audit — A03 predecessor STOP

## H / T / D / C / U

- **H:** The retained A03 package's 10 SHA256SUMS entries match the bytes at its source PR head.
- **T:** Hash the 10 manifest-listed files read-only and verify the Git blob for the report against source PR #7935 head `af4c9d63336e508dfc846c79403500674339c805`. Do not run the consumed auditor or candidate; do not edit the source package or manifest.
- **D:** `STOP_PACKAGE_MANIFEST_MISMATCH`: 9/10 listed files match. The report entry expects `0ff36352f55dc44309b9b7273790667b68a17703bc1d782305189ffca23c0217`; source-head `REPORT.md` has SHA-256 `85e2811be7f4e2c020183ccc4349c81f22823572ac07947f321782b4497d07c7`. Its Git blob is exactly `0f119f0344f1d4378b23a8e04c3f8a5720fba800`, matching PR #7935's changed-file identity. All other nine manifest-listed files pass.
- **C:** Local macOS 27.0.1 arm64, CPython 3.12.10. This check is deterministic SHA-256 bookkeeping, not the formal host-Python 3.14.5 audit and not a container run.
- **U:** This does not invalidate or upgrade the recorded A03 auditor disposition; it identifies an integrity defect in the published package manifest. Candidate/runtime remains 0, the frozen audit invocation remains 1, and retries remain 0. No claim is made about physical input, application effect, or gameplay.

The source package at `research/doom/map01_v39_v15_selected_path_prepost_a03_audit_20261005/` and its `SHA256SUMS.txt` are preserved byte-for-byte. This audit records the discrepancy; it does not silently repair the manifest or rewrite a historical result.

The preserved source `RUN_RECORD.md` has seven trailing-space Markdown hard-break lines. A full-tree `git diff --check` reports these unchanged-source lines; they are not normalized because that would alter the source package. `git diff --check` on this additive integrity-audit directory is clean.

Reproduce from the repository root with `python3 research/doom/map01_v39_v15_prepost_a03_integrity_audit_20261005/audit_manifest.py`. A package-wide digest mismatch exits 1 and prints the typed STOP; a fully matching manifest exits 0.
