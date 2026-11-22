# Windows current-main Research Preview builder R01

**Disposition: HOLD; no distributable artifact produced.**

## Conditions

- Frozen current-main source: `39cbd0d202db82baf4886f1d781461909c4f706a`.
- Host: Windows PowerShell, CPython 3.11.9, `core.autocrlf=true`.
- Existing checkout was intentionally sparse. No dependency installation, WSL, GUI, model/provider, live golden run, or `audit-live` was performed.
- Builder tests: `python release/preview_bundle_v1/test_build_preview.py -v` — 6/6 passed in 8.727 s. This validates builder fixtures, not host acceptance.

## Results and preserved failures

1. Initial build to `%TEMP%/agent-interface-preview-r02-20261123` stopped with `BUILD_FAIL: retained frozen source bytes do not match preregistration: run_integrated_efficiency_live_v1.py`.
2. The tracked frozen-source manifest has 29 entries. The Windows working bytes mismatched 26 entries due CRLF checkout materialization (`git ls-files --eol` showed index LF / worktree CRLF); immutable `origin/main` blobs matched the frozen manifest. Restoring each mismatching file from its exact current-main Git blob returned all 29/29 archive hashes to the manifest. No logical source content changed.
3. A follow-up builder invocation to `%TEMP%/agent-interface-preview-r02c-20261123` exited 2: clean sparse checkout lacks 22 tracked files selected by the release closure (including `LICENSE`, `SECURITY.md`, and the golden/offline/preview readiness trees). This does not establish a builder defect; the checkout is incomplete for that operation.
4. A disposable full-worktree attempt inherited sparse-checkout state and was safely detached from Git registration after initialization failed. Its local residue is 19 files, all hash-identical to `origin/main`, under the current worktree `.worktrees/preview-release-current-main-r02-20261123`. Automated review rejected recursive cleanup; leave this isolated residue for explicit later cleanup. No other worktree was touched.

## Interpretation

The frozen-source mismatch was a Windows working-tree byte-normalization issue, not a changed frozen source. After correcting it, the builder correctly refused to build from a sparse checkout with missing selected files. No current-main Windows archive was built. Prior WSL R06 build/audit evidence remains valid only for its recorded source and host; it does not convert this attempt into a pass.

## Next finite step

Run the same builder once from a complete, clean current-main checkout configured to preserve `.source` bytes, then retain archive hash/audit output. Do not install host runtime dependencies or consume the fresh no-retry live run as part of this package-only step.
