# V39 pre-acceptance stale replan to Executor admission, A03

## H / T / D / C / U

**H.** After current-main `Executor.submit` rejects a stale pre-acceptance sequence, a bounded recovery can discard that answer, open a distinct planner turn from a matching newer typed/full observation, compile only that fresh turn's action with the exact current-main controller compiler, and reach the exact `Executor.submit` acceptance boundary once. If the backend advances again before submission, the exact executor must reject before acceptance or worker start.

**T.** Freeze current main `2a9052e` and the controller/compiler, `Executor.submit`, its exact program-hash function, and planner adapter blobs. Use the already-retained A02 result from PR #8501 as prior evidence that current producer `Backend.snapshot` can emit a matched typed/full sequence-2 pair; do not rerun its A02 outcome. Construct a matching local sequence-2 fixture, run a fake two-turn planner through the exact adapter, discard the first answer after an exact stale-sequence rejection, compile the second answer with the exact `compile_commands`, and invoke the exact `Executor.submit` AST method against an inert backend. The thread stub records `start()` without executing `_run` or input. Then repeat with backend sequence 3 while the new answer still references sequence 2.

**D.** Pass only if sequence-1 submission against backend sequence 2 emits no admission and performs no validation/start; the new planner turn includes sequence-2 HUD/image; the fresh compiled program is accepted exactly once when backend remains at 2; and the same sequence-2 program is rejected with no admission/start after backend advances to 3.

**C.** An accepted event proves only the method-level admission boundary. It does not prove worker execution, key release, or gameplay. A second sequence advance remains a safe refusal and requires a separately bounded recovery decision in production.

**U.** This is synthetic source-bound construction. It does not include a live app-server model, Doom process, GUI, OS input, game timing, threat, release, useful feedback, task effect, or MAP01 outcome. It neither implements production recovery nor closes Issue #59.

## Result

See `RESULT.json`. The candidate has no authorization to run physical input: the exact Executor method is executed with a no-op worker start stub.

## Reproduction

From repository root:

```powershell
python research/doom/v39_preacceptance_stale_replan_a03_20261008/run.py
python -m py_compile research/doom/v39_preacceptance_stale_replan_a03_20261008/run.py
python research/doom/v39_preacceptance_stale_replan_a03_20261008/verify.py
```
## Scope correction

The stale answer is compiled into the original seq-1 attempt before the Executor rejects it. A03 verifies that this rejected program is not retried after the rejection; it does not claim the planner answer was never compiled. The seq-2 fresh answer is compiled separately. The inert worker stub records the exact Executor's accepted boundary but invokes no input routine.

Package hashes can be regenerated and checked with:

```powershell
python research/doom/v39_preacceptance_stale_replan_a03_20261008/hash_package.py
python research/doom/v39_preacceptance_stale_replan_a03_20261008/verify.py
```
