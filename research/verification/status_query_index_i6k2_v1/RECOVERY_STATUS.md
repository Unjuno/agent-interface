# Recovery status (2026-10-01)

This directory preserves the exact 11-file frozen source/gate package from
`research/status-query-index-20260926-i6k2` at commit
`672f4c149d076d7b64ebb3e6ee8c7204a8a483ba`. It is an additive research
artifact; it changes no runtime or production query path.

The Issue reports a completed 18-worker/792-query allocation and scoped
semantic and query-time PASS outcomes. The original branch head contains only
the preformal source freeze: no formal raw worker records, independent audit,
or corruption-control results are present there. The reported outcomes are
therefore historical Issue reports, not independently verified or reproduced
by this recovery. Do not infer or reconstruct missing evidence from summary
statistics, rerun the consumed allocation, or promote the candidate to runtime
use on this basis.

Validation during recovery:

- The 11 frozen files are copied from the exact original Git commit without
  modification; their original Git object identities remain available from
  the preservation tag recorded in the Issue.
- In a read-only, network-disabled `python:3.13.5-slim` container, all 7 Python
  files syntax-compiled and the 11 frozen file Git identities matched the
  original branch. The frozen unittest suite ran 12 tests: 2 passed and 10
  errored with `StopIteration` because `construction/` contains no performance
  records. This is a missing-fixture/preflight limitation, not a scientific
  FAIL or PASS; the frozen code and tests were not changed to bypass it.
- Formal raw/audit/control delivery remains HOLD pending recovery of the exact
  original bytes. No formal experiment was rerun.

This source-only recovery does not close Issue #4396 or the repository
ROADMAP. Any future evidence delivery must be additive and pass the frozen
read-only auditor and applicable exact-head checks.
