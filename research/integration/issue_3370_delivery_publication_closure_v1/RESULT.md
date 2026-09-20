# Issue #3602 — delivery-pair publication closure audit

## H / T / D / C / U

**H.** The merged #3599 task auditor may reproduce both task-scoped PASS rows
without checking whether every path claimed by the evidence manifest is
publicly available. A separate inventory auditor should distinguish task-gate
reproduction from publication closure and fail closed on missing, changed,
unlisted, or unsafe paths.

**T.** Read-only audit of #3599 merge `e3d04078d8d6d09fe3a3e33456b144c3d892adee`.
The committed `evidence/manifest.json` has SHA-256
`ca19dd840352d50f7b2d2512661ceeedaee17af3aa1a50f1f90aed62f4d0533f` and 99
rows totaling 1,458,438 declared bytes. Fetch every row from that immutable
commit and compare exact length/SHA-256. Run the original pair audit against
the available evidence separately. Do not rerun either GUI task, MCP client,
model, or input; do not alter #3599's manifest or audit output.

**D.** The added closure auditor returns
`PASS_PUBLICATION_CLOSED` only for a one-to-one inventory with matching bytes
and digests. On the frozen #3599 evidence it returns `HOLD_PUBLICATION_GAP`:
93/99 available files match; six paths are missing. The original pair auditor
still returns `PASS_BOTH_DELIVERY_PATHS_TASK_SCOPED` with zero failures when
run against the 93 available files. These are separate gates, and neither
result overwrites the other.

**C.** Evidence commit fixed at #3599 merge
`e3d04078d8d6d09fe3a3e33456b144c3d892adee`; evidence subtree is unchanged at
main `cf0be811a56785ce29864456c13556f3271655cf`. Only a new read-only auditor,
synthetic contract tests, and this receipt are added.

**U.** This is publication-integrity evidence only. It does not invalidate the
task-level pair PASS, establish host/model visibility, add replicates, measure
latency/cost/efficiency, or close #3370. The six original log bytes were not
available from either the merged commit or PR head, so this work cannot
restore them. Resolve by publishing their unchanged bytes or explicitly
scoping them out in an additive inventory while preserving the historical
manifest and audit.

## Missing paths

All six paths match the repository-wide `.gitignore` rule `*.log` and return
HTTP 404 from both PR head `4c9cf2079f2b5f8d4b348207eb2777e44b003949` and merge
`e3d04078d8d6d09fe3a3e33456b144c3d892adee`:

- `evidence/direct_mcp_image/allocation/stderr.log` (0 bytes)
- `evidence/direct_mcp_image/allocation/stdout.log` (921 bytes)
- `evidence/direct_mcp_image/mcp-stderr.log` (216 bytes)
- `evidence/saved_file_view_image/allocation/stderr.log` (0 bytes)
- `evidence/saved_file_view_image/allocation/stdout.log` (931 bytes)
- `evidence/saved_file_view_image/mcp-stderr.log` (216 bytes)

The pair auditor does not read the manifest. Reconstructed independently from
the 93 published files, it reports both original start-image hashes
`505c17b695d2c4a71b8ae5b0e52a1c90261d25764ca4d3ae9b19b2933e1abec9`,
`PASS_BOTH_DELIVERY_PATHS_TASK_SCOPED`, and `failures=[]`. The publication
auditor independently reports `HOLD_PUBLICATION_GAP`, 99 entries, 93 matches,
six missing, zero mismatches, and zero unlisted files.

## Verification

- `python -m unittest -v test_audit` — 8/8 passed. Cases cover complete
  closure, missing files, digest drift, unlisted files, parent traversal, and
  duplicate paths, invalid schema, and refusal to write inside frozen evidence.
- `python audit.py --bundle <frozen-evidence> --output <separate-receipt>` —
  expected exit 1 with `HOLD_PUBLICATION_GAP` on the frozen public tree.
- Frozen #3599 `audit.py` run on the same 93-file reconstruction — exit 0,
  `PASS_BOTH_DELIVERY_PATHS_TASK_SCOPED`, zero failures.
- `git diff --check` — clean.
- No container, model, GUI, MCP allocation, or input was run. Downloaded raw
  evidence and generated receipts stayed in a temporary directory.
