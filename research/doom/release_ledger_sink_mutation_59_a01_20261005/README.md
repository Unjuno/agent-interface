# Release ledger sink-mutation boundary — #59 A01

## H / T / D / C / U

**H.** At #7635 head `12522ccd0b58d3333da1d241d1b04f2c888c46e6`, a sink that mutates the event dictionary's `release_batch_position` and then raises can make the release-delivery ledger classify an attempted row as `not_attempted`. This crosses the publication callback boundary in both complete release-batch publication and incomplete-cleanup publication.

**T.** Freeze the backend at PR #7635 head `12522ccd0b58d3333da1d241d1b04f2c888c46e6` (backend Git blob `924c99a3838ba49ad0b4ec07aaa568b1a09a1713`, SHA-256 `39f93d00a529392454b63a0c568ebf01681b05c2691af695eb09a596ad44c809`; test blob `e0a1371247ed1b61ac177503102e64f5710569d3`). Add one mutating fail-before-accept sink case to the complete batch and one to incomplete cleanup. Run both against the exact parent, then run the focused backend composition suite on the candidate under Windows Python 3.11 and pinned WSLc Python 3.12.

**D.** The parent must fail both regressions because the attempted position is reported `not_attempted`; the candidate must classify it `unknown`, preserve the confirmed and not-attempted neighboring positions, and pass all backend composition tests on both environments.

**C.** A sink could be specified never to mutate its input object. The current callback contract does not make that guarantee, and passing a mutable dictionary across the boundary permits mutation. Capturing the position before callback invocation removes the dependency without changing the emitted row schema. This does not show that the production sink currently mutates rows.

**U.** Deterministic in-process construction only. It does not establish a defect in a live sink, physical key release, X-server behavior, application consumption, useful feedback, recovery efficacy, threat response, or MAP01 completion. No game, model, GUI, native input, or live allocation ran. The prior live allocation remains consumed and was not retried.

## Result

The exact parent fails both added regressions. Complete publication returns position 1 as `not_attempted`; incomplete cleanup returns the same incorrect classification. The repair captures the position before `emit(row)` and uses that frozen scalar when recording `unknown`, `confirmed`, or `confirmed_incomplete`.

- WSLc candidate backend suite: 12/12 passed.
- Windows Python 3.11 candidate backend suite: 12/12 passed.
- Changed-file `py_compile` and `git diff --check`: passed on Windows.
- WSLc image: `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (cached; `--pull never`); network disabled, one requested CPU, 512 MiB requested memory, UID/GID 1000, read-only source mount and separate writable output mount.
- WSLc reported that swap limit capabilities/cgroup are unavailable; memory-limit enforcement is not claimed.

The backend suite excludes `test_executor_terminal_retains_actual_backend_delivery_positions`, which imports an additional executor dependency omitted from this sparse worktree. The changed backend and both complete/incomplete publication paths are covered by the 11 executed tests. The earlier exploratory command that attempted the full module is retained in the session output but is not counted as a pass.

## Independent review follow-up — 2026-10-05

An independent exact-head review swept sink mutation across first/middle/last positions and fail-before-accept plus accept-then-raise outcomes. I retained that 12-case matrix in the two parameterized regressions. The full focused backend suite passes 12/12 on Windows Python 3.11; the two matrix tests pass on pinned WSLc Python 3.12. WSLc output is retained in `wslc-matrix/`. The initial WSLc invocation from the task-root path failed to locate the sparse checkout, and the corrected invocation from the repository worktree passed; only the corrected run is evidence.

## Reproduction

From the repository root on the candidate branch:

```powershell
python -m unittest research.doom.test_release_backend_v3_actual_composition.ActualReleaseCompositionTests.test_sink_mutation_cannot_erase_failed_position_from_delivery_ledger research.doom.test_release_backend_v3_actual_composition.ActualReleaseCompositionTests.test_incomplete_sink_mutation_cannot_erase_failed_position_from_delivery_ledger -v
```

Raw WSLc parent failures are in `wslc-baseline/`; candidate output and exit code are in `wslc-candidate/`. Windows candidate output and exit code are beside this README. Run `python audit.py` from this directory to independently check the retained outcomes, source mutation points, parent blob, and hashes.

Run the expanded WSLc matrix from `/research/doom` with `python -m unittest test_release_backend_v3_actual_composition.ActualReleaseCompositionTests.test_sink_mutation_cannot_erase_failed_position_from_delivery_ledger test_release_backend_v3_actual_composition.ActualReleaseCompositionTests.test_incomplete_sink_mutation_cannot_erase_failed_position_from_delivery_ledger -v`.
