# Current-main late-usage test recheck at `8207849`

## Scope

This is a deterministic local regression check of the App Server late-usage spool/provider/client path present in main. It makes no provider/model call, GUI action, input, formal allocation, Docker action, or runtime code change. The candidate patch changes only the timing and cleanup discipline of one threaded fake-host unit test.

## R01: initial current-main run, retained as FAIL

At main `8207849ad0bd30b6b31ef4a9cee7eb95f5b4619a`, the four focused modules ran 26 tests normally and under `-O`. Normal mode failed twice in `test_file_planner_joins_start_and_terminal_receipts`: `begin_turn` timed out waiting for the started receipt; teardown then hit a Windows `PermissionError` on the atomic temporary JSON file. Optimized mode passed 26/26.

Post-run inspection found the started receipt in R01's `TemporaryDirectory`, although the consumer had already timed out. The exact receipt and marker are retained. Its file timestamp proves only when the file metadata was observed, not when publication occurred. This does not prove host load caused the failure. The test gave its fake host and the planner equal one-second deadlines, and did not join the worker in a `finally` path; those are concrete scheduling and cleanup hazards.

## R02: after test-only repair, diagnostic pass with invalid freeze

A follow-up run passed 26/26 normally and 26/26 under `-O`, but its condition-generation script used a doubled relative directory and produced an empty source-hash map. Preserve the raw run, but exclude it from the adjudicated PASS set.

## R03: correctly frozen candidate run

R03 froze the exact source hashes and base revision before execution. After a narrow fixture-only repair, both commands passed: 26/26 normal and 26/26 optimized. The repair gives the fake host more scheduling slack than the planner wait and guarantees the publisher thread is signaled and joined before temporary-directory cleanup. Product/runtime behavior and assertions remain unchanged.

The earlier full 107-test current-main discovery still has two separate Calc/Fake X failures recorded in the parent packet; this focused pass does not resolve them. It also does not establish real provider billing/delivery, a live task effect, recovery reliability, or an integrated efficiency result. Keep PR #10218 draft: its head remains based on `78cef41` and is 246 commits behind current main with four ahead; this test result is not merge readiness.

## Per-attempt evidence

- `r01-initial-failure/`: original conditions, normal/-O logs and codes, and the residual late started receipt. No cleanup/deletion of the source temp directory was performed.
- `r02-pass-invalid-freeze/`: unchanged invalid conditions and diagnostic logs; excluded because source hashes were absent.
- `r03-pass-frozen/`: corrected conditions, exact tested file hashes, and both successful raw logs/codes.
- Each directory contains a `SHA256SUMS` manifest covering its conditions and raw evidence.

## Later PR disposition

The audit at frozen main `897f4896d23dd127a4523dc4955e573dace7d674` found PR #10218's implementation/evidence already represented in main (37/41 changed-path blobs identical; the remaining differences were superseding main content). PR #10218 was closed unmerged on 2026-11-20 without deleting its branch. See the [path-by-path audit](../pr10218_supersession_audit_20261121/RESULT.md). Issue #57 remains open for live provider accounting, caller task success, recovery reliability, and matched efficiency.
