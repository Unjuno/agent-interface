# A09 original invocation receipt provenance

This is the complete 15-file A09 package copied byte-for-byte from closed PR #8142 (head `db8585bfc8c9806a0c3dadf7cc95a1d160c81858`). It preserves that PR's original execution receipt, stdout, manifest, raw result, and auditor records as one self-contained package.

The A09 candidate raw result and most package files already exist on main under the canonical A09 path. Twelve of the 15 blobs are identical; the original `RUN.json`, `SHA256SUMS`, and `results/candidate.stdout.log` differ from the current-main copies. This custody copy preserves the original path-bearing receipt and stdout without overwriting the canonical package. Its SHA256 manifest verifies the files in this directory.

No experiment or auditor was rerun. The result remains the narrowly scoped synthetic fake-X construction recorded in the copied report; it is not live X11, physical input, application-effect, or game evidence.
