# Recovery status — save-query reconciliation (#4309)

Recovered from remote branch
`research/save-query-reconcile-2869-20260924-q9b2`, tip
`b45cbc45fbf2cc427da4c35fe857a57fee74b699`. The 17 original files are retained
byte-for-byte under this recovery path: the freeze, complete source capsule and
restorer, plus the nine evidence fragments present at that branch tip.

## Source and evidence recovery checks

- The source capsule restored 10 files and matched its declared archive
  SHA-256 `91260d4ae9f8d43ade96b150235916c5c87a44a43e3442928b287d60afbf36b3`.
- Source policy unit tests passed 16/16; Python syntax and JSON parsing passed.
  These are source/recovery checks, not a rerun of the consumed allocation.
- The nine `EVIDENCE_00.b64`–`EVIDENCE_08.b64` Git blobs match the old branch
  exactly. Removing only each chunk's final LF yields 54,000 Base64 characters
  and 40,500 decoded bytes. XZ decompression stops with
  `Compressed data ended before the end-of-stream marker was reached`.
- No evidence-specific manifest, complete archive length/hash, member set, or
  evidence restore/audit entrypoint exists in the recovered branch. The part
  byte identities preserve these fragments only; they are not a scientific
  archive manifest and do not establish completeness.

## Scientific disposition (unchanged)

Issue #4309 reports a consumed 16-session formal allocation and the historical
`PASS_SAVE_QUERY_RECONCILIATION_SCOPED` outcome (1,155 raw-audit checks,
`errors=[]`, and 12/12 copied-evidence controls). Because the full raw package
cannot be restored, this outcome remains reported but is not independently
re-auditable from the recovered bytes. Recovery disposition:
`HOLD_EVIDENCE_INCOMPLETE`.

Do not reconstruct raw rows from the Issue summary, edit the historical
outcome, or rerun the consumed allocation. Issue #4309 remains OPEN pending
recovery of the exact complete original evidence package. This recovery changes
no runtime code and makes no production, durability, authority, latency, or
product claim.
