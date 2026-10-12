# Visual-context-staleness A01 run record

- Local CPython 3.11.9 preflight: two invocations during test development; both passed 2/2. Final test source was unchanged for the second invocation.
- WSLc 3.0.1.0 final frozen run: completed `PASS_BOUNDARY_CHARACTERIZATION`; exactly one invocation; pinned Python 3.14.8 base; no network; one CPU; 512 MiB requested. `results/exit.txt` is `0`; the retained transcript reports both tests passed; image ID is retained in `results/image_id.txt`. The transcript warns that swap-limit cgroups are unavailable, so the requested memory limit is not treated as verified enforcement.
- Input pair: current-main retained V39 `cover-0` sequences 2→3. Both have health 97, ammo 48, identical focus/surface/geometry. Source/current decoded-RGB hashes differ (`0ac32b…745da` → `0e06f6…d71c8`); frame audit recomputes those digests from the two exact PNG files.
- Expected scoped behavior: the actual paired-signal monitor returns no invalidation, the synthetic planner answer remains eligible, and actual current action admission reaches executor-ready because this path does not bind the image hash. Same-hash control gives the same result.
- Both output branches assert `executor_admission=null` and `input_authority_admitted=false`.
- This replays historical observation bytes through exact current-main software functions; original V39's controller source was not pinned to current main. No model, game, OS input, executor, physical release, threat semantic interpretation, recovery, or task outcome.
- Post-run check: see `POSTHOC_VALIDATION.md`. It uses the retained PNGs and transcript only, runs no WSLc allocation, and does not change the frozen v1 test or its recorded result.
