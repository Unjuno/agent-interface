# Cancellation outcome repair: context v3

This is the ordinary source-context check for PR #6894 after main adopted the
cancellation-release lower bound (#6892). It preserves the original possible-effect
repair, plus every release constructor, backend protocol and cancellation guard
already in fixed base `a96283aceb2d4e72aabd592a9b94fd60397d5622`.

The source refresh is a history-preserving merge of original head
`fa276a1c5b85c45251f2ffd175e65fb18836d664` and that fixed base, using common base
`cb13a10dce358649458f5aea00947b8aa43fc5b8`. The only content conflict was kernel
README. Its resolution retains the full current release documentation, appends
the original uncertainty paragraph, and documents the already adopted all-kernel
discovery command. One new joint regression refuses a typed stale cancellation
without changing request/stage/start/receipt/reason, then accepts fresh typed
cleanup and preserves possible occurrence. No lifecycle guard is removed.

The before arm contains the fixed base's eight Python files except test_kernel,
which adds the same five PR regressions used by the candidate. The after arm is
the exact eight candidate Python files. Both test definitions are byte-identical.
SOURCE_REFRESH.json pins each file by Git blob, SHA256 and length.

Three actual ordinary child runs, Windows CPython 3.12.10, were frozen before
execution. Before: 40 methods, exactly two expected missing-True failures and no
errors. After: 40/40 normal and 40/40 with -O, no errors. RUN_PLAN and RUN_RECEIPTS
retain actual parameters and UTC/exits through disclosed private-metadata
projections. Receipt log hashes refer to original logs; PUBLICATION_TRANSFORMS
maps the single red traceback projection and projected records to their exact
original hashes. Green logs and all source snapshots are copied byte-exactly.
Execution duration is bookkeeping, not a latency or efficiency measurement.

The original 25 package files and original 24-entry manifest remain unchanged.
Their original six source pins, six inert histories and canonical 25-method
checks describe the old fa276a1c snapshot. They are historical evidence, not
assertions that the refreshed kernel still has only 25 methods. No old producer,
formal allocation or raw matrix was replayed for this refresh.

First setup failure: a full temporary index used git write-tree without
--missing-ok in a partial clone, causing an unwanted large promisor fetch.
Only the verified seven-process lineage of this author's preparation was
stopped. The stopped command exited nonzero before any test began; partial
index, fetch output and private process records were retained. Preparation was
repaired with a new author-owned index and write-tree --missing-ok. The original
README conflict output and repaired preflight output are retained here. This
setup failure is not relabeled as a test result or a successful formal run.

Scope: sequential inert kernel reporting. No physical release/task effect,
GUI/backend/model/GPU/container, concurrent or hostile-object defense, clock
authenticity or efficiency claim. This is author evidence, not a nonauthor
content vote, exact actual-base application certificate, or main adoption.
Pending #6901 receipt-start defense and #6875 nominal promotion remain separately
owned. Any intervening lifecycle change needs an explicit later dependency check.

`archived-runner.py` records the original workspace-relative run procedure; do
not run it from this publication layout. The sources and logs are evidence under
runtime/results, outside runtime/kernel test discovery and production imports.
Run `python -B verify_retained.py` to check retained bytes and log expectations;
it does not import kernel sources or repeat the tests.
