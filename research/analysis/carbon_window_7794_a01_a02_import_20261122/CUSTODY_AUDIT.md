# Issue #7794 A01/A02 evidence custody import — 2026-11-22

## Source and transfer

This additive packet transfers eight unique files from Draft PR #7968's exact
head `338e6e8facf1dbdc94c7e3f0c41743945cadf4de` into their original
`research/analysis/carbon_window_7794_a01/` and `_a02/` paths. Neither folder
existed in current main `dc31debe1a25b887fc688e5543417ce908a51095` before this
transfer. The two per-folder `SHA256SUMS` files were added without changing
the original eight file bytes. `.gitattributes` marks both folders `-text
-whitespace` so Windows checkouts do not rewrite hash-bound evidence bytes.

The original PR remains OPEN/Draft. Its listed `replay-gate` and
`analysis-index` checks pass; formal is skipped; it has no submitted reviews
and GitHub reports mergeability UNKNOWN. GitHub compare reports two PR commits
and 3,880 current-main commits from the reported comparison (diverged, no merge
base in the response); this repository's clone is shallow, and local
`merge-tree` could not resolve a common base. The transfer preserves its data
without treating the stale Draft as merge-ready. The PR and its comment remain
the provenance record.

## Byte audit

The eight files were read as raw Git blobs from the PR head. Their SHA-256
digests are recorded in the two manifests. Before staging, each original file
digest matched the `git show origin/pr-7968:<path>` bytes. After staging, verify
each Git blob ID against the exact PR-head path; the `-text` attributes preserve
those bytes across Windows checkouts. The candidate and auditor were not run.

## Scope retained

- A01 `PASS_METHOD_SCOPED` applies to a deterministic three-job scheduler
  model with fixed energy and synthetic intensity; it makes no operational
  emissions claim.
- A02 `PASS_METHOD_SCOPED` applies to the finite nine-case synthetic replay.
  Its frozen protocol calls one comparator serial ASAP, while the candidate
  chooses the lexicographically earliest globally feasible assignment. The
  nine cases do not distinguish them. Preserve A02 and its first result;
  later A04/A05 records supply the fixed discriminator and byte-bound replay.
- A04 remains unchanged with its own metadata digest mismatch. The current-main
  A04 manifest audit found 8 of 14 entries differ from checked-in bytes. A05
  reconstructs four execution inputs as the exact A04 Git blobs plus one final
  LF and passes its own finite replay; a separate read-only current-main audit
  verified all 12 A05 manifest entries. A05 does not repair A04's
  `FREEZE.json`/preregistration hashes or retroactively validate A04.
- Child Issue #8386 is CLOSED at its byte-bound replay scope. Parent Issue
  #7794 remains OPEN at `HOLD_ACCOUNTING`: no owner-approved representative
  workload, metered energy, time/region carbon factor, or operational boundary
  establishes the proposed emissions result. Do not delay runtime or user
  work based on these synthetic schedules.

This is an evidence-custody transfer and read-only digest audit, not a new
candidate/auditor run, container/WSLc experiment, or issue closure.
