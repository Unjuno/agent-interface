# r87 exact Git blob custody follow-up — 2026-11-04

After PR #10185 merged at `85193c48ad4ffa307425939e26633c689d5db144`, a clean checkout failed the r87 custody verifier only for the source attempt manifest (`r87-c11/SHA256SUMS.json`) and the root `FREEZE.sha256`. The r87 correction manifest records their expected raw SHA-256 values. The preserved PR worktree contained exact matching bytes for both; clean main had the LF-normalized tracked blobs.

Copied the two hash-verified original byte sequences into this follow-up branch. `.gitattributes` marks the r87 tree `-text`, so Git records these files byte-for-byte. The verifier now reports `PASS_CUSTODY_MAP`: 227/235 verified original bytes, one available mismatch, seven unavailable. This fixes reproducibility of the metadata checks; it does not recover those eight files or change r87's failed 591-pixel full-frame digest gate.

The original file contents and checksums are unchanged; only their line-ending bytes were restored. No runtime behavior or experiment result changed.
