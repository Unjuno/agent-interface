# A09 package custody repair — 2026-10-20

Source packet: PR #8841 at exact head `04e7ddaa583fb3b120e9f3d00f3249c79c304f04`.

## Findings and changes

The original 16-entry `SHA256SUMS` had two stale entries when calculated over the exact Git blob bytes at that PR head: `results/audit.json` and `source_hashes.json`. The other 14 listed members matched. The manifest now records the SHA-256 values of those exact retained blobs. The source, test, transcript, and saved `PASS_SCOPED` audit contents are unchanged.

The saved audit checks the two frozen source identities, the test identity, and the retained WSLc transcript; it does not validate the full package manifest. Its scoped PASS therefore remains unchanged and does not imply the two package-manifest entries were correct. A fresh audit in an isolated copy extracted from the exact staged Git blobs returned `PASS_SCOPED`; its parsed JSON result matched the retained audit object. The generated audit file remained in the disposable copy.

This checkout has `core.autocrlf=true`. A local Windows run of the package test passed 4/4 under CPython 3.11.9. The first local audit invocation against CRLF-converted working files emitted `HOLD_AUDIT_MISMATCH` and rewrote only the working copy of `results/audit.json`; that file was immediately restored from the exact PR-head Git blob. No audit output or experimental raw was replaced. The package-local `.gitattributes` now keeps packet text at LF so byte-bound source/test identity checks remain valid in Windows checkouts; the two corrected manifest entries continue to bind the original exact Git blobs. All 18 manifest entries were checked against the staged Git objects.

## Scope

No WSLc/Docker command, formal candidate, or live allocation was run. The only test re-execution was the four-case source unit test described above; the saved WSLc transcript and original audit result remain immutable. The result is construction-only source-monitor evidence and does not establish a live model/game response, input release, recovery, task effect, or MAP01 completion.
