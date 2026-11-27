# A09 — V39 authored paired HUD guard boundary

This experiment advances the #59 threat-control question at a construction boundary: will the current-main health/ammo cover monitor invalidate an authored policy when paired HUD evidence crosses the monitor's hard floor?

The controller and `ObservableSignalGuard` source files are frozen from main `f185a9059d485a4f8d5a65e9e7f6782897f67eae`; their Git blob IDs and SHA-256 hashes are in `FREEZE.json`. The test AST-extracts exact production monitor functions and uses the exact production one-way guard class. The only test invocation ran inside WSLc; its raw console transcript, exit code, environment observation, and a transcript-only audit are retained here.

## Result

All four conditions passed: health 70→64 crossed floor 65 and invalidated; ammo 6→0 crossed its positive floor 1 and invalidated; an in-envelope same-epoch pair returned no invalidation and recorded two soft changes; a mixed-epoch pair failed closed. Invalidation receipts require a new decision and grant no input authority. `results/audit.json` independently validates the frozen input IDs and retained test transcript without rerunning the suite.

The ammo boundary here is the monitor's built-in positive floor of one; it does not test whether a higher planner-authored ammunition requirement is carried into pending cover. This check does not exercise controller wait/cancel ordering, a real model or game, a live release, useful feedback, recovery, task effect, or terminal success. It is synthetic source-composition evidence, not end-to-end computer-control success.

See `HYPOTHESIS.md` for H/T/D/C/U, `RUNS.md` for execution, and `DEVIATION.md` for resource and scope caveats.

`SHA256SUMS` inventories all retained package inputs, code, reports, and transcripts except itself and generated Python `__pycache__` files.
