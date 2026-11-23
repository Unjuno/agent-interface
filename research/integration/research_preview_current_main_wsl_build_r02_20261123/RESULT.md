# Current-main WSL Research Preview bundle R02

**Disposition: package construction and retained-audit pass; Research Preview acceptance remains open.**

## Frozen environment and source

- Current main: `c5fc0ee00b5fa5208088ee69004a336770336ac4` (confirmed against `refs/heads/main` before checkout).
- Host: Ubuntu WSL 24.04, Python 3.12.3, Git 2.43.0, ext4 persistent home; shallow single-branch main clone, complete non-sparse checkout, clean status.
- Frozen retained-source archive: 29/29 SHA-256 entries match; `.source` files are LF in the worktree. No host runtime dependencies were installed.

## Results

- `release/preview_bundle_v1/test_build_preview.py -v`: 6/6 pass (0.150 s).
- `build_preview.py --root <clean-main> --out <output>`: success. Checkout and extracted archive static preflight both report `PASS_LAUNCHER_BOUNDARY`; selected closure exact; 22,647 members; required files and launcher modes preserved.
- Bundle: `agent-interface-research-preview-2026-09-17+c5fc0ee00b5f.tar.gz`, 349,893,264 bytes, SHA-256 `5850fc0581a47570b542d74198450227da75e010022365f52bc496c17a1b7006`. Bundle `sha256sum -c` reports `OK`.
- Extracted package `runtime/golden-demo-v3.sh audit-retained`: `passed: true`, disposition `RETAIN`, frozen historical source count 29, zero frozen archive mismatches. The audit reports seven differences between those historical frozen files and current source; these are preserved as provenance, not treated as audit failure.

## Scope and remaining gates

This verifies current-main package construction, static launcher boundary and retained-evidence audit on WSL. It does not establish runtime dependency installation, supported-host doctor, fresh no-retry Golden run, `audit-live`, live GUI/input permissions, task effect, or runtime release readiness. No model, GUI, or live-control action occurred. Issue #58 remains open.

## Durable outputs

- `raw/MANIFEST.json`: exact builder manifest.
- `raw/bundle-SHA256SUMS`: bundle-provided checksum.
- `raw/audit-retained.json`: exact extracted-package audit response.
- `raw/builder-tests.stdout.txt`: test output.
- Bundle bytes remain in the persistent WSL build output, not duplicated in Git.
