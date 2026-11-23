# Whole-repository membership recheck r175 — 2026-11-23 UTC

Complete GitHub REST pagination returned 1,640 open Issues and 404 open PRs.
The `main` ref was `acce16071b604fa8c06287d0b71d27addeccf481` before and after
the reads.

Compared with the exact full sorted arrays in r173, Issue additions/removals
were empty. PR additions were empty; PR #7760 was the only removal. Its A01
trace/HOLD packet was transferred byte-for-byte to current main by merged PR
#10511; the broader #5531 research Issue remains open. Docs PR #10512 records
the corrected coverage interpretation and evidence links.

The current-set hashes are `8ffa0fe03507328e29ced059f599f0f24a1bad1fe63afd53d6678cfcdbc647eb`
(Issues) and `9e33af2beaf1ae1093e0409316a7014766df7183132e0eb559242cd0a50b4668`
(PRs), using SHA-256 over UTF-8 compact JSON arrays of numerically sorted
integer IDs. The full Issue ID array is unchanged from r173; the full PR ID
array is r173 minus #7760. See the [machine-readable receipt](repository-inventory-recheck-20261123-r175.json)
and [r173 full-array baseline](repository-inventory-recheck-20261123-r173.json).

This is membership evidence only, not semantic triage, worktree/branch custody
reconciliation, merge readiness, or permission to bulk-close issues.
