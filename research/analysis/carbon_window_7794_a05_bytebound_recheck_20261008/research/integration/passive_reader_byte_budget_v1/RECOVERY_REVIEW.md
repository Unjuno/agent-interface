# Recovery review: Issues #3977 and #3999 whole-stream byte budget

The old 2026-09-22 branch carries 21 source, freeze, plan, environment, and
auditor files for two distinct allocations. It does not contain either
allocation's formal raw package, terminal manifest, batch receipts, or audit
outputs. A bounded search of accessible local workspace/temp/download paths
found no corresponding output bundle.

## Immutable predecessor STOP — Issue #3977

Issue [#3977](https://github.com/Unjuno/agent-interface/issues/3977),
comment [5766613274](https://github.com/Unjuno/agent-interface/issues/3977#issuecomment-5766613274),
records `STOP_FORMAL_EXECUTION_TIMEOUT`: five of 12 rows complete, case 05
partial, no terminal or original manifest, and the unchanged raw auditor
exited 1 because the manifest was missing. Scientific disposition is NONE.
Those partial observations cannot be resumed, pooled, or called a scientific
PASS/FAIL. The raw bytes remain unavailable here.

## Issue-reported successor — Issue #3999

Issue [#3999](https://github.com/Unjuno/agent-interface/issues/3999),
comment [5766770797](https://github.com/Unjuno/agent-interface/issues/3999#issuecomment-5766770797),
reports six once-only batches, 12/12 streams, 84/84 CLI calls, all writer,
batch, and launcher exits zero, and
`PASS_WHOLE_STREAM_BUDGET_BOUNDARY_SCOPED`, with 13/13 rehashed corruption
controls rejected. The Issue reports that all four 1,025-byte streams refused
the fixed 1,024-byte reads; saved-cursor continuation at 2,048 bytes returned
the remaining record; reset controls redelivered 24 prior identities; and all
changed-prefix controls refused.

The Issue lists hashes for ROWS, manifest, raw audit, and controls, but those
artifacts are not in the branch or bounded local search. Therefore the counts,
hashes, and audit disposition remain Issue-reported, not independently
verified from bytes in this repository. Keep v2 separate from—and do not use
it to overwrite—the immutable v1 STOP.

## Recovery boundary

All 21 original source/freeze files are preserved byte-for-byte. Static JSON
and Python syntax checks and an eight-case synthetic prefix-guard construction
test pass locally; no formal worker or batch was invoked. Raw-dependent formal
audit tests were not run because their required outputs are absent. No
allocation, retry, resume, replacement, or runtime change was performed.

The finite result does not establish automatic recovery, unbounded liveness,
production adoption, model/GUI utility, or a performance benefit. Issues
#3977 and #3999 remain open; any subsequently recovered corpus must be
independently audited from its original saved bytes.
