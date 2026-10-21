# PR #8643 current-head recovery overlay validation A05

## H / T / D / C / U

**H.** PR #8643's recovery changes should preserve bounded drain and invalidation behavior, including fail-closed observation timeouts, ACK-wait event consumption, and cancelling an invalidated initial cover before planning, under normal and optimized Python execution.

**T.** Freeze PR head `38569db07352a8d42e08fd6711ba32c77aca20a4` and dependency base `1f81daa690b567a9a049cc75fae8619b2660c343`. Extract only the eight candidate files listed in `FREEZE.json` into a temporary source overlay. Verify the checked-out dependency tree differs from the base only under the listed evidence output prefixes. Run `test_map01_v39_pending_observation_drain.py` and `test_map01_overlap_controller_v39.py` against unchanged dependencies from the base, normally and with `-O`. Record stdout/stderr and exit codes.

**D.** PASS if all eight overlay blobs match their frozen Git identities and all four runs exit zero: 17 drain tests and 9 controller tests in each Python mode.

**C.** The runner overlays changed controller/test/admission/guard files while importing other modules from the pinned base checkout. Tests use deterministic fixtures; this is a small source overlay rather than a full checkout.

**U.** No full controller session, App Server, model, game, GUI, OS input, physical release measurement, or live task effect is run. These tests cover local recovery contracts only; Issue #59's live threat and task-effect gates remain open.

## Result

PASS. Python 3.13 completed 17/17 pending-drain tests and 9/9 overlap-controller tests in both normal and optimized modes against candidate head `38569db`. This includes the current ACK invalidation and initial-cover cancellation path. The dependency checkout had no changes outside the listed experiment packages. The temporary overlay was removed after each run. Candidate hashes and raw output are retained in `FREEZE.json`, per-suite output files, and `RESULT.json`.

## Reproduction

From the repository root:

```powershell
py -3.13 -B research/doom/v39_pr8643_overlay_regression_a05_20261008/run_suite.py
py -3.13 -B research/doom/v39_pr8643_overlay_regression_a05_20261008/audit.py
```

The runner uses a small temporary overlay and does not materialize a full worktree.

## Output lineage and canonical A05 evidence

The canonical A05 decision is bound to candidate `38569db07352a8d42e08fd6711ba32c77aca20a4` and the eight overlay blobs in `FREEZE.json`. Use `RESULT.json`, `AUDIT.stdout.txt`, and the four suite-specific stderr files (one per suite and Python mode) to interpret the four runs: 17 pending-drain tests and 9 overlap-controller tests in normal and optimized mode.

The top-level `RUN.stdout.txt` is retained historical output from an earlier partial attempt. It explicitly records candidate `ce7f4a9f0eac5e38388372a2638c23734a19dee5`, seven overlay paths, and only the pending-drain suite. It is superseded for the final A05 decision and must not be combined with the later eight-file result. The generic top-level `normal.*` and `optimized.*` files are also retained legacy outputs; their exact candidate/run binding is not established, so they are not the canonical per-suite evidence.

`SHA256SUMS.txt` verifies the bytes of both canonical and retained historical files. A matching checksum establishes byte integrity, not that a historical output belongs to the canonical run. No historical bytes were removed or rewritten.
