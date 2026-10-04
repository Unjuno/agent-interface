# Run report — SELECTION-AWARE-PARTIAL-IDENTIFICATION-5681-T0-20261005-01

## Disposition

`PASS_METHOD_SCOPED` for the frozen finite method only. The closed-form candidate agrees with separate exhaustive enumeration of every eligible unknown-label completion. This does not repair, repeat, or supersede the prior #5681 T1 `STOP_CANDIDATE_COMMAND_DIVERGENCE`.

## Execution and results

- Source freeze: `4791915140d86211274cdc0d41479e45689a4559`; base main: `86a2694c6251c2d7df2f69dbea490ec037903ff7`.
- One candidate and one separate auditor invocation; no formal retries or replacements.
- Both ran in WSLc 3.0.1.0, pinned cached Python image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, Linux/amd64 / CPython 3.12.15, network disabled, one CPU requested, and 128 MiB requested. WSLc warned that swap/cgroup memory enforcement is unavailable; effective memory limiting is unverified.
- Candidate exited 0 as container `e7380a3eec7b`; source was read-only and output separate. Auditor exited 0 as `82fc0f2796e6`; source and raw candidate were read-only, output separate. Both were inspected and removed.
- WSLc rejected tested `--cidfile` formats before entrypoint, so the actual formal calls omitted it and used unique container names to recover IDs. A PowerShell wrapper path-conversion mistake also happened before formal entrypoints; these setup errors and logs are retained and did not consume either invocation.
- Candidate raw [`CANDIDATE_RAW.json`](CANDIDATE_RAW.json), SHA-256 `eed997934645548ff6813cf5eefce938e9f9156c4c4e3828ac37ec5670702258`.
- Auditor raw [`AUDITOR_RAW.json`](AUDITOR_RAW.json): 30 completions, no errors, all 10 mutation controls rejected. Exit code 0.
- Construction: 12 Windows CPython 3.11.9 tests passed; py_compile and diff check passed before freeze. Separate from the formal run.

## Scope and limits

For a complete finite frame of binary labels, `N` rows with `k` known positives and `u` unknown labels have exact sharp bounds `[k/N,(k+u)/N]`. The auditor enumerated all 30 completions across complete-frame fixtures. The incomplete frame correctly emitted no interval; threshold endpoint equality remained HOLD; the outside-frame transition retained only a captured-frame interval and returned `HOLD_OUT_OF_FRAME_NOT_IDENTIFIABLE`.

This is arithmetic over eight synthetic fixtures. It establishes no confidence interval, GUI or population prevalence, duration or hidden-state bound, task effect, safety evidence, runtime adoption, action authority, or GPU claim, and makes no general novelty claim for partial identification.

See [`RUN.json`](RUN.json), [`FREEZE.json`](../../FREEZE.json), and [`README.md`](../../README.md) for exact setup, inputs, and reproduction commands. The prior T1 STOP is preserved separately.
