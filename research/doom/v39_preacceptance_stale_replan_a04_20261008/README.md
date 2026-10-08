# V39 stale replan through exact producer and Executor admission, A04

## H / T / D / C / U

**H.** When a sequence-1 answer is refused before acceptance because the backend has advanced to sequence 2, the exact producer's typed sequence-2 row and later full image can pass through the controller wait and a distinct fresh planner turn; that turn's compiled action can reach exact `Executor.submit` once. If sequence advances to 3 before that submit, it must be refused before backend validation, acceptance publication, or worker start.

**T.** At current main `2a9052efdd155b8cdc173d216a969ea5f64a1ce9`, AST-execute the exact `Backend.snapshot`, controller nested `wait`, `begin_model_turn`, `compile_commands`, and `Executor.submit`; load the exact typed observation module and `PersistentPlannerAdapter`. Keep image capture/transport, HUD values, planner, backend, lease, and thread inert. Queue the executor's stale rejection before the producer's typed/full events, then test exact sequence-2 admission and sequence-3 drift.

**D.** Pass only if the exact producer emits typed then full sequence 2 with matching capture, binding and RGB hash; the controller wait advances only on the full image while preserving the typed signals; the old sequence-1 compiled answer is refused with zero validation/admission/start; a distinct sequence-2 planner answer uses fresh HUD/image and is admitted once; and the same answer is refused if the backend advances to sequence 3. Negative recovery controls must refuse.

**C.** One synthetic source-bound schedule establishes method composition and order only. The worker start stub does not execute the worker body.

**U.** No model service, Doom, GUI, OS input, live timing, release, threat response, useful task feedback, recovery after worker execution, or task effect was tested. This does not establish production recovery or close Issue #59.

## Result

`RESULT.json` reports the exact event and admission boundaries, negative controls, and synthetic scope. Normal and optimized Python outputs must match byte-for-byte. `verify.py` independently checks source pins, output parity, event invariants, and package hashes.

## Reproduction

From repository root:

```powershell
$resultsDir = Join-Path $env:TEMP ("v39-a04-" + [guid]::NewGuid().ToString("N"))
python -B research/doom/v39_preacceptance_stale_replan_a04_20261008/run_modes.py --output-dir $resultsDir
python -B research/doom/v39_preacceptance_stale_replan_a04_20261008/verify.py --results-dir $resultsDir
```


The runner requires a fresh output directory outside this package and refuses an existing directory before starting the candidate. The verification command checks the replay output against the committed first-run bytes while separately verifying the retained package hashes. Run `python -B -m unittest research/doom/v39_preacceptance_stale_replan_a04_20261008/test_run_modes.py` for the output-safety regressions; these tests do not invoke the candidate.
