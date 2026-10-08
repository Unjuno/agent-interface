# Main advancement check before A03 freeze

- Initial A03 construction reference was db749b182224842defd6556cc82f88ac5e6448fa.
- Before formal execution, origin/main advanced to 0db00a564daff64e47fd6931954ace0f71ab8f2b (PR #8113, reverting the #59 per-key batch-boundary experiment).
- The full db749..0db00 path comparison showed a broad independent batch of main updates. The only shared path with this A03 allocation is research/analysis/README.md; A03's unique result directory and A02 source files did not overlap. The index will be edited against the rebased latest version and no existing index content will be reverted.
- The local A02 STOP commit was rebased onto the new main, producing merge-base exactly 0db00a564daff64e47fd6931954ace0f71ab8f2b. A02's original STOP evidence and frozen source hashes were not edited.
- Formal run has not started. A03 protocol/runner base constants are updated to this main SHA. The cached image was independently inspected as sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151 linux/arm64; the corrected full digest is used for A03.
