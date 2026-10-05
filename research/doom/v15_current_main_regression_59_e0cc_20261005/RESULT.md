# Current-main integration regression repair

The exact virtual integration of #8094 source head `59e307adde701dc3e061ee3ff124c5982c20fcc9` with main `95316efef54b092fc2f0264539223830cdb9ba21` merges cleanly at tree `6b7f94c8270021457b321b40fe3c757f39b50dec`. All 81 selected source/resource/test paths are byte-identical to the PR head, and none of those main-side paths changed since the previous main pin `b673c9f1ca9717cbaeec44aa9feb262a28b9097f`.

This resolves the attribution question in #8094 comment 5993632573: the four main-versus-PR source differences are intended branch changes, not intervening main edits. A main-versus-PR comparison alone does not show that previously frozen branch evidence became inapplicable. This byte check is restricted to the stated closure and does not review the complete PR or establish full runtime integration.

Fresh focused tests nevertheless found two stale AST test fixtures: V15's extracted `main` lacked the production `HERE`/`RESEARCH` bindings, and the initial-cover test extraction omitted the real `wait_for_invalidation_frame` dependency. They failed with NameError; their original outputs are preserved. This patch changes only those two tests. The V15 fixture now asserts the measured bridge and current owner paths. The wait fixture uses the actual barrier/helper, binds its initial-cover frames fully, and rejects wrong pointer binding, stale capture and mismatched RGB hash before accepting the matching frame. No production behavior was changed.

After the two-file patch, the exact candidate tree is `1b70144f44470d6e07b51111b793683781aca33b`. Seventeen selected modules, **153 tests**, pass in fresh Python processes. The two repaired modules also pass normally and under `-O` (3 session + 16 wait methods per mode). These counts are test methods, not independent experimental trials. No native/game/model/formal run was performed or replayed.

## Setup failures remain distinct

The initial 81-file export was enough for the prior native component probe but not for every selected regression entrypoint. Four startup-route failures came from missing historical bridge/owner files. The broader typed-feedback test lacked three retained JSONL fixtures, the wheel test lacked a shared fixture module, and the signal-guard package import needed the repository root on PYTHONPATH. Six exact Git files were added to the isolated export and the package path was corrected; production repository files were not changed to resolve these errors. Original exports, failures and their source tree are retained in the records. The final export has 87 files, including these test-only dependencies and raw fixtures.

## Evidence and source applicability

- `tree-comparison.json`: exact refs/tree and all 81 blob comparisons, plus the intervening main path list.
- `candidate-final-freeze.json`: the final tree, two test-only changes and all 87 exported SHA256 hashes, fixed before the 17-module run.
- `initial-execution.json`: first focused and adjacent outputs, exit codes, commands and full stdout/stderr, including failure traces.
- `repair-execution.json`: export fixes and focused normal/optimized test results.
- `final-execution.json`: all 17 fresh-process commands and outputs for the final tree.
- `tests.patch`, before/after `.txt` files: exact test repair, stored inertly.
- `peer-review.md` / `peer-repair.md`: coauthor source attribution and repair reports; no quorum vote.

All 64 non-test files in the earlier 81-file selection remain unchanged. Fifteen of its 17 test definitions remain unchanged; the other two are repaired here. In particular, all 32 modules loaded by the prior native X11 run remain unchanged, so this test-only patch does not regrade or rerun that native result. Prior immutable evidence packages are untouched. The selected suite does not cover the full 1,387-path pre-repair PR, all historical nested scripts, or all repository tests.

No main update or merge was performed. The full-scope nonauthor review, committee requirements, exact integration approval and serialized/CAS application remain outstanding. The live threat-exposure gate is separate and unassigned. This is an author virtual-tree check and regression repair, not an end-to-end native or gameplay qualification.
