# Evidence rescue status — 2026-10-09

This is an evidence-only copy of the saved plan, result, test streams, and independent audit from closed-unmerged PR #8137, head `6be323b3f3ccb7c94f2bd684864e246eab8e6914`. The original PR commit remains the canonical source for the exact code/test diff and original full manifest. The auditor is stored with a `.py.txt` suffix as inert source material; it was not run during this rescue.

`RESCUE_SHA256SUMS` covers only the files copied into this archive. It intentionally does not reuse the original `SHA256SUMS`, whose entries also bind the modified active projector and test paths that this documentation-only PR does not replace. The closed PR preserves those exact versions and its original manifest.

The finding is synthetic schema-boundary evidence on historical main `19a6b723e58ccfd2b8265e88659589ef9223fcc9`. It is not a claim about live key release, application effect, game behavior, or current main. The broader exact-int/identity repair is open Draft PR #8139 with zero submitted reviews; current main's attempt ordinal comparison still lacks an exact-type guard. This rescue neither adopts a code patch nor repeats the original test.
