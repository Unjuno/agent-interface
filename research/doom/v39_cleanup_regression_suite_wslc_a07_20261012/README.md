# A07: focused duplicate-cleanup regression suite

This is a distinct test of the actual `ControllerFailureCleanup` class API, separate from A06's AST-extracted finite exhaustive state-space check. It applies the PR #8687 focused test module to both the frozen current-main implementation and the frozen PR implementation, under CPython 3.12.3 in normal and optimized (`-O`) mode.

## Frozen inputs

- Main: `f185a9059d485a4f8d5a65e9e7f6782897f67eae`; source blob `50c63fa83969ed518a91e39c08d1ee52064eb636`.
- Candidate: `6195600931fa6de4ecf1a5012cb83b549addb5af`; source blob `576d481a3503e8be4d8ceded8a6371b3fe8850fc`.
- Candidate test module blob: `0bad8e47bb1a78798ad982fbd6be63c09d834742`.

## Result

The candidate passed all five tests in both modes. Current main failed three assertions across exactly the two duplicate-identity tests, in both modes. The separate audit verified Git blob identities, loaded source paths and source SHA-256 values, and reclassified each raw unittest transcript independently. It found three failing assertions in the main run (including both terminal orders) across two test methods; the candidate has no failing assertion.

`results/run.json` is the unmodified runner output. Its summary says `FAIL_SCOPED` because the first classifier retained trailing whitespace in test names and counted two subtest failures separately; the raw output itself records the expected current-main regressions and clean candidate runs. `results/audit.json` records the independently verified scoped outcome and this classifier correction. Earlier invalid harness outputs and infrastructure attempts are retained in `results/` and `results/attempts.jsonl`.

## Runtime deviation and limits

WSLc did not expose the D: bind-mounted `/runner` path and exited before the suite ran. We preserved that pre-test stop and used native Ubuntu WSL instead. Native cgroup values were `cpu.max=max 100000` and `memory.max=max`, so this run makes no CPU/memory confinement claim.

This tests cleanup receipt semantics only. It does not exercise the controller's integrated event producer, physical key release, GUI/game, model, useful feedback, bounded recovery, or live threat response. It does not rerun A05's formal allocation or auditor and does not establish end-to-end computer-control success.

