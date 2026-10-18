# A01 — exact integer epochs at fresh fire admission

This focused fix validation targets Issue #59 and parent PR #7725 (typed epoch/binding alias fix). It is pinned to baseline head `4781ae734dc90539e8e0e99a072e97a9932223cc`, controller blob `d42df13b36ec56eaaf316a12675deab08736b003`, then candidate controller blob `304ec68c03eb5f10e9130d40f8af8d2bcf5c889f`.

## H/T/D/C/U

- **H:** `prepare_action_admission()` must reject health or ammo `sequence` / `capture_ns` values unless each field's exact type is `int`, before comparing or projecting metadata into the final snapshot. A coherent integer pair must retain existing admission behavior.
- **T:** Execute the exact production function AST and the regression method in offline WSLc. The old-source red run uses the preserved baseline test; the candidate green run uses the corrected final regression test. Contract, evaluator and receipt helpers are stubbed to isolate this metadata gate; equal binding comparison remains enabled.
- **D:** Old source failed for both floats because no `ValueError` was raised. Candidate source rejects the float sequence and capture aliases before evaluation, while the integer pair remains `VALID_CURRENT`. One focused unittest passes.
- **C:** `PASS_FLOAT_EPOCH_ADMISSION_REJECTION_AND_INTEGER_CONTROL` at this synthetic fresh-admission construction boundary.
- **U:** The full dual-signal module was not run. This does not establish live producer metadata, game behavior, physical release, task effect, recovery, or MAP01 progress.

## Procedure deviations and stops

The freeze originally named bool cases `True`/`False` against integer 4/40; those are not equality aliases and were removed before the green run. The retained red output shows two actual float misses plus two invalid bool expectations. A first invocation stopped on a test-source syntax error, and another stopped on an obsolete test-method name; neither reached candidate logic. Both outputs are preserved. The result explicitly records these deviations rather than counting them as experiment failures.

WSLc ran offline in `post-guard-game-59-4d74:20261004`, with a read-only mount, one requested CPU and 1 GiB. It warned that swap/cgroup memory enforcement is unavailable. No GPU was allocated.


Protocol deviation: the initial retained red log also exercised bool aliases, although the freeze only specifies float-equal aliases. The original log is preserved adjacent to this package as dmission-epoch-a01-red-output-preserved.txt; the package's red-output.txt is a fresh rerun restricted to the two frozen float cases and reports exactly those two expected failures. The integer pair remains the positive control.


Frozen-plan deviation: `FREEZE.json` specified `True`/`False` aliases against integer 4/40, but those values are not equal to 4/40 under Python. The exploratory float cases (`4.0` and `40.0`) were not preregistered. Therefore this is exploratory red/green evidence, not a preregistered replication. The original mixed red output remains preserved adjacent to the package as `admission-epoch-a01-red-output-preserved.txt`; the package's `red-output.txt` is an isolated rerun restricted to the two exploratory float cases.


## Current-main source revalidation (2026-10-05)

GitHub MCP returned controller blob `d42df13b36ec56eaaf316a12675deab08736b003` for `main`, matching the frozen baseline source. The exact extracted `prepare_action_admission()` was rerun with the float-only regression: sequence `4.0` and capture `40.0` each failed because `ValueError` was not raised. The candidate rerun passes the one focused unittest. Raw output is retained as `current-main-red.txt` and `green-current.txt`; `CURRENT_MAIN_REVALIDATION.json` records H/T/D/C/U, provenance and limitations. This is an exploratory float follow-up, not the bool matrix named in the earlier freeze.
