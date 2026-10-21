# V39 current-main versus latest PR #8643 regression control A07

## H / T / D / C / U

**H.** The latest PR #8643 controller regression tests should distinguish its recovery changes from current main: current main should permit stale remaining-cover reuse and lack the new invalidation receipts/cancel path, while the candidate should pass.

**T.** Freeze current main `5cfe661826c5742eb26da2ba9a9304ae0cb480d4`, candidate PR #8643 head `e5579183f8a083ad51d331a19b1ec8a8e37bf714`, and dependency base `1f81daa690b567a9a049cc75fae8619b2660c343`. For each arm, extract the exact controller and its static import closure from that arm's commit, plus the same candidate 10-test controller file from the candidate commit. Run normal and optimized Python in separate temporary overlays.

**D.** PASS for this differential if current main runs ten tests with exactly one assertion failure and two errors, including all three predeclared regression cases, in both modes; the candidate must run 10/10 successfully in both modes.

**C.** Deterministic test fixtures isolate controller contracts. This checks that the new regression cases distinguish current main from the latest candidate; it measures neither runtime frequency nor user-visible effect.

**U.** No Doom process, model, GUI, OS input, live threat exposure, physical key release, or task-effect endpoint was used. This evidence does not authorize merging PR #8643 and does not satisfy Issue #59's live gate.

## Result

**DISCRIMINATING_BASELINE.** Current main failed three expected cases: it reused a stale cover after partial-action discard, lacks the pre-planner cancellation helper, and lacks the receipt distinction for preacceptance versus cancellation. Seven other cases passed. The same ten tests passed 10/10 against candidate head `e557918` in normal and optimized Python.

## Reproduction

```powershell
py -3.13 -B research/doom/v39_main_vs_pr8643_regression_control_a07_20261009/run_comparison.py
py -3.13 -B research/doom/v39_main_vs_pr8643_regression_control_a07_20261009/audit.py
```
