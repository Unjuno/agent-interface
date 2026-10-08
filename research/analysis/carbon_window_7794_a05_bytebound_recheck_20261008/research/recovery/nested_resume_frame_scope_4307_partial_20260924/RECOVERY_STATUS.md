# Recovery status — nested-frame resume (#4307)

Recovered from remote branch
`research/nested-resume-frame-scope-4222-20260924-c7e4`, tip
`06ccaa7e436944c43aabc6f162186a9a5a105a94`. The old branch name says #4222,
but the PLAN, REPORT, and source metadata identify the distinct #4307 allocation
`nrs4307-c7e4-formal01`.

## What is preserved and verified

- The original 11 files (PLAN, REPORT, three source-capsule chunks, source
  metadata, and five formal-evidence chunks) are retained byte-for-byte under
  this recovery path.
- Concatenating the three SOURCE chunks, base64-decoding, and checking the
  compressed source archive gives the declared SHA-256
  `9d39d91744de2b74a8ac01a5612624401be882bdaa163228d9664e0bb3534c25` and 13
  safe `source/` members.
- The branch tree and all-ref history contain only
  `EVIDENCE.00.b64` through `EVIDENCE.04.b64` (five 10,001-byte chunks). The
  declared 22-part formal evidence stream cannot be reconstructed from them.
  A bounded all-ref path search found no later parts. The current GitHub Actions
  artifact inventory produced no matching #4307/nested-resume run; two numeric
  name-search false positives were checked and belong to unrelated branches.
  This does not prove absence from every offline archive.

## Scientific disposition (unchanged)

REPORT.md records the owner's historical `PASS_NESTED_FRAME_RECHECK_SCOPED`
claim for 48/48 sessions, 8,286 raw-audit checks, and 14/14 corruption controls.
Because the formal evidence stream is incomplete, that claim is **reported but
not independently re-auditable from this recovery package**. The recovery
disposition is `HOLD_FORMAL_EVIDENCE_INCOMPLETE`; it neither changes the
historical report nor promotes its PASS.

The separate three-case Docker construction revalidation in PR #4581 is not a
substitute for the consumed 48-case formal allocation. Do not rerun, continue,
or synthesize missing formal rows. Issue #4307 remains OPEN pending recovery of
the exact remaining evidence or an explicit final STOP/HOLD disposition.

This is source/report/partial-evidence preservation only. It changes no
runtime code and makes no broader GUI, platform, authority, model, latency,
or product claim.
