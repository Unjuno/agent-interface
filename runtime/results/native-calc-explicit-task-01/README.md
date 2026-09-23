# Calc keyboard transfer exposed a missing public task destination

The primary assistant used the existing keyboard-continuation path in Calc,
without a leading click or a helper model. This is a transfer to another actual
desktop application, with a retained task failure and a fresh corrected run.

Run-1, seed 991102, exposed only numeric `a=762`, `b=745` in its public goal.
The assistant wrongly assumed horizontal placement, typed 762 in selected A1,
pressed Tab, typed 745 in B1, saved, viewed the format dialog, clicked the Excel
format button, viewed the worksheet and explicitly finished. The independent
score failed: expected A1/A2, actual [762, null]. The saved workbook separately
confirms B1=745. Successful key delivery and visible values did not establish
task success. The assistant's assumption was wrong; the failure is not relabeled.

The native harness now includes the existing task's cell destinations in the
public goal: `task.kind=write_cells`, `task.cells={A1:a,A2:b}`, `save_format=xlsx`.
This is task specification supplied before action, not observed success or a
controller reading the saved-file oracle. The original controller convention and
independent evaluator already required A1 and A2; the evaluator is unchanged.

Run-2 is a new private allocation, seed 991103, with explicit A1=551, A2=768.
After viewing the actual A1 selection, the assistant chose keyboard input with
Return between values, saved, inspected the format dialog, confirmed Excel
format by a separately grounded click, inspected the result and finished.
Independent saved-file parsing confirms A1=551, A2=768 and B1 empty. It passes.
The frozen first run was not edited, resumed or replayed after failure.

Both runs contain one pointer-free keyboard program and one explicit modal
confirmation click. All four programs report verified neutral release. Focus
changes return needs_review and fresh window review, not automatic dialog input.
Both owners are terminal with retained cleanup. Sensor configuration, sensor
development and Docker were not used.

`audit.py` independently reads both workbooks, checks goal destinations, request/
reply digests, native programs, releases, exact image hashes and terminal cleanup.
The pre-change harness, corrected harness, bridge and actual client metadata are
retained. No matched speed/token or generalized model-accuracy claim is made:
the assistant also learned the task convention from its first failure.

```sh
PYTHONPATH=.:research/live_control python3 research/live_control/run_native_calc_self_use_v1.py \
  --app calc --max-stages 4 --text-gap-ms 2 --seed 991103 --out results-local/FRESH-DIRECTORY
python3 runtime/results/native-calc-explicit-task-01/audit.py
```
